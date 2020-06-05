import dwf
import sys

# check library loading errors, like: Adept Runtime not found
print(dwf.FDwfGetLastErrorMsg())

# print DWF version
print("DWF Version: " + dwf.FDwfGetVersion())

# enumerate and print device information
devs = dwf.DwfEnumeration()
print("Number of Devices: " + str(len(devs)))

for i, device in enumerate(devs):
    print("------------------------------")
    print("Device " + str(i) + " : ")
    print("\t" + device.deviceName())
    print("\t" + device.SN())

    n_configs = device.config()
    # q = dwf.FDwfEnumConfig(i)

    n_configs = dwf.FDwfEnumConfig(i)

    for iCfg in range(0, n_configs):
        sz = "\t"+str(iCfg)+"."
        cInfo = dwf.FDwfEnumConfigInfo(iCfg, 1) # DECIAnalogInChannelCount
        sz += " AnalogIn: "+str(cInfo)
        cInfo = dwf.FDwfEnumConfigInfo(iCfg, 7) # DECIAnalogInBufferSize
        sz += " x "+str(cInfo)
        cInfo = dwf.FDwfEnumConfigInfo(iCfg, 2) # DECIAnalogOutChannelCount
        sz += " \tAnalogOut: "+str(cInfo)
        cInfo = dwf.FDwfEnumConfigInfo(iCfg, 8) # DECIAnalogOutBufferSize
        sz += " x "+str(cInfo)
        cInfo = dwf.FDwfEnumConfigInfo(iCfg, 4) # DECIDigitalInChannelCount
        sz += " \tDigitalIn: "+str(cInfo)
        cInfo = dwf.FDwfEnumConfigInfo(iCfg, 9) # DECIDigitalInBufferSize
        sz += " x "+str(cInfo)
        cInfo = dwf.FDwfEnumConfigInfo(iCfg, 5) # DECIDigitalOutChannelCount
        sz += " \tDigitalOut: "+str(cInfo)
        cInfo = dwf.FDwfEnumConfigInfo(iCfg, 10) # DECIDigitalOutBufferSize
        sz += " x "+str(cInfo)
        print(sz)


    if not device.isOpened():
        dwf_ai = dwf.DwfAnalogIn(device)
        channel = dwf_ai.channelCount()
        _, hzFreq = dwf_ai.frequencyInfo()
        print("\tAnalog input channels: " + str(channel))
        print("\tMax freq: " + str(hzFreq))
        dwf_ai.close()

# ensure all devices are closed
dwf.FDwfDeviceCloseAll()