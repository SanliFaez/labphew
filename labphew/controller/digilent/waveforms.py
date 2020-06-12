


import logging
import dwf

import time
import matplotlib.pyplot as plt
from ctypes import *



class DfwController(dwf.Dwf):
    def __init__(self, device_number=0, config=0):
        super().__init__(device_number, config)
        # self.buffer_ai = self.ai.bufferSizeInfo()

        self.AnalogIn = dwf.DwfAnalogIn(self)
        self.AnalogOut = dwf.DwfAnalogOut(self)
        self.DigitalIn = dwf.DwfDigitalIn(self)
        self.DigitalOut = dwf.DwfDigitalOut(self)

        self.AnalogIO = dwf.DwfAnalogIO(self)
        self.DigitalIO = dwf.DwfDigitalIO(self)

        # create short name references
        self.ai = self.AnalogIn
        self.ao = self.AnalogOut
        self.di = self.DigitalIn
        self.do = self.DigitalOut



def close_all():
    """Close all Digilent "WaveForms" devices"""
    dwf.FDwfDeviceCloseAll()

def enumerate_devices():
    """List connected devices and their possible configurations."""

    print(dwf.FDwfGetLastErrorMsg())
    # enumerate devices
    devs = dwf.DwfEnumeration()
    ch = lambda n=0, b=0: {'ch': n, 'buf': b}
    devices = []
    for i, device in enumerate(devs):
        dev_dict = {'info': {}, 'configs': []}
        dev_dict['info']['SN'] = device.SN()
        dev_dict['info']['deviceName'] = device.deviceName()
        dev_dict['info']['userName'] = device.userName()
        dev_dict['dev'] = device

        if not device.isOpened():
            dwf_ai = dwf.DwfAnalogIn(device)
            channel = dwf_ai.channelCount()
            _, hzFreq = dwf_ai.frequencyInfo()
            # print("\tAnalog input channels: " + str(channel))
            dev_dict['info']['maxAIfreq'] = hzFreq
            dwf_ai.close()

        n_configs = dwf.FDwfEnumConfig(i)
        for iCfg in range(0, n_configs):
            aic = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIAnalogInChannelCount)  # 1
            aib = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIAnalogInBufferSize)  # 7
            aoc = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIAnalogOutChannelCount)  # 2
            aob = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIAnalogOutBufferSize)  # 8
            dic = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIDigitalInChannelCount)  # 4
            dib = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIDigitalInBufferSize)  # 9
            doc = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIDigitalOutChannelCount)  # 5
            dob = dwf.FDwfEnumConfigInfo(iCfg, dwf.DECIDigitalOutBufferSize)  # 10
            dev_dict['configs'].append({'ai': ch(aic, aib), 'ao': ch(aoc, aob), 'di': ch(dic, dib), 'do': ch(doc, dob)})

        devices.append(dev_dict)
    # ensure all devices are closed
    dwf.FDwfDeviceCloseAll()
    return devices

def print_device_list(devices):
    for i, device in enumerate(devices):
        print("------------------------------")
        print("Device " + str(i) + " : ")
        print("\tdeviceName:\t" + device['info']['deviceName'])
        print("\tuserName:\t" + device['info']['userName'])
        print("\tSN:\t\t\t" + device['info']['SN'])
        print("\tmaxAIfreq:\t" + str(device['info']['maxAIfreq']))
        print('\tConfig AnalogIN   AnalogOUT  DigitalIN   DigitalOUT')
        for iCfg, conf in enumerate(device['configs']):
            print('\t{}      {} x {:<5}  {} x {:<5}  {:2} x {:<5}  {:2} x {:<5}'.format(
                iCfg, conf['ai']['ch'], conf['ai']['buf'],
                      conf['ao']['ch'], conf['ao']['buf'],
                      conf['di']['ch'], conf['di']['buf'],
                      conf['do']['ch'], conf['do']['buf']))

if __name__ == '__main__':

    # display a list of devices and their possible configurations
    devices = enumerate_devices()
    print_device_list(devices)

    # create object with
    daq = DfwController(0, 0)


    # daq.ao.nodeFunctionSet(ch, daq.ao.NODE.CARRIER, daq.ao.FUNC.DC)
    # daq.ao.nodeFunctionSet(ch, daq.ao.NODE.CARRIER, daq.ao.FUNC.SINE)


    print("\nConfigure and first analog out channel")
    ch_out = 0

    print('Carrier: "sine", 0.4V, 6kz, offset 1V')
    daq.ao.nodeEnableSet(ch_out, daq.ao.NODE.CARRIER, True)
    daq.ao.nodeFunctionSet(ch_out, daq.ao.NODE.CARRIER, daq.ao.FUNC.SINE)
    daq.ao.nodeFrequencySet(ch_out, daq.ao.NODE.CARRIER, 6000.0)
    daq.ao.nodePhaseSet(ch_out, daq.ao.NODE.CARRIER, 0)
    daq.ao.nodeAmplitudeSet(ch_out, daq.ao.NODE.CARRIER, 0.4)
    daq.ao.nodeOffsetSet(ch_out, daq.ao.NODE.CARRIER, 1.0)

    print('Amplitude Modulation: "ramp up", 400Hz, 100%')
    daq.ao.nodeEnableSet(ch_out, daq.ao.NODE.AM, True)
    daq.ao.nodeFunctionSet(ch_out, daq.ao.NODE.AM, daq.ao.FUNC.RAMP_UP)
    daq.ao.nodeFrequencySet(ch_out, daq.ao.NODE.AM, 400.0)
    daq.ao.nodePhaseSet(ch_out, daq.ao.NODE.AM, 0)
    daq.ao.nodeAmplitudeSet(ch_out, daq.ao.NODE.AM, 100)

    print('Frequency Modulation: "square", 100Hz, 20%, phase 90 degrees')
    daq.ao.nodeEnableSet(ch_out, daq.ao.NODE.FM, True)
    daq.ao.nodeFunctionSet(ch_out, daq.ao.NODE.FM, daq.ao.FUNC.SQUARE)
    daq.ao.nodeFrequencySet(ch_out, daq.ao.NODE.FM, 100.0)
    daq.ao.nodePhaseSet(ch_out, daq.ao.NODE.FM, 90)
    daq.ao.nodeAmplitudeSet(ch_out, daq.ao.NODE.FM, 20)

    print("\nConfigure analog in")
    print('Sampling rate 100kHz, 1000 points (i.e. 10ms)')
    n_points = 1000
    daq.ai.frequencySet(1e5)
    print("Set range for all channels")
    daq.ai.channelRangeSet(-1, 4.0)
    daq.ai.bufferSizeSet(n_points)
    daq.ai.channelAttenuationSet(0, 0.5)

    print("\nStarting output and starting acquisition")
    daq.ao.configure(ch_out, True)
    daq.ai.configure(True, True)

    # print("   waiting to finish")
    # while True:
    #     if daq.ai.status(True) == daq.ai.STATE.DONE:
    #         break
    #     time.sleep(0.1)
    # print("   done")

    timeout = 0.1 + 16400 / daq.ai.frequencyGet()
    t0 = time.time()
    while daq.ai.status(True) != daq.ai.STATE.DONE:
        time.sleep(0.001)
        if time.time() > t0 + timeout:
            print('timeout occured')
            break



    print("   reading data")
    rg = daq.ai.statusData(0, n_points)

    # hdwf.close()  # DONT CLOSE, I WANT TO EXPLORE

    dc = sum(rg) / len(rg)
    print("DC: " + str(dc) + "V")

    plt.plot(rg)
    plt.show()

    # daq.ao.configure(ch_out, 0)
    # daq.ao.reset()
    # daq.ao.nodeFunctionSet(ch_out, daq.ao.NODE.CARRIER, daq.ao.FUNC.DC)
    # daq.ao.nodeOffsetSet(ch_out, daq.ao.NODE.CARRIER, -0.7)
    # print("\nStarting output")
    # daq.ao.configure(ch_out, True)
    #
    # n_points = 10
    # daq.ai.frequencySet(1000)
    # print("Set range for all channels")
    # daq.ai.channelRangeSet(-1, 4.0)
    # daq.ai.bufferSizeSet(n_points)
    #
    # print("\nStarting input")
    # daq.ai.configure(True, True)
    #
    # while daq.ai.status(True):
    #     time.sleep(0.001)
    #
    # print("   reading data")
    # rg = daq.ai.statusData(0, n_points)
    # print(rg)


# TODO:
# attenuation analog in
# single shot ???
