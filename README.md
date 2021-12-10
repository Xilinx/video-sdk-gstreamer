# Video SDK GStreamer

This folder contains scripts to clone and build open source Gstreamer plug-ins. This folder also contains sources and build scripts for gstreamer plug-ins developed by Xilinx. 

First step is to build and install the open source GStreame plug-ins. Second step is to build and install GStreamer plug-ins developed by Xilinx.

## Building open source GStreamer plug-ins
A single script, ***install_gst.sh***, is provided to clone, apply xilinx patches, compile and install open source GStreamer packages.

## Building Xilinx developed GStreamer plug-ins
A single script, ***build_install_vvas.sh***, is provided to build and install gstreamer plug-ins developed by Xilinx.

## Retrieving open source GStreamer sources
The script ***install_gst.sh*** mentioned above does cloning, compilation  and installation of plug-ins from GStreamer sources and then deleting the sources. If someone wants to browse through the open source GStreamer sources patched with the Xilinx patches that are used in this project, they can use the script ***retrieve_gst_sources.sh***. This script will clone open source GStreamer sources from the github repository and apply Xilinx specific patches on top of it. The patched sources will be available in the /tmp folder and the sources will be present as 
 - gst-libav-1.16.2
 - gst-plugins-bad-1.16.2
 - gst-plugins-base-1.16.2
 - gst-plugins-good-1.16.2
 - gstreamer-1.16.2
