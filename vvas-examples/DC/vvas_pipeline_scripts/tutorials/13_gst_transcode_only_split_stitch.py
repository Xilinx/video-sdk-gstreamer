#
# Copyright 2020-2021 Xilinx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); 
# you may not use this file except in compliance with the License. 
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software 
# distributed under the License is distributed on an "AS IS" BASIS, 
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
# See the License for the specific language governing permissions and 
# limitations under the License.
#

# This script accepts an 8-bit, YUV420, pre-encoded file and will send the encoded output to a user-defined output path.
# This will split the clip on a boundary that ensures no visual quality is lost (a closed GOP boundary), and will distribute
# the clip across all available Alveo U30 cards, and stitches the outputs to generate the final encoded file
# Usage: python 13_gst_transcode_only_split_stitch.py [options]
# python 2.7.x is the required version
# e.g. python 13_gst_transcode_only_split_stitch.py  -s ~/videos/bbb_sunflower_1080p_60fps_normal.mp4 -d ./output.mp4 -i h264 -o h264 -b 5

# Options: 
#   -s INPUT_FILE,    --sourcefile=INPUT_FILE
#                     input file to convert
#   -d OUTPUT_FILE,   --destinationfile=OUTPUT_FILE 
#                     output file path
#   -i INPUT_FORMAT,  --icodec=INPUT_FORMAT 
#                     input file algorithm standard <h264, hevc, h265>
#                     default: h264
#   -o OUTPUT_FORMAT, --ocodec=OUTPUT_FORMAT
#                     output file algorithm standard <h264, hevc, h265>
#                     default: hevc
#   -b BITRATE,       --bitrate=BITRATE
#                     output bitrate in Mbit/s. Must be a float or integer value between 1.0 and 25.0
#                     default: 5.0
#                     (example: use -b 3 to specify an output bitrate of 3Mbits/sec)
ASPECT_RATIO = (16/9)

import subprocess
from optparse import OptionParser
import time
from datetime import datetime
import json
import re
from fractions import Fraction

def count_substrings(string, substring):
    string_size = len(string)
    substring_size = len(substring)
    count = 0
    for i in range(0,string_size-substring_size+1):
        if string[i:i+substring_size] == substring:
            count+=1
    return count

def main():
    (filename, ofilename, input_encoder, output_encoder, bitrate) = parse_options()

    #number of supported devices
    num_dev = subprocess.Popen("xbutil  list | grep xilinx_u30 | wc -l", shell = True, stdout = subprocess.PIPE).stdout.read()
    num_dev2 = int(num_dev.strip())
    print ("Number of U30 devices detected on this host are:", num_dev2)
    
    #check input video stream codec type and it should match with input variable
    extra_chunks = 0
    output = subprocess.Popen("gst-discoverer-1.0 "+filename+" | grep video | grep codec 2>&1",
                              shell = True,
                              stdout = subprocess.PIPE).stdout.read()
    outputS = str(output)   
    print("outputS is", outputS)
    result = outputS.find('codec')
    print ("result is", result)
    if (result == -1):
        print ("gst-discoverer-1.0 can't determine video codec type of input stream, exiting ...")
        raise SystemExit    
    input_stream_codec_type_temp = int(re.search(r'\d+', outputS).group())
    input_stream_codec_type = re.sub("[^0-9]", "", str(input_stream_codec_type_temp))

    print ("input_stream_codec_type is:", input_stream_codec_type)
    if input_encoder == "h265" or input_encoder == "H265" or input_encoder == "HEVC":
       input_encoder = "hevc"
    if input_encoder != "hevc" and input_encoder != "h264":
        print ("Input encoder needs to be h264, h265 or hevc")
        raise SystemExit

    if ((input_encoder == "hevc") and ("265" not in input_stream_codec_type)):
        print ("Given input stream format does not match with input format type argument, exiting")
        print ("Input format is:", input_encoder, "and Input stream format is:", input_stream_codec_type)
        raise SystemExit
    
    if ((input_encoder == "h264") and ("264" not in input_stream_codec_type)):
        print ("Given input stream format does not match with input format type argument, exiting")
        print ("Input format is:", input_encoder, "and Input stream format is:", input_stream_codec_type)
        raise SystemExit

    if output_encoder == "h265":
        output_encoder = "hevc"
    if output_encoder != "hevc" and output_encoder != "h264":
        print ("Output encoder needs to be h264, h265 or hevc")
        raise SystemExit

    if bitrate < 1.0 or bitrate > 25.0:
        print ("Bitrate should be between 1.0 ... 25.0 Mbit/s")
        raise SystemExit
    br =str(int(bitrate*1000))

    if ofilename[-4:] != ".mp4":
        print ("Only mp4 output file format supported")
        raise SystemExit        
    if filename[-4:] != ".mp4" and filename[-4:] != ".mov" and filename[-4:] != ".mkv" and filename[-4:] != ".MOV":
        print ("Only mp4 & mov & mkv input file format supported")
        raise SystemExit        
    
    if filename == ofilename:
        print ("Source and destination filename cannot be the same")
        raise SystemExit 
    
    startSec = time.time()
    #ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration,r_frame_rate -of default=nw=1

    output = subprocess.Popen("gst-discoverer-1.0 -v "+filename+" | grep Width: 2>&1",
                              shell = True,
                              stdout = subprocess.PIPE).stdout.read()
    outputS = str(output)    
    result = outputS.find('Width:')
    if (result == -1):
        print ("gst-discoverer-1.0 can't determine clip resolution, exiting ...")
        raise SystemExit    
    xres = int(re.search(r'\d+', outputS).group())

    output = subprocess.Popen("gst-discoverer-1.0 -v "+filename+" | grep Height: 2>&1",
                              shell = True,
                              stdout = subprocess.PIPE).stdout.read()
    outputS = str(output)    
    result = outputS.find('Height:')
    if (result == -1):
        print ("gst-discoverer-1.0 can't determine clip resolution, exiting ...")
        raise SystemExit    
    yres = int(re.search(r'\d+', outputS).group())

    # find out length of the clip such that we can determine segments sizes
    output = subprocess.Popen("gst-discoverer-1.0 -v "+filename+" | grep 'Frame rate' 2>&1",
                              shell = True,
                              stdout = subprocess.PIPE).stdout.read()

    outputS = str(output)
   
    #extract the framerate from the string
    result = outputS.find('Frame rate:')
    if (result == -1):
        print ("Can't determine framerate, exiting ...")
        raise SystemExit
    tmpS = outputS[result+11:]
    anc = tmpS.strip()
    print("tmpS is:", anc)

    framerateS = Fraction(tmpS)
    framerate = float (framerateS)
    
    print("")
    #extract the video duration from the string
    output = subprocess.Popen("gst-discoverer-1.0 -v "+filename+" | grep Duration: 2>&1",
                              shell = True,
                              stdout = subprocess.PIPE).stdout.read()
    outputS = str(output)
    result = outputS.find('Duration:')
    if (result == -1):
        print ("gst-discoverer-1.0 can't determine video length, exiting ...")
        raise SystemExit    
    video_lengthS = outputS[result+10:].split(".")[0]
    try:
        pt = datetime.strptime(video_lengthS,'%H:%M:%S')
        video_length = pt.second + pt.minute*60 + pt.hour*3600
        print("Video clip parameters:")
        print ("      length in seconds : "+str(video_length))
        print ("      length in hh:mm:ss: "+video_lengthS)
    except ValueError:
        print ("gst-discoverer-1.0 can't determine video length, exiting ...")
        raise SystemExit
    #framesinClip = framerate * video_length / split_count
    #split_length = int(video_length / split_count) + 1
    #print ("split_length is ...", split_length)
    #print ("framesinClip  is ...", framesinClip)
    
    totFrames = video_length * framerate
    nCards=num_dev2
    if float((xres/yres)/(ASPECT_RATIO)) != 1.0 :
        print ("Example script only supports 16:9 aspect ratios (e.g. 4k, 1080p, 720p)")
        raise SystemExit
    elif xres == 3840:
        chip_split_count = 1 * (int(60/framerate))
        maxFPS=nCards * 60
    elif xres == 1920:
        chip_split_count = 4 * (int(60/framerate))
        maxFPS=nCards * 240
    elif xres == 1280:
        chip_split_count = 9 * (int(60/framerate))
        maxFPS=nCards * 540
    else:
        print ("I didn't code lower than 720p, sorry!")
        raise SystemExit

    split_count = chip_split_count * nCards

    framesinClip = framerate * video_length / split_count
    split_length = int(video_length / split_count) + 1
    
    print ("split_count is ...", split_count)
    print ("split_length is ...", split_length)
    print ("framesinClip  is ...", framesinClip)



    print("      resolution: "+ str(xres)+"x"+str(yres))
    print("      framerate: "+ str(framerate))
    print("      framesinClip: "+ str(framesinClip))
    print("      split_length: "+ str(split_length))

    print ("")

    #Delete tmp and log files from previous process if any
    output = subprocess.Popen("ls -al | grep tmpfile | wc -l", shell = True, stdout = subprocess.PIPE).stdout.read()
    if int(output) > 0:
        print("Deleting previous tmp files..")
        cmd = "rm tmpfile*"
        output = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE).stdout.read()
    output = subprocess.Popen("ls -al | grep stdout | wc -l", shell = True, stdout = subprocess.PIPE).stdout.read()
    if int(output) > 0:
        print("Deleting previous log files..")
        cmd = "rm stdout*.log"
        output = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE).stdout.read()
    print ("Start splitting clip in " + str(split_count)+ " segments")
    # creating cmd to be run for splitting into segments
    if split_count != 1:
        if filename[-4:] == ".mp4" or filename[-4:] == ".mov":  
            split_cmd = "gst-launch-1.0 filesrc location=" + \
                    filename + \
                    " ! qtdemux ! splitmuxsink muxer=matroskamux max-size-time=" + str(split_length) + str("000000000") + " location=tmpfile" + "%02d." + "mkv" + " > stdout.log 2>&1 \n"
        elif filename[-4:] == ".mkv":  
            split_cmd = "gst-launch-1.0 filesrc location=" + \
                    filename + \
                    " ! matroskademux ! splitmuxsink muxer=matroskamux max-size-time=" + str(split_length) + str("000000000") + " location=tmpfile" + "%02d." + "mkv" + " > stdout.log 2>&1 \n"
    else:
        split_cmd = "gst-launch-1.0 filesrc location=" + \
                filename + \
                " ! qtdemux ! matroskamux ! filesink location=tmpfile00.mkv " + " > stdout.log 2>&1 \n"
    
    # run the command in a blocking way
    output = subprocess.Popen(split_cmd, shell = True, stdout = subprocess.PIPE).stdout.read()
       
    # check if the number of segments written equals the desired split_count
    output = subprocess.Popen("ls tmpfile* | wc -l", shell = True, stdout = subprocess.PIPE).stdout.read()
    print("      output: "+ str(output))
    if int(output) < split_count:
        print ("Video file may not be splittable ...")
        print ("Only able to create " + str(int(output)) + " segments for parallel processing")
        raise SystemExit   
    if int(output) > split_count:
        extra_chunks = int(output)-split_count
        print ("Got " + str(extra_chunks) + " extra chunks")
    print ("")
   
    n=0
    for device in range(0, num_dev2):        
        for inst in range(0, chip_split_count):        
            print ("Start transcoding segment: " + str(n))
            #Prepare transcode command based on the input format and output format
            if input_encoder == "h264" and output_encoder == "h264":
                transcode_cmd = "gst-launch-1.0 filesrc location=tmpfile" + \
                        format(n, '02d') + ".mkv" + \
                        " ! matroskademux ! h264parse ! vvas_xvcudec  dev-idx="+str(device)+" ! queue ! vvas_xvcuenc dev-idx="+str(device)+" target-bitrate="+br+" max-bitrate="+br+ \
                        " periodicity-idr=120 "+"num-slices=4 num-cores=4 "+ \
                        "!  h264parse ! qtmux ! fpsdisplaysink video-sink=\"filesink location=tmpfileout" + \
                        format(n, '02d') + ofilename[-4:] + \
                        "\" text-overlay=false sync=false -v" + \
                        " > stdout" +str(n)+".log 2>&1 & \n"
            
            elif input_encoder == "h264" and output_encoder == "hevc":
                transcode_cmd = "gst-launch-1.0 filesrc location=tmpfile" + \
                        format(n, '02d') + ".mkv" + \
                        " ! matroskademux ! h264parse ! vvas_xvcudec  dev-idx="+str(device)+" ! queue ! vvas_xvcuenc dev-idx="+str(device)+" target-bitrate="+br+" max-bitrate="+br+ \
                        " periodicity-idr=120 "+"num-slices=4 num-cores=4 "+ \
                        "!  h265parse ! qtmux ! fpsdisplaysink video-sink=\"filesink location=tmpfileout" + \
                        format(n, '02d') + ofilename[-4:] + \
                        "\" text-overlay=false sync=false -v" + \
                        " > stdout" +str(n)+".log 2>&1 & \n"
            
            elif input_encoder == "hevc" and output_encoder == "hevc":
                transcode_cmd = "gst-launch-1.0 filesrc location=tmpfile" + \
                        format(n, '02d') + ".mkv" + \
                        " ! matroskademux ! h265parse ! vvas_xvcudec  dev-idx="+str(device)+" ! queue ! vvas_xvcuenc dev-idx="+str(device)+" target-bitrate="+br+" max-bitrate="+br+ \
                        " periodicity-idr=120 "+"num-slices=4 num-cores=4 "+ \
                        "!  h265parse ! qtmux ! fpsdisplaysink video-sink=\"filesink location=tmpfileout" + \
                        format(n, '02d') + ofilename[-4:] + \
                        "\" text-overlay=false sync=false -v" + \
                        " > stdout" +str(n)+".log 2>&1 & \n"
            
            elif input_encoder == "hevc" and output_encoder == "h264":
                transcode_cmd = "gst-launch-1.0 filesrc location=tmpfile" + \
                        format(n, '02d') + ".mkv" + \
                        " ! matroskademux ! h265parse ! vvas_xvcudec  dev-idx="+str(device)+" ! queue ! vvas_xvcuenc dev-idx="+str(device)+" target-bitrate="+br+" max-bitrate="+br+ \
                        " periodicity-idr=120 "+"num-slices=4 num-cores=4 "+ \
                        "!  h264parse ! qtmux ! fpsdisplaysink video-sink=\"filesink location=tmpfileout" + \
                        format(n, '02d') + ofilename[-4:] + \
                        "\" text-overlay=false sync=false -v" + \
                        " > stdout" +str(n)+".log 2>&1 & \n"
            
            else:
                print ("Given input format and output format are not compatiable")
                print("input format is:", input_encoder, "output format is:", output_encoder)
                raise SystemExit   

            output = subprocess.Popen(transcode_cmd, shell = True)
            #changed for debuging 
            '''out, err = output.communicate()
            errcode = output.returncode
            print('output..........',out)
            print('errrrr..........',err)
            print('errcode',errcode)
            print(output,'output')
            print(transcode_cmd,'transcode_cmd')'''
            time.sleep(0.01)
            n=n+1
    
    #total_files=n+1
    #print ("Total temp files are", total_files)

    # wait until all gstreamer processes are done
    pidsExist = True
    
    tail_cmd = "tail -1 stdout0.log"
    ps_cmd = "ps -ef | grep gst-launch"  
    percentDone = 10   
    print("")
    print("  0 percent of transcoding completed")
    while pidsExist:
        time.sleep(0.1)
               
        output = subprocess.Popen(ps_cmd, shell = True, stdout = subprocess.PIPE).stdout.read()
        nr = count_substrings(str(output), "gst-launch-1.0 filesrc")
        if nr == 0:
            pidsExist = False

        output = subprocess.Popen(tail_cmd, shell = True, stdout = subprocess.PIPE).stdout.read()
        outputS = str(output)
        outputpartS = outputS[-150:]
        result = outputpartS.find('rendered:')
        if result != -1:
            frameS = outputpartS[result+10:result+20].split()
            frameN = frameS[0].partition(",")
            frame = int(frameN[0])
            if int(100.0 * frame/framesinClip) > percentDone:
                if percentDone > 95:
                    percentDone = 150
                else:
                    print(" " + str(percentDone) + " percent of transcoding completed")
                if percentDone > 89:
                    percentDone = percentDone + 5
                else:
                    percentDone = percentDone + 10

    print("")
    for n in range(0, extra_chunks):
        #Prepare transcode command based on the input format and output format
        if input_encoder == "h264" and output_encoder == "h264":
            transcode_cmd = "gst-launch-1.0 filesrc location=tmpfile" + \
                    format(split_count+n, '02d') + ".mkv" + \
                    " ! matroskademux ! h264parse ! vvas_xvcudec  dev-idx="+str(n)+" ! queue ! vvas_xvcuenc dev-idx="+str(n)+" target-bitrate="+br+" max-bitrate="+br+ \
                    " periodicity-idr=120 "+"num-slices=4 num-cores=4 "+ \
                    "!  h264parse ! qtmux ! fpsdisplaysink video-sink=\"filesink location=tmpfileout" + \
                    format(split_count+n, '02d') + ofilename[-4:] + \
                    "\" text-overlay=false sync=false -v" + \
                    " > stdout" +str(split_count+n)+".log 2>&1 & \n"
        
        elif input_encoder == "h264" and output_encoder == "hevc":
            transcode_cmd = "gst-launch-1.0 filesrc location=tmpfile" + \
                    format(split_count+n, '02d') + ".mkv" + \
                    " ! matroskademux ! h264parse ! vvas_xvcudec  dev-idx="+str(n)+" ! queue ! vvas_xvcuenc dev-idx="+str(n)+" target-bitrate="+br+" max-bitrate="+br+ \
                    " periodicity-idr=120 "+"num-slices=4 num-cores=4 "+ \
                    "!  h265parse ! qtmux ! fpsdisplaysink video-sink=\"filesink location=tmpfileout" + \
                    format(split_count+n, '02d') + ofilename[-4:] + \
                    "\" text-overlay=false sync=false -v" + \
                    " > stdout" +str(split_count+n)+".log 2>&1 & \n"
        
        elif input_encoder == "hevc" and output_encoder == "hevc":
            transcode_cmd = "gst-launch-1.0 filesrc location=tmpfile" + \
                    format(split_count+n, '02d') + ".mkv" + \
                    " ! matroskademux ! h265parse ! vvas_xvcudec  dev-idx="+str(n)+" ! queue ! vvas_xvcuenc dev-idx="+str(n)+" target-bitrate="+br+" max-bitrate="+br+ \
                    " periodicity-idr=120 "+"num-slices=4 num-cores=4 "+ \
                    "!  h265parse ! qtmux ! fpsdisplaysink video-sink=\"filesink location=tmpfileout" + \
                    format(split_count+n, '02d') + ofilename[-4:] + \
                    "\" text-overlay=false sync=false -v" + \
                    " > stdout" +str(split_count+n)+".log 2>&1 & \n"
        
        elif input_encoder == "hevc" and output_encoder == "h264":
            transcode_cmd = "gst-launch-1.0 filesrc location=tmpfile" + \
                    format(split_count+n, '02d') + ".mkv" + \
                    " ! matroskademux ! h265parse ! vvas_xvcudec  dev-idx="+str(n)+" ! queue ! vvas_xvcuenc dev-idx="+str(n)+" target-bitrate="+br+" max-bitrate="+br+ \
                    " periodicity-idr=120 "+"num-slices=4 num-cores=4 "+ \
                    "!  h264parse ! qtmux ! fpsdisplaysink video-sink=\"filesink location=tmpfileout" + \
                    format(split_count+n, '02d') + ofilename[-4:] + \
                    "\" text-overlay=false sync=false -v" + \
                    " > stdout" +str(split_count+n)+".log 2>&1 & \n"
        
        else:
            print ("Given input format and output format are not compatiable")
            print("input format is:", input_encoder, "output format is:", output_encoder)
            raise SystemExit   

        print ("Start transcoding segment: " + str(split_count+n))

        output = subprocess.Popen(transcode_cmd, shell = True)
        #changed for debuging
        '''out, err = output.communicate()
        errcode = output.returncode
        print('output..........',out)
        print('errrrr..........',err)
        print('errcode',errcode)
        print(output,'output')
        print(transcode_cmd,'transcode_cmd')'''
        time.sleep(0.01)

    # wait until all gstreamer processes are done
    pidsExist = True

    tail_cmd = "tail -1 stdout0.log"
    ps_cmd = "ps -ef | grep gst-launch"
    while pidsExist:
        time.sleep(0.1)

        output = subprocess.Popen(ps_cmd, shell = True, stdout = subprocess.PIPE).stdout.read()
        nr = count_substrings(str(output), "gst-launch-1.0 filesrc")
        if nr == 0:
            pidsExist = False

    print("100 percent of transcoding completed")   
    #start concatenating the transcoded files
    
    print("")
    print ("Start concatenating segments into final clip")
    cmd = "printf \"file '%s'\\n\" tmpfileout* > mylist.txt"
    output = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE).stdout.read()
    cmd = "rm -f " + ofilename
    output = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE).stdout.read()
    if output_encoder == "h264":
        cmd = "gst-launch-1.0 splitmuxsrc location=tmpfileout* ! h264parse ! qtmux ! filesink location=" + ofilename + " > stdout.log 2>&1"
    elif output_encoder == "hevc":
        cmd = "gst-launch-1.0 splitmuxsrc location=tmpfileout* ! h265parse ! qtmux ! filesink location=" + ofilename + " > stdout.log 2>&1"
    else:
        print ("Given output format is not supported, not able to merge encoded segments, Exiting...")
        raise SystemExit   
    output = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE).stdout.read()
    cmd = "rm tmpfile*"
    output = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE).stdout.read()
    cmd = "rm mylist.txt"
    output = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE).stdout.read()
    cmd = "rm stdout*.log"
    output = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE).stdout.read()
    endSec = time.time()
    totSec = int(endSec-startSec)

    print(" ")
    
    if totSec > 119:
        print("Time from start to completion : "+ str(totSec) + \
            " seconds (" + str(int(totSec/60)) + " minutes and " + \
            str(totSec - 60*(int(totSec/60))) + " seconds)")
    elif totSec > 59:
        print("Time from start to completion : "+ str(totSec) + \
            " seconds (1 minute and " + \
            str(totSec - 60) + " seconds)")
    else:
        print("Time from start to completion : "+ str(totSec) + \
            " seconds")
    print(" ")
    print("This clip was processed "+str(round(1.0*video_length/totSec,1))+" times faster than realtime")
    print(" ")

def destroy():
	# Release resource
    print("Exiting ...")
    
def parse_options():
    parser = OptionParser()
    parser.add_option("-s", "--sourcefile",
                      dest = "ifilename",
                      help = "input file to convert",
                      type = "string",
                      action = "store"
    )
    parser.add_option("-d", "--destinationfile",
                      dest = "ofilename",
                      help = "output file",
                      type = "string",
                      action = "store"
    )
    parser.add_option("-i", "--icodec",
                      dest = "input_encoder",
                      help = "input encode standard <h264, hevc, h265> \
                              default h264",
                      type = "string",
                      action = "store", default = "h264"
    )
    parser.add_option("-o", "--ocodec",
                      dest = "output_encoder",
                      help = "output encode standard <h264, hevc, h265> \
                              default hevc",
                      type = "string",
                      action = "store", default = "hevc"
    )
    parser.add_option("-b", "--bitrate",
                      dest = "bitrate",
                      help = "output bitrate in Mbit/s. Must be a float or integer value between 1.0 and 25.0 (example: use -b 3 to specify an output bitrate of 3Mbits/sec) \
                              default 5.0",
                      type = "float",
                      action = "store", default = 5.0
    )

    (options, args) = parser.parse_args()
    if options.ifilename and options.ofilename:
        return (options.ifilename, options.ofilename, \
                options.input_encoder, options.output_encoder,options.bitrate)
    else:
        parser.print_help()
        raise SystemExit

if __name__ == '__main__':
	try:
		main()
	# When 'Ctrl+C' is pressed, the child program 
	# destroy() will be executed.
	except KeyboardInterrupt:
		destroy()
