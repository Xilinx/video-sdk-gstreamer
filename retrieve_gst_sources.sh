#! /bin/bash

#####################################
###### Fetching GStreamer Sources  #######
#####################################

BASEDIR=$PWD

cp ./patches/* /tmp/

# GStreamer core package installation
cp ./patches/0001-build-Adapt-to-backwards-incompatible-change-in-GNU-.patch /tmp
cd /tmp/ && wget https://gstreamer.freedesktop.org/src/gstreamer/gstreamer-1.16.2.tar.xz --no-check-certificate && \
    tar -xvf gstreamer-1.16.2.tar.xz && cd gstreamer-1.16.2 && \
    cd common && patch -p1 < /tmp/0001-build-Adapt-to-backwards-incompatible-change-in-GNU-.patch && cd .. && \

cd $BASEDIR

# GStreamer base package installation with patch
cp ./patches/0001-Add-Xilinx-s-format-support.patch /tmp
cp ./patches/0001-gst-plugins-base-Add-HDR10-support.patch /tmp

cd /tmp/ && wget https://gstreamer.freedesktop.org/src/gst-plugins-base/gst-plugins-base-1.16.2.tar.xz --no-check-certificate && \
    tar -xvf gst-plugins-base-1.16.2.tar.xz && cd gst-plugins-base-1.16.2 && \
    cd common && patch -p1 < /tmp/0001-build-Adapt-to-backwards-incompatible-change-in-GNU-.patch && cd .. && \
    patch -p1 < /tmp/0001-Add-Xilinx-s-format-support.patch && \
    patch -p1 < /tmp/0001-gst-plugins-base-Add-HDR10-support.patch

cd $BASEDIR

# GStreamer good package installation
cp ./patches/0001-Use-helper-function-to-map-colorimetry-parameters.patch /tmp

cd /tmp/ && wget https://gstreamer.freedesktop.org/src/gst-plugins-good/gst-plugins-good-1.16.2.tar.xz --no-check-certificate && \
    tar -xvf gst-plugins-good-1.16.2.tar.xz && cd gst-plugins-good-1.16.2
    cd common && patch -p1 < /tmp/0001-build-Adapt-to-backwards-incompatible-change-in-GNU-.patch && cd .. && \
    patch -p1 < /tmp/0001-Use-helper-function-to-map-colorimetry-parameters.patch
cd $BASEDIR

# GStreamer bad package installation
cp ./patches/0001-Update-Colorimetry-and-SEI-parsing-for-HDR10.patch /tmp
cp ./patches/0001-Derive-src-fps-from-vui_time_scale-vui_num_units_in_.patch /tmp
cd /tmp/ && wget https://gstreamer.freedesktop.org/src/gst-plugins-bad/gst-plugins-bad-1.16.2.tar.xz --no-check-certificate && \
    tar -xvf gst-plugins-bad-1.16.2.tar.xz && cd gst-plugins-bad-1.16.2 && \
    cd common && patch -p1 < /tmp/0001-build-Adapt-to-backwards-incompatible-change-in-GNU-.patch && cd .. && \
    patch -p1 < /tmp/0001-Update-Colorimetry-and-SEI-parsing-for-HDR10.patch
    patch -p1 < /tmp/0001-Derive-src-fps-from-vui_time_scale-vui_num_units_in_.patch && \

cd $BASEDIR

# GStreamer libav package installation
cd /tmp/ && wget https://gstreamer.freedesktop.org/src/gst-libav/gst-libav-1.16.2.tar.xz --no-check-certificate && \
    tar -xvf gst-libav-1.16.2.tar.xz && cd gst-libav-1.16.2

rm -rf /tmp/*.tar.xz
cd $BASEDIR

#echo "#######################################################################"
#echo "########  GStreamer Sources downloaded and patch applied       ########"
#echo "#######################################################################"

