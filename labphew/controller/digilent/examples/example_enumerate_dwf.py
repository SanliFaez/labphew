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

    print('\tConf  AnalogIN   AnalogOUT  DigitalIN   DigitalOUT')
    for iCfg in range(0, n_configs):
        # sz = "\t"+str(iCfg)+"."
        aic = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIAnalogInChannelCount) # 1
        # sz += " AnalogIn: "+str(cInfo)
        aib = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIAnalogInBufferSize) # 7
        # sz += " x "+str(cInfo)
        aoc = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIAnalogOutChannelCount) # 2
        # sz += " \tAnalogOut: "+str(cInfo)
        aob = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIAnalogOutBufferSize) # 8
        # sz += " x "+str(cInfo)
        dic = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIDigitalInChannelCount) # 4
        # sz += " \tDigitalIn: "+str(cInfo)
        dib = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIDigitalInBufferSize) # 9
        # sz += " x "+str(cInfo)
        doc = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIDigitalOutChannelCount) # 5
        # sz += " \tDigitalOut: "+str(cInfo)
        dob = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIDigitalOutBufferSize) # 10
        # sz += " x "+str(cInfo)
        # print(sz)
        print('\t{}     {} x {:<5}  {} x {:<5}  {:2} x {:<5}  {:2} x {:<5}'.format(iCfg, aic,aib,aoc,aob,dic,dib,doc,dob))


    if not device.isOpened():
        dwf_ai = dwf.DwfAnalogIn(device)
        channel = dwf_ai.channelCount()
        _, hzFreq = dwf_ai.frequencyInfo()
        print("\tAnalog input channels: " + str(channel))
        print("\tMax freq: " + str(hzFreq))
        dwf_ai.close()

# ensure all devices are closed
dwf.FDwfDeviceCloseAll()