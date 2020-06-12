# #! /usr/bin/env python
# # -*- coding: utf-8 -*-
# """
#    DWF Python Example 2
#
#    Modified by: MURAMATSU Atsushi <amura@tomato.sakura.ne.jp>
#    Revised: 2016-04-21
#    Original Author:  Digilent, Inc.
#    Original Revision: 10/17/2013
#
#    Requires:
#        Python 2.7, 3.3 or later
# """
#
import dwf
import time
import matplotlib.pyplot as plt

print("Version: " + dwf.FDwfGetVersion())

cdevices = dwf.DwfEnumeration()
print("Number of Devices: " + str(len(cdevices)))

if len(cdevices) == 0:
    print("no device detected")
    quit()

print("Opening first device")
hdwf = dwf.Dwf(0, 2)  # idxDevice, idxCfg

n_points = 1000

print("Configure and start first analog out channel")
dwf_ao = dwf.DwfAnalogOut(hdwf)
dwf_ao.nodeEnableSet(0, dwf_ao.NODE.CARRIER, True)
print("1 = Sine wave")
dwf_ao.nodeFunctionSet(0, dwf_ao.NODE.CARRIER, dwf_ao.FUNC.SINE)
dwf_ao.nodeFrequencySet(0, dwf_ao.NODE.CARRIER, 3000.0)
# tmp = dwf_ao.nodeFrequencyGet(0, dwf_ao.NODE.CARRIER)   # WHY DOES THIS NOT WORK????!
# print(tmp)
dwf_ao.configure(0, True)

print("Configure analog in")
dwf_ai = dwf.DwfAnalogIn(hdwf)
dwf_ai.frequencySet(1e6)
print("Set range for all channels")
dwf_ai.channelRangeSet(-1, 4.0)
dwf_ai.bufferSizeSet(n_points)

print("Wait after first device opening the analog in offset to stabilize")
time.sleep(1)

print("Starting acquisition")
dwf_ai.configure(True, True)

print("   waiting to finish")
while True:
    if dwf_ai.status(True) == dwf_ai.STATE.DONE:
        break
    time.sleep(0.1)
print("   done")

print("   reading data")
rg = dwf_ai.statusData(0, n_points)

# hdwf.close()  # DONT CLOSE, I WANT TO EXPLORE

dc = sum(rg) / len(rg)
print("DC: " + str(dc) + "V")

plt.plot(rg)
plt.show()



#
# from labphew.controller.digilent.examples.dwfconstants import *
# """
#    DWF Python Example
#    Author:  Digilent, Inc.
#    Revision:  2018-07-19
#
#    Requires:
#        Python 2.7, 3
# """
#

# import dwf
#
# version = dwf.FDwfGetVersion()
# print("DWF version: " + version)
#
# device_list = dwf.DwfEnumeration()
# print('number of devices found: ', len(device_list))
# # nd = len(device_list)
# # print(f"{nd} device{['s',''][nd==1]} found: ", device_list)
# for i, dev in enumerate(device_list):
#     print(f'device {i}: {dev.userName()}, {dev.deviceName()}, {dev.SN()}')
#
# #
# # dwf_ao = dwf.DwfAnalogOut(dev)
# # dwf_a1 = dwf.DwfAnalogIn(dev)
# #
# # # out = dev.open()
# #
# # hdwf = dwf.FDwfDeviceOpen()
# #
# # dwf_ao = dwf.DwfAnalogOut()
# #
# # dwf.FDwfAnalogOutNodeSet(hdwf, 0, dwf.AnalogOutNodeCarrier, True)
# # dwf.FDwfAnalogOutNodeFunctionSet(hdwf, 0, dwf.AnalogOutNodeCarrier, dwf.funcCustom)
# #
# # dwf.FDwfDeviceOp
#
#
# #
# # from ctypes import *
# # import time
# # # from dwfconstants import *
# # import sys
# # import matplotlib.pyplot as plt
# # import numpy
# # import numpy as np
# #
# # if sys.platform.startswith("win"):
# #     dwf = cdll.dwf
# # elif sys.platform.startswith("darwin"):
# #     dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
# # else:
# #     dwf = cdll.LoadLibrary("libdwf.so")
# #
# # version = create_string_buffer(16)
# # dwf.FDwfGetVersion(version)
# # print("Version: "+str(version.value))
# #
# # cdevices = c_int()
# # dwf.FDwfEnum(c_int(0), byref(cdevices))
# # print("Number of Devices: "+str(cdevices.value))
# #
# # if cdevices.value == 0:
# #     print("no device detected")
# #     quit()
# #
# # print("Opening first device")
# # hdwf = c_int()
# # dwf.FDwfDeviceOpen(c_int(0), byref(hdwf))
# #
# # # dwf.FDwfDeviceConfigOpen(c_int(0), c_int(1), byref(hdwf))
# #
# # if hdwf.value == hdwfNone.value:
# #     print("failed to open device")
# #     quit()
# #
# # print('hdwf ', hdwf, type(hdwf))
# #
# # print("Configure and start first analog out channel")
# # dwf.FDwfAnalogOutEnableSet(hdwf, c_int(0), c_int(1))
# # dwf.FDwfAnalogOutFunctionSet(hdwf, c_int(0), funcDC)
# # dwf.FDwfAnalogOutFrequencySet(hdwf, c_int(0), c_double(3000))
# # dwf.FDwfAnalogOutAmplitudeSet(hdwf, c_int(0), c_double(4.5))
# # dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_int(1))
# # dwf.FDwfAnalogOutOffsetSet(hdwf, c_int(0), c_double(0.6))
# #
# # pvmin = c_double()
# # pvmax = c_double()
# # dwf.FDwfAnalogOutNodeAmplitudeInfo(hdwf, c_int(0), c_int(1), byref(pvmin), byref(pvmax))
# # print('minmax', pvmin, pvmax)
# #
# # pfsnode = c_int()
# # dwf.FDwfAnalogOutNodeInfo(hdwf, c_int(0), byref(pfsnode))
# # print('pfsnode: ', pfsnode.value)
# #
# # var = c_int()
# # for node in range(3):
# #     dwf.FDwfAnalogOutNodeEnableGet(hdwf, c_int(0), c_int(node), byref(var))
# #     print(f'node {node}: {var.value}')
# #
# # n_samples = 1000
# #
# # print("Configure analog in")
# # dwf.FDwfAnalogInFrequencySet(hdwf, c_double(1000000))
# # print("Set range for all channels")
# # dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(-1), c_double(4))
# # dwf.FDwfAnalogInBufferSizeSet(hdwf, c_long(n_samples))
# #
# # pvoltsMin = c_double()
# # pvoltsMax = c_double()
# # pnSteps = c_double()
# # dwf.FDwfAnalogInChannelRangeInfo(hdwf, byref(pvoltsMin), byref(pvoltsMax), byref(pnSteps))
# # print(pvoltsMin.value, pvoltsMax.value, pnSteps.value)
# #
# # rgVoltsStep = (c_double*32)()
# # pnSteps = c_int()
# # dwf.FDwfAnalogInChannelRangeSteps(hdwf, byref(rgVoltsStep), byref(pnSteps))
# # print(np.array(rgVoltsStep))
# # print('pnSteps: ', pnSteps.value)
# #
# # dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(-1), c_double(5))
# # pvoltsRange = c_double()
# # dwf.FDwfAnalogInChannelRangeGet(hdwf, c_int(0), byref(pvoltsRange))
# # print('pvoltsRange: ', pvoltsRange.value)
# #
# # f = c_double()
# # dwf.FDwfAnalogInFrequencyGet(hdwf, byref(f))
# # print('frequency is: ', f.value)
# #
# # print("Wait after first device opening the analog in offset to stabilize")
# # time.sleep(1)
# #
# # print("Starting acquisition...")
# # dwf.FDwfAnalogInConfigure(hdwf, c_int(1), c_int(1))
# #
# # sts = c_int()
# # while True:
# #     dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
# #     if sts.value == DwfStateDone.value :
# #         break
# #     time.sleep(0.1)
# # print("   done")
# #
# # # rg = (c_double*16384)()
# # rg = (c_double*n_samples)()
# # dwf.FDwfAnalogInStatusData(hdwf, c_int(0), rg, c_long(len(rg))) # get channel 1 data
# # #dwf.FDwfAnalogInStatusData(hdwf, c_int(1), rg, len(rg)) # get channel 2 data
# #
# # dwf.FDwfAnalogOutReset(hdwf, c_int(0))
# # dwf.FDwfDeviceCloseAll()
# #
# # dc = sum(rg)/len(rg)
# # print("DC: "+str(dc)+"V")
# #
# #
# #
# # plt.plot(numpy.fromiter(rg, dtype = numpy.float))
# # plt.show()
# # #
# # #
# # # t0 = time.clock()
# # # a = np.array(rg)
# # # t1 = time.clock()
# # # print(t1-t0)
# # #
# # # t0 = time.clock()
# # # a = np.asarray(rg)
# # # t1 = time.clock()
# # # print(t1-t0)
# # #
# # #
# #
# #
# #
# # data = np.array(rg)
# # d = np.diff(np.sort(data))
# # step = np.min(d[np.nonzero(d)])
# # print(step)
# # print(step*2**14)