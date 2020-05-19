# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 14:26:43 2019

@author: Sam, Rinske
"""

from ctypes import *
from dwfconstants import *
import math
import time
import matplotlib.pyplot as plt
import sys
import os
import numpy as np
import datetime

############################################################
#### Initialize a connection with the Analog Discovery 2 ###
############################################################  

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

#declare ctype variables
hdwf = c_int()
sts = c_byte()
rgdSamples1 = (c_double*1)()
rgdSamples2 = (c_double*1)()

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

dwf.FDwfParamSet(DwfParamOnClose, c_int(1)) # 0 = run, 1 = stop, 2 = shutdown

#open device
print("Opening first device")
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

if hdwf.value == hdwfNone.value:
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(szerr.value)
    print("failed to open device")
    input("Press enter to quit")
    quit()

######################################################################
### Create directories and a file in which the data will be stored ###
######################################################################

d = os.path.dirname(__file__) # directory of script
pathindex = 0
pathstring = 'calibration_results'+str(datetime.date.today())+'_'+str(pathindex)
p = pathstring.format(d) # path to be created

try:
    os.makedirs(p)
except OSError:
    while pathindex<100:
        pathindex=pathindex+1
        pathstring = 'calibration_results'+str(datetime.date.today())+'_'+str(pathindex)
        p = pathstring.format(d)
        try:
            os.makedirs(p)
        except OSError:
            pass
        else:
            break
      
def make_voltage_list(line, filename=p+"/photodiode_voltage_list.dat"):
    with open(filename, "a") as myfile:
        myfile.write(line)  

##########################################################
### Create a function to write away the acquired data ###
##########################################################

while True:
    try:
        d = float(input("Please enter d in cm: "))  
    except:
        print("**ERROR** Could not process user input. Make sure you use a dot instead of komma. Please try again.")
        continue
    break
while True:
    try:
        Reff = float(input("Please enter Reff in cm: "))  
    except:
        print("**ERROR** Could not process user input. Make sure you use a dot instead of komma. Please try again.")
        continue
    break
while True:
    try:
        x0 = float(input("Please enter x0 in cm: "))  
    except:
        print("**ERROR** Could not process user input. Make sure you use a dot instead of komma. Please try again.")
        continue
    break
make_voltage_list(str(d)+" "+str(Reff)+" "+str(x0)+"\n")  
make_voltage_list("Calibration step, xi (cm), Vdiode (V), sigma Vdiode, V_ch2 (V), sigma Vch2 \n")
        
def yes_or_no(question):
    reply = str(input(question+' (y/n): ')).lower().strip()
    if reply == '':
        return yes_or_no("Please answer the question...")
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        return yes_or_no("Please answer the question...")

#############################################################
### Initialize the oscilloscope on the Analog Discovery 2 ### 
#############################################################
        
cBufMax = c_int()
dwf.FDwfAnalogInBufferSizeInfo(hdwf, 0, byref(cBufMax))
print("Device buffer size: "+str(cBufMax.value))     
#set up acquisition
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(20000000.0))
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(1)) 
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(5))

#wait at least 2 seconds for the offset to stabilize
time.sleep(2.0)

###################################################
### Start data collection with the oscilloscope ###
###################################################

x_list = []
n=1
question = "Would you like to do a measurement?"  
    
while yes_or_no(question):
    while True:
        try:
            print("Place a mass to put the Balance Beam in a different position")
            xi = float(input("Input the value measured for x"+str(n)+" in cm: "))
        except:
            print("**ERROR** Could not process user input. Make sure you use a dot instead of komma. Please try again.")
            continue
        break
    x_list.append(xi)
    
    i=0
    number_of_iterations = 4000
    dc1list=[]
    dc2list=[]
    
    while i<number_of_iterations:
        print("Starting oscilloscope")
        dwf.FDwfAnalogInConfigure(hdwf, c_bool(False), c_bool(True))
        
        while True:
            dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
            if sts.value == DwfStateDone.value :
                break
            #time.sleep(0.1)
       
        
        ##########################################################################
        ### Import the oscilloscope data and write it away in the voltage list ###
        ##########################################################################
    
        dwf.FDwfAnalogInStatusData(hdwf, 0, rgdSamples1, 1) # get channel 1 data, should be the photodiode voltage
        dwf.FDwfAnalogInStatusData(hdwf, 1, rgdSamples2, 1) # get channel 2 data, should be the coil voltage
        
        dc1 = np.mean(rgdSamples1)
        sigma_dc1 = np.std(rgdSamples1)
        #print("DC1: "+str(dc1)+"V")
        #print("Standarddeviation1: "+str(sigma_dc1)+"V")
        dc1list=np.append(dc1list, dc1)
        
        dc2 = sum(rgdSamples2)/len(rgdSamples2)
        sigma_dc2 = np.std(rgdSamples2)
        #print("DC2: "+str(dc2)+"V")
        #print("Standarddeviation2: "+str(sigma_dc2)+"V")
        dc2list=np.append(dc2list, dc2)
        
        i=i+1
    
    dc1mean = np.mean(dc1list)
    dc2mean = np.mean(dc2list)
    stddc1 = np.std(dc1list)
    stddc2 = np.std(dc2list)

    print(dc1mean)
    print(stddc1) print("Acquisition done")
        print("You can now remove the mass")
    make_voltage_list(str(n)+" "+str(xi)+" "+str(dc1mean)+" "+str(stddc1)+" "+str(dc2mean)+" "+str(stddc2)+"\n")
    n=n+1
    #wait 1 ms before acquiring another measurement
    time.sleep(0.001)
    
    
print("Calibration data acquisition finished. The data is stored in photodiode_voltage_list.dat.")
input("Press Enter to exit the console")
dwf.FDwfDeviceCloseAll()
############
### End ### 
########### 