"""
to do:
Licence needs to be added
Variables may be stated at the beginning of the code    
Understand the buffer
understand raw data output
fix std I since the raw data cannot be devided 
Save raw data
Fix the analyses such that it can be integrated into this code      
"""    

from ctypes import *
from labphew.controller.digilent.examples.dwfconstants import *
import math
import time
import sys
import os
import matplotlib.pyplot as plt
import numpy as np

#Variables
measnr = 0          #Change this number before a measurement
meas = 5            #The total number of measurements (steps in increasing voltage) 
NSamples = 40       #The number of measurements per single voltage
Resistance = 220    #The resistance (Ohm) of the resistor for channel 2
dV=0.01             #Stepsize (increase of voltage) between measurements 
V0 = 0              #Initial voltage level at first measurement

#This is the direction the data is saved to, according to the measurement number
os.makedirs("measurements//meas" + str(measnr), exist_ok=True)

#making this compattible to work from windows and macOS
if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

#declare ctype variables
hdwf = c_int()
sts = c_byte()
rgdSamples1 = (c_double*40)()
rgdSamples2 = (c_double*40)()
hzSys = c_double()
channel = c_int(0)

#Define number of measurements (meas) and number of samples per measurement (NSamples)
Vdata = []
Idata = []
Vstddata = []
Istddata = []

#Creating the signal on Wavegen 1
print("Opening device")
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

if hdwf.value == 0:
    print("failed to open device")
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()

dwf.FDwfAnalogOutNodeEnableSet(hdwf, channel, AnalogOutNodeCarrier, c_bool(True))

#For loop for increasing the voltage each step with a

for i in range(meas):
    #Function is set to DC with the value set as offset (last parameter of OffsetSet)
    dwf.FDwfAnalogOutNodeFunctionSet(hdwf, channel, AnalogOutNodeCarrier, funcDC)
    dwf.FDwfAnalogOutNodeOffsetSet(hdwf, channel, AnalogOutNodeCarrier, c_double(V0 + dV*i))
    
    #From here the measurment of the signal starts
    cBufMax = c_int()
    
    #set up acquisition
    dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
    dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(1), c_bool(True))
    dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(5))
    dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(1), c_double(5))
    
    #wait at least 2 seconds for the offset to stabilize
    time.sleep(2)
    
    dwf.FDwfAnalogInConfigure(hdwf, c_bool(False), c_bool(True))
    
    while True:
        dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
        if sts.value == DwfStateDone.value :
            break
        time.sleep(0.1)

    #print("Acquisition " + str(i) + " done")
    
    dwf.FDwfAnalogInStatusData(hdwf, 0, rgdSamples1, NSamples) # get channel 1 data
    dwf.FDwfAnalogInStatusData(hdwf, 1, rgdSamples2, NSamples) # get channel 2 data
    dwf.FDwfDigitalOutReset(hdwf)
    
    #rgdSamples are all sample measurements. Taking the mean and std gives a single point per voltage
    V = sum(rgdSamples1)/len(rgdSamples1)
    stdV = np.std(rgdSamples1)
    Vdata.append(V)
    Vstddata.append(stdV)
    
    I = sum(rgdSamples2)/len(rgdSamples2)/Resistance
    stdI = np.std(rgdSamples2)
    Idata.append(I)
    Istddata.append(stdI)
        
dwf.FDwfDeviceCloseAll()

#Saving the mean and the std data. 
np.savetxt("measurements//meas"+ str(measnr) +"//V.txt", Vdata, fmt='%1.6f')
np.savetxt("measurements//meas"+ str(measnr) +"//I.txt", Vstddata, fmt='%1.6f')
np.savetxt("measurements//meas"+ str(measnr) +"//Vstd.txt", Idata, fmt='%1.6f')
np.savetxt("measurements//meas"+ str(measnr) +"//Istd.txt", Istddata, fmt='%1.6f')

    
#b= np.loadtxt('/Users/milocollaris/Documents/UU/Masters/Experiment_Design/measurements/meas0/a.txt')    
#print(b)    
    
    
########################################################################
## Here the analysis can be added once finished. Still save the data. ##
########################################################################