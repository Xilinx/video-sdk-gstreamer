# Video SDK GStreamer

This repository contains the sources and scripts required to compile and rebuild the open source GStreamer packages and the Xilinx accelerator GStreamer plugins.

To rebuild the contents of this repository, follow the steps below.

1. Download, compile, build and install the GStreamer packages with required patches applied::
  
   ./install_gst.sh

   To learn more about the OS-specific details of the installation procedure, you can examine the contents of this script

1. Clean the Xilinx GStreamer plugin libraries::
  
   ./clean_vvas.sh

1. Build and install the Xilinx GStreamer plugin libraries::
  
    ./build_install_vvas.sh PCIe 1
