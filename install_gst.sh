#! /bin/bash

#####################################
###### Setup VVAS Environment #######
#####################################
sudo rm -rf /opt/xilinx/vvas
sudo mkdir -p /opt/xilinx/vvas/lib/pkgconfig
sudo mkdir -p /opt/xilinx/vvas/bin
sudo cp -rf setup.sh /opt/xilinx/vvas/

if [[ $PATH == /opt/xilinx/vvas/bin* ]] && \
   [[ $LD_LIBRARY_PATH == /opt/xilinx/vvas/lib* ]] && \
   [[ $PKG_CONFIG_PATH == /opt/xilinx/vvas/lib/pkgconfig* ]] && \
   [[ $GST_PLUGIN_PATH == /opt/xilinx/vvas/lib/gstreamer-1.0* ]]
then
	echo "Already has VVAS environment variables set correctly"
else
	echo "Does not have VVAS environment paths. Setting using /opt/xilinx/vvas/setup.sh"
	source /opt/xilinx/vvas/setup.sh
fi


BASEDIR=$PWD

cpu_count=`cat /proc/cpuinfo | grep processor | wc -l`

echo CPU = $cpu_count

retval=$?
if [ $retval -ne 0 ]; then
	echo "Unable to uninstall package(s) ($retval)"
	return 1
fi

os_distr=`lsb_release -a | grep "Distributor ID:"`
os_version=`lsb_release -a | grep "Release:"`

echo $os_distr
echo $os_version

if [[ $os_distr == *Ubuntu* ]]; then
	OS_TYPE="UBUNTU"
        if [[ $os_version =~ .*18.04.* ]]; then
		OS_VERSION="18_04"
        elif [[ $os_version =~ .*20.04.* ]]; then
		OS_VERSION="20_04"
        else
                echo "Unsupported OS version"
                return 1
        fi
elif [[ $os_distr == *RedHatEnterpriseServer* ]]; then
	OS_TYPE="RHEL"
        if [[ $os_version == *7.8* ]]; then
		OS_VERSION="7_8"
                echo "OS version : $os_version"
        else
                echo "Unsupported OS version"
                return 1
        fi
elif [[ $os_distr == *Amazon* ]]; then
	OS_TYPE="AMAZON"
        if [[ $os_version == *2* ]]; then
		OS_VERSION="2"
                echo "OS version : $os_version"
        else
                echo "Unsupported OS version"
                return 1
        fi
elif [[ $os_distr == *CentOS* ]]; then
	OS_TYPE="CENTOS"
        if [[ $os_version == *7* ]]; then
		OS_VERSION="7"
                echo "OS version : $os_version"
        else
                echo "Unsupported OS version"
                return 1
        fi
else
        echo "Unsupported OS type"
        return 1
fi

if [[ $OS_TYPE == "UBUNTU" ]]; then
	sudo apt-get update
	sudo apt-get install -y build-essential git autoconf autopoint libtool bison flex yasm \
		 libssl-dev libjansson-dev python3 python3-pip python3-setuptools python3-wheel \
		 ninja-build cmake libxext-dev libpango1.0-dev libgdk-pixbuf2.0-dev
	if [[ $os_version =~ .*18.04.* ]]; then
                OS_VERSION="18_04"
                sudo apt-get install -y libpangocairo-1.0-0
        elif [[ $os_version =~ .*20.04.* ]]; then
                OS_VERSION="20_04"
                sudo apt-get install -y libpangocairo-1.0-0 librust-pangocairo-dev
        else
                echo "Unsupported OS version"
                return 1
        fi

	retval=$?
	if [ $retval -ne 0 ]; then
		echo "Unable to install package(s) ($retval)"
		return 1
	fi
elif [[ $OS_TYPE == "RHEL" ]]; then
	sudo yum install -y http://repo.okay.com.mx/centos/7/x86_64/release/okay-release-1-1.noarch.rpm
	sudo yum install -y automake glib glib2-devel openssl-devel openssl-devel xorg-x11-server-devel \
		libssl-dev openssl openssl-devel yasm-devel  python3 python3-pip python3-setuptools python3-wheel jansson-devel ninja-build \
		pango pango-devel cairo-devel gdk-pixbuf2-devel
elif [[ $OS_TYPE == "AMAZON" ]]; then
	sudo yum install -y http://repo.okay.com.mx/centos/7/x86_64/release/okay-release-1-1.noarch.rpm
	sudo yum-config-manager --save --setopt=okay.skip_if_unavailable=true
	
	cd /tmp/ && wget http://ftp.gnu.org/gnu/automake/automake-1.14.tar.gz --no-check-certificate && \
	tar xvzf automake-1.14.tar.gz && cd automake-1.14 && \
	./configure
	make && sudo make install
	cd $BASEDIR
	rm -rf /tmp/automake*
	
	sudo yum install -y automake glib glib2-devel openssl-devel openssl-devel xorg-x11-server-devel \
		libssl-dev openssl openssl-devel yasm-devel  python3 python3-pip python3-setuptools python3-wheel jansson-devel ninja-build \
		pango pango-devel cairo-devel gdk-pixbuf2-devel gettext-devel flex bison
elif [[ $OS_TYPE == "CENTOS" ]]; then
	sudo yum install -y http://repo.okay.com.mx/centos/7/x86_64/release/okay-release-1-1.noarch.rpm
	sudo yum-config-manager --save --setopt=okay.skip_if_unavailable=true
	
	cd /tmp/ && wget http://ftp.gnu.org/gnu/automake/automake-1.14.tar.gz --no-check-certificate && \
	tar xvzf automake-1.14.tar.gz && cd automake-1.14 && \
	./configure
	make && sudo make install
	cd $BASEDIR
	rm -rf /tmp/automake*
	
	sudo yum install -y automake glib glib2-devel openssl-devel openssl-devel xorg-x11-server-devel \
		libssl-dev openssl openssl-devel yasm-devel  python3 python3-pip python3-setuptools python3-wheel jansson-devel ninja-build \
		pango pango-devel cairo-devel gdk-pixbuf2-devel gettext-devel flex bison
else
	echo "Unsupported OS type $OS_TYPE"
	return 1
fi

cp ./patches/* /tmp/
retval=$?
if [ $retval -ne 0 ]; then
	echo "Unable to copy patches"
        return 1
fi

# GStreamer core package installation
cd /tmp/ && wget https://gstreamer.freedesktop.org/src/gstreamer/gstreamer-1.16.2.tar.xz --no-check-certificate && \
    tar -xvf gstreamer-1.16.2.tar.xz && cd gstreamer-1.16.2 && \
    ./autogen.sh --prefix=/opt/xilinx/vvas --disable-gtk-doc
    make -j$cpu_count && sudo make install
retval=$?
if [ $retval -ne 0 ]; then
	echo "Unable to install gstreamer core package ($retval)"
	cd $BASEDIR
	return 1
fi

cd $BASEDIR
rm -rf /tmp/gstreamer-1.16.2*

# GStreamer base package installation with patch
cp ./patches/0001-Add-Xilinx-s-format-support.patch /tmp
cp ./patches/0001-gst-plugins-base-Add-HDR10-support.patch /tmp

cd /tmp/ && wget https://gstreamer.freedesktop.org/src/gst-plugins-base/gst-plugins-base-1.16.2.tar.xz --no-check-certificate && \
    tar -xvf gst-plugins-base-1.16.2.tar.xz && cd gst-plugins-base-1.16.2 && \
    patch -p1 < /tmp/0001-Add-Xilinx-s-format-support.patch && \
    patch -p1 < /tmp/0001-gst-plugins-base-Add-HDR10-support.patch
retval=$?
if [ $retval -ne 0 ]; then
	echo "Unable to apply patch"
	cd $BASEDIR
	return 1
fi
    ./autogen.sh --prefix=/opt/xilinx/vvas --disable-gtk-doc && \
    make -j$cpu_count && sudo make install && \
retval=$?
if [ $retval -ne 0 ]; then
	echo "Unable to install base gstreamer plugins ($retval)"
	cd $BASEDIR
	return 1
fi
cd $BASEDIR
rm -rf /tmp/gst-plugins-base-1.16.2*

# GStreamer good package installation
cd /tmp/ && wget https://gstreamer.freedesktop.org/src/gst-plugins-good/gst-plugins-good-1.16.2.tar.xz --no-check-certificate && \
    tar -xvf gst-plugins-good-1.16.2.tar.xz && cd gst-plugins-good-1.16.2 && \
    ./autogen.sh --prefix=/opt/xilinx/vvas --disable-gtk-doc && \
    make -j$cpu_count && sudo make install
retval=$?
if [ $retval -ne 0 ]; then
	echo "Unable to install good gstreamer plugins ($retval)"
        cd $BASEDIR
	return 1
fi
cd $BASEDIR
rm -rf /tmp/gst-plugins-good-1.16.2*

# GStreamer bad package installation
cp ./patches/0001-Update-Colorimetry-and-SEI-parsing-for-HDR10.patch /tmp
cd /tmp/ && wget https://gstreamer.freedesktop.org/src/gst-plugins-bad/gst-plugins-bad-1.16.2.tar.xz --no-check-certificate && \
    tar -xvf gst-plugins-bad-1.16.2.tar.xz && cd gst-plugins-bad-1.16.2 && \
    patch -p1 < /tmp/0001-Update-Colorimetry-and-SEI-parsing-for-HDR10.patch && \
    ./autogen.sh --prefix=/opt/xilinx/vvas --disable-gtk-doc --disable-openexr  && make -j$cpu_count && sudo make install
retval=$?
if [ $retval -ne 0 ]; then
	echo "Unable to install bad gstreamer plugins ($retval)"
        cd $BASEDIR
	return 1
fi
cd $BASEDIR
rm -rf /tmp/gst-plugins-bad-1.16.2*

# GStreamer libav package installation
cd /tmp/ && wget https://gstreamer.freedesktop.org/src/gst-libav/gst-libav-1.16.2.tar.xz --no-check-certificate && \
    tar -xvf gst-libav-1.16.2.tar.xz && cd gst-libav-1.16.2 && \
    ./autogen.sh --prefix=/opt/xilinx/vvas --disable-gtk-doc  && make -j$cpu_count && sudo make install
retval=$?
if [ $retval -ne 0 ]; then
	echo "Unable to install gstreamer libav ($retval)"
        cd $BASEDIR
	return 1
fi
cd $BASEDIR
rm -rf /tmp/gst-libav-1.16.2*

######## Install Meson ###########
if [[ $OS_TYPE == "UBUNTU" ]]; then
	#pip3 install meson
	#export PATH=~/.local/bin:$PATH
	#elif [[ $OS_TYPE == "RHEL" ]]; then
	sudo pip3 install meson
elif [[ $OS_TYPE == "RHEL" ]]; then
	sudo pip3 install meson
elif [[ $OS_TYPE == "CENTOS" ]]; then
	#pip3 install meson --user
	#pip3 install ninja --user
	#export PATH=~/.local/bin:$PATH
	sudo pip3 install meson
	sudo pip3 install ninja
	export PATH=/usr/local/bin:$PATH
elif [[ $OS_TYPE == "AMAZON" ]]; then
	#pip3 install meson --user
	#pip3 install ninja --user
	#export PATH=~/.local/bin:$PATH
	sudo pip3 install meson
	sudo pip3 install ninja
	export PATH=/usr/local/bin:$PATH
fi

cd $BASEDIR

#Remove GStreamer plugin cache
rm -rf ~/.cache/gstreamer-1.0/

echo "#######################################################################"
echo "########         GStreamer setup completed successful          ########"
echo "#######################################################################"
