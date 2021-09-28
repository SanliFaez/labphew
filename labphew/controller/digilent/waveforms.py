"""
=============================
Digilent WaveForms Controller
=============================

This module is made to control `Digilent WaveForms <https://store.digilentinc.com/waveforms-download-only/>`_ compatible devices.
It is developed with the `Analog Discovery 2 <https://reference.digilentinc.com/reference/instrumentation/analog-discovery-2/start>`_ but probably also works for the other devices.

It depends on `Digilent's DWF library wrapper <https://pypi.org/project/dwf/>`_ (pip install dwf) which provides a pythonic way of interacting with the WaveForms dll.
The DfwController class inherits from the Dwf class of the dwf module, meaning all functionality of Dwf is available.
In addition the input and output channels are made available internally and basic methods are added to read and write analog values.
The example code at the end shows both examples of using these basic methods and of interacting with the more complex inherited methods.

Unfortunately there's no extended documentation for the dwf module, but original functions to interact with the dll are
described in the `WaveForms SDK Reference Manual <https://s3-us-west-2.amazonaws.com/digilent/resources/instrumentation/waveforms/waveforms_sdk_rm.pdf>`_.
Using an autocompleting IDE it's possible to explore the available methods and find the documentation of the corresponding functions in the WaveForms SDK Reference Manual.

In addition to the DfwController class this module contains functions to explore which devices are connected and to close connections.

"""
import logging
import dwf
import time
import numpy as np


class DfwController(dwf.Dwf):
    """
    Controller for Digilent devices controlled through WaveForms software
    """
    def __init__(self, device_number=0, config=0):
        """
        Connect to device with optional configuration.

        It connects to device with device_number as listed by the enumerate_devices() function of this module.
        Note that the default value of 0 will simply connect to the first device found.
        The possible configurations are also returned by enumerate_devices(). Note that enumerate devices is run at time
        of module import and stored in the variable devices. Note that the information returned by enumerate_devices()
        (or stored in the variable devices) can be diplayed in more readable form with the function print_device_list()
        of this module.

        :param device_number: the device number (default: 0)
        :type device_number: int
        :param config: configuration number (default: 0)
        :type config: int
        """
        self.logger = logging.getLogger(__name__)
        super().__init__(device_number, config)

        self.AnalogIn = dwf.DwfAnalogIn(self)
        self.AnalogOut = dwf.DwfAnalogOut(self)
        self.DigitalIn = dwf.DwfDigitalIn(self)
        self.DigitalOut = dwf.DwfDigitalOut(self)

        # Not sure yet what these do:
        self.AnalogIO = dwf.DwfAnalogIO(self)
        self.DigitalIO = dwf.DwfDigitalIO(self)

        # create short name references
        self.ai = self.AnalogIn
        self.ao = self.AnalogOut
        self.di = self.DigitalIn
        self.do = self.DigitalOut

        self.basic_analog_return_std = False  # will be overwritten by preset_basic_analog()
        self._read_timeout = 1  # will be overwritten by preset_basic_analog()
        self._last_ao0 = 0  # will be overwritten by write_analog()
        self._last_ao1 = 0  # will be overwritten by write_analog()
        self._time_stabilized = time.time()  # will be overwritten by write_analog()
        self.preset_basic_analog()

        self.logger.debug('DfwController object created')

    def preset_basic_analog(self, n=80, freq=10000, range=50.0, return_std=False):
        """
        Apply settings for read_analog() and write_analog()
        Please note that there may be a significant overhead (delay) for reading which seems to be larger for lower
        frequencies and oddly seems to be larger for collecting a small number of points.
        The default values of averaging over 82 points at 10kHz results in <10ms per averaged datapoint.

        :param n:     number of datapoints to collect and average (default 85)
        :type n:      int
        :param freq:  analog in frequency (default 10000)
        :type freq:   int or float or None
        :param range: the voltage range for the ADC (5.0 or 50.0) (default 50.0)
        :type range:  int or float or None
        :param return_std: also returns the standard deviations (default False)
        :type return_std:  bool
        """
        self.ao.reset()
        self.ai.reset()
        self.ao.nodeFunctionSet(-1, self.ao.NODE.CARRIER, self.ao.FUNC.DC)
        self.ao.configure(-1, 3)  # apply
        self.ai.bufferSizeSet(n)
        self.ai.frequencySet(freq)
        self.ai.channelRangeSet(-1, range)
        self.ai.configure(1, 0)  # apply config to AI, but not start
        # self._read_timeout = 1.9 + self.ai.bufferSizeGet() / self.ai.frequencyGet()
        self.ao.configure(-1, 1)
        self.basic_analog_return_std = False

    def stop_analog_out(self, channel=-1):
        """
        Basic method to stop analog output.

        :param channel: analog out channel to stop (default is -1, meaning all channels)
        :type channel: int
        """
        self.ao.configure(channel, 0)

    def write_analog(self, volt, channel=-1, enable=True):
        """
        Basic method to apply voltage to analog out channels (the Arbitrary Waveform Generator (AWG) pins W1 and W2).
        Not that these pins can only supply about 2mA.
        In the background it also approximates the timestamp when the output will be stabilize (based on the change in voltage applied).
        To wait for that timestamp, call wait_for_stabilization()

        :param volt: voltage to apply (in Volt)
        :type vol: float
        :param channel: analog out channel to set (default is -1, meaning all channels)
        :type channel: int
        :param delay: delay (s) to wait after setting output to allow for stabilization
        :type delay: float
        """
        self.ao.nodeOffsetSet(channel, self.ao.NODE.CARRIER, volt)
        self.ao.configure(channel, enable)
        if channel == 0 or channel == -1:
            self._time_stabilized = max(self._time_stabilized, time.time()+0.013+0.005*abs(self._last_ao0-volt))
            self._last_ao0 = volt
        if channel == 1 or channel == -1:
            self._time_stabilized = max(self._time_stabilized, time.time()+0.013+0.005*abs(self._last_ao1-volt))
            self._last_ao1 = volt

    def wait_for_stabilization(self):
        """
        Waits for the output to stabilize. Note that this is calculated and approximated, not actively measured or verified.

        :return: the amount of time waited (s)
        :rtype: float
        """
        wait = self._time_stabilized - time.time()
        if wait > 0:
            time.sleep(wait)
            return wait
        return 0

    def read_analog(self):
        """
        Basic method to read voltage of analog in channels.
        See preset_basic_analog() to setup specifics for reading.
        Returns both channels.
        (Also returns standard deviations if self.basic_analog_return_std is True)

        :return: the analog values of both AI channels (and possibly the standard deviations)
        :rtype: float, float [,float, float] (or None's in case of read timeout)
        """
        self.ai.configure(0, 1)  # start acquisition
        if self.wait_for_ai_acquisition():
            return tuple([None, None])*(1 + self.basic_analog_return_std)  # return the right amount of None's
        buf = self.ai.bufferSizeGet()
        c0 = np.array(self.ai.statusData(0, buf))
        c1 = np.array(self.ai.statusData(1, buf))
        if self.basic_analog_return_std:
            return c0.mean(), c1.mean(), c0.std(), c1.std()
        else:
            return c0.mean(), c1.mean()

    def wait_for_ai_acquisition(self, start_timestamp=None):
        """
        Waits while ai status is busy. Uses the AI frequency and buffersize in combination with start_timestamp to
        calculate a read timeout. If no start_timestamp is supplied it uses time at moment of calling the method.
        It returns True if timeout occurred and None if acquisition finished regularly.

        :param start_timestamp: the timestamp (as returned by time.time()) from which to calculate how long to wait
        :type start_timestamp: float or None
        :return: True for timeout, None when nothing happened
        :rtype: True or None
        """
        if start_timestamp is None:
            start_timestamp = time.time()
        read_timeout = 1.9 + self.ai.bufferSizeGet() / self.ai.frequencyGet()
        while self.ai.status(True) != self.ai.STATE.DONE:
            if time.time() > start_timestamp + read_timeout:
                self.logger.error('AI read timeout occured')
                return True

    def power_supply(self, positive=None, negative=None, enable=True):
        # """
        # Set the voltage for the positive programmable power supply (V+, V-).
        # These can supply larger current than the AWG pins, but are slower,
        # probably less accurate and technically not rated for voltages
        # below 0.5V (although they still appear to operate).
        #
        # Both V+ and V- may be set at once: power_supply(3.3, -1.1)
        # Or positive only: power_supply(3.3) or power_supply(positive=3.3)
        # Or negative only: power_supply(negative=-1.1)
        # The outputs are enabled by default. To disable set enable=False
        #
        # :param positive: (optional) Voltage to apply to V+ (between 0 and 5)
        # :type positive: float
        # :param negative: (optional) Voltage to apply to V- (between -5 and 0)
        # :type negative: float
        # :param enable: (optional) enable the output (default is True)
        # :type enable: bool
        # """
        if positive is not None:
            if positive > 5.0:
                self.logger.warning("positive power supply cannot be higher than 5.0. Setting V+ to 5.0V")
                positive = 5.0
            if positive < 0:
                self.logger.warning("positive power supply cannot be lower than 0. Setting V+ to 0V")
                positive = 0.0
            self.AnalogIO.channelNodeSet(0, 1, positive)  # set V+ value
        if negative is not None:
            if negative < -5.0:
                self.logger.warning("negative power supply cannot be lower than 5.0. Setting V- to -5.0V")
                negative = -5.0
            if negative > 0:
                self.logger.warning("negative power supply cannot be higher than 0. Setting V- to 0V")
                negative = 0.0
            self.AnalogIO.channelNodeSet(1, 1, negative)  # set V- value
        if not enable:
            self.AnalogIO.enableSet(False)
            self.AnalogIO.channelNodeSet(0, 0, False)
            self.AnalogIO.channelNodeSet(1, 0, False)
            self.logger.info('Disabling V+, V- and power supply master')
        else:
            if positive is not None and self.AnalogIO.channelNodeGet(0, 0) != bool(positive):
                self.AnalogIO.channelNodeSet(0, 0, bool(positive))
                self.logger.info('Enabling V+')
            if negative is not None and self.AnalogIO.channelNodeGet(1, 0) != bool(negative):
                self.AnalogIO.channelNodeSet(1, 0, bool(negative))
                self.logger.info('Enabling V-')
            if not self.AnalogIO.enableGet():
                self.AnalogIO.enableSet(True)
                self.logger.info('Enabling power supply master')

    def read_digital(self, as_list=True):
        """
        Returns a list of all 16 pins values (regardless of whether it is
        in Input or Output mode).
        Optionally by setting as_list=False, it returns the values as a single
        "16 bit integer" where the bits represent the pins.

        :param as_list: (optional, default is True)
        :type as_list:
        :return: list of 16, 0 or 1 values (or "16 bit integer")
        :rtype: list (or int)
        """
        status = self.DigitalIO.inputStatus()
        if as_list:
            return self._convert_number_to_list(status)
        else:
            return status

    def _convert_number_to_list(self, number):
        """
        Internal helper function that converts a number to a list where the
        elements represent the values of the bits.

        :param number: integer in range [0 - 65535]
        :type number: int
        :return: list consisting of 0 and 1, of length 16
        :rtype: list
        """
        if number < 0 or number > 65535:
            self.logger.error("Number out of range [0 - 65535]")
            return
        return [int(c) for c in '{0:016b}'.format(number)[::-1]]

    def _convert_value_and_pin_to_bits(self, value, pin=None):
        """
        Internal helper function that does a lot of argument type checking
        (with appropriate error messages) and converts it to the number
        required by dwf module (where the bits represent the pins).
        It can take an iterable (list/tuple/array) of 16 boolean (0, 1)
        elements as input, or a number where the bits represent the state, or
        a single value and pin number can be specified. In the latter case,
        when the value is 0 (or False) it will return the "inverted" number,
        i.e. all bits are 1 except the one specified by 'pin'.

        :param value: mode of specific pin, or list of all pins, or "16 bit integer"
        :type value: int or list
        :param pin: (optional) pin number [0 - 16]
        :type pin: int
        :return: the "16 bit integer" where each bit represents a pin
        :rtype: int
        """
        if pin is not None:
            if type(pin) is not int or pin<0 or pin>15:
                self.logger.error("If pin is specified it needs to be an integer [0 - 15]")
                return
            if type(value) is not bool and (type(value) is not int or value not in (0,1)):
                self.logger.error("When specifing pin number, the value needs to be a single boolean, or a 0 or a 1")
                return
            ret = 1 << pin
            if value == 0:
                return 65535 - ret
            else:
                return ret
        elif type(value) is int:
            if value<0 or value > 65535:
                self.logger.error("When specifing the number directly it needs to be in range [0 - 65535]")
                return
            return value
        else:
            try:
                iterator = iter(value)
                assert(len(value)==16)
            except TypeError:
                self.logger.error("When not specifying the pin, a list/tuple/array of 16 elements needs to be passed, or a single number")
                return
            ret = 0
            for v in reversed(value):
                ret <<= 1
                ret += v
            return ret

    def get_IO_pin_mode(self, as_list=True):
        """
        Returns a list of all 16 pin modes. 1 means Output, 0 means Input.
        Optionally by setting as_list=False, it returns the values as a single
        "16 bit integer" where the bits represent the pins.

        :param as_list: (optional, default is True)
        :type as_list:
        :return: list of 16, 0 or 1 values (or "16 bit integer")
        :rtype: list (or int)
        """
        modes = self.DigitalIO.outputEnableGet()
        if as_list:
            return self._convert_number_to_list(modes)
        else:
            return modes

    def set_IO_pin_mode(self, value, pin=None):
        """
        Set the mode of one or all digital IO pins.
        True or 1 means Output, False or 1 means Input.
        To set one specific pin: specify value (True, False, 0 or 1) and
        pin-number [0 - 16].
        To set all pins at once, one can specify a list (of length 16), or
        specify the integer number where each bit represents a pin.

        :param value: mode of specific pin, or list of all pins, or "16 bit integer"
        :type value: int, or list
        :param pin: (optional) pin number [0 - 16]
        :type pin: int

        """
        if value == 'all':
            change_modes = 65535
        else:
            change_modes = self._convert_value_and_pin_to_bits(value, pin)
        if change_modes is None:
            self.logger.error("Incorrect arguments in enable_digital_ouput()")
            return
        if pin is not None:
            # This means only a specific pin will be set
            current_modes = self.DigitalIO.outputEnableGet()
            if value:
                change_modes |= current_modes
            else:
                change_modes &= current_modes
        self.DigitalIO.outputEnableSet(change_modes)



    def write_digital(self, value, pin=None):
        """
        Write the output of one or all digital Output pins.
        To write to one specific pin: specify value (True, False, 0 or 1) and
        pin-number [0 - 16].
        To write all values at once, one can specify a list (of length 16), or
        specify the integer number where each bit represents a pin.

        Note: For a single pin it will enable Output mode if it was not set yet.
        When setting all pins it will only warn when some pins are changed but
        not set as Output.

        :param value: value of specific pin, or list of all pins, or "16 bit integer"
        :type value: int, or list
        :param pin: (optional) pin number [0 - 16]
        :type pin: int
        """
        change_ouput = self._convert_value_and_pin_to_bits(value, pin)
        if change_ouput is None:
            self.logger.error("Incorrect arguments in write_digital()")
            return
        current_modes = self.DigitalIO.outputEnableGet()
        current_values = self.DigitalIO.inputStatus()
        if pin is None:
            if (current_values ^ change_ouput) & ~current_modes:
                self.logger.warning('Some of the pins being changed are not set as output!')
            self.DigitalIO.outputSet(change_ouput)
            return
        else:
            if not ((1 << pin) & current_modes):
                self.logger.info("Setting pin {} as Output (it was set as Input)")
            self.enable_digital_ouput_mode(True, pin)
        if value:
            change_ouput |= current_modes
        else:
            change_ouput &= current_modes
        self.DigitalIO.outputSet(change_ouput)






class SimulatedDfwController:
    """
    Rudimentary simulated version of DfwController for the purpose of developing without a connected device.
    Note that it is far from a complete simulation, it just mimics a few basic methods.
    You can add any simulation function to relate read_analog() to a value set with write_analog() via _analog_simulation_functions.
    """
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self._analog_in_values = [0.0, 0.0]  # empty dictionary to hold simulated analog values
        # self._analog_simulation_functions = [lambda v: np.exp(v-0.7)/20, lambda v: np.random.normal(1,.5)]
        self._analog_simulation_functions = [lambda v: np.random.normal(1, .5), lambda v: np.exp(v - 0.7) / 20]
        self.basic_analog_return_std = False
        from collections import defaultdict

        class Dummy:
            """A dummy class that allows "Setting" and "Getting" arbitrary values and doesn't crash for unknown values."""
            def __init__(s2, *args, **kwargs):
                s2.__dict__.update(kwargs)
                s2.getset = defaultdict(lambda: 0)

            def __getattr__(s2, name):
                if 'Set' in name:
                    return lambda *args, **kwargs: s2.getset.__setitem__(tuple([name.strip('Set')])+args[:-1], args[-1])
                elif 'Get' in name:
                    return lambda *args, **kwargs: s2.getset[tuple([name.strip('Get')])+args]
                else:
                    return lambda *args, **kwargs: None

        self.AnalogIn = Dummy()
        self.AnalogIn.statusData = lambda ch, n: tuple(np.random.normal(size=n))
        self.AnalogOut = Dummy()
        self.AnalogOut.NODE = Dummy(CARRIER=0, FM=1, AM=2)
        self.AnalogOut.FUNC = Dummy(DC=0, SINE=1, SQUARE=2, TRIANGLE=3, RAMP_UP=4, RAMP_DOWN=5, NOISE=6, CUSTOM=30, PLAY=31)
        self.DigitalIn = Dummy()
        self.DigitalOut = Dummy()
        self.AnalogIO = Dummy()
        self.DigitalIO = Dummy()
        # create short name references
        self.ai = self.AnalogIn
        self.ao = self.AnalogOut
        self.di = self.DigitalIn
        self.do = self.DigitalOut

        self.logger.debug('SimulatedDfwController object created')

    def __getattr__(self, item):
        """This method is called when an undefined method is called"""
        if item != 'shape':
            self.logger.debug(f'method {item} is not implemented (in SimulatedDfwController)')

    # When running in PyCharm console, __len__ gets called and will result in the method above printing warnings.
    # Hence it's implemented here as an empty method
    def __len__(self):
        pass

    def read_analog(self):
        """
        Simulated version of read_analog().
        Applies functions specified in self._analog_simulation_functions (optionally to the values set by write_analog() ).
        """
        time.sleep(0.01)
        results = [func(v) for func, v in zip(self._analog_simulation_functions, self._analog_in_values)]
        if self.basic_analog_return_std:
            return tuple([*results, results[0]/10, results[1]/10])
        else:
            return tuple(results)

    def write_analog(self, volt, channel=-1):
        """
        Simulated version of write_analog().

        :param volt:
        :type volt:
        :param channel:
        :type channel:
        :return:
        :rtype:
        """
        if channel == 0 or channel == -1:
            self._analog_in_values[0] = volt
        if channel == 1 or channel == -1:
            self._analog_in_values[1] = volt

    def wait_for_ai_acquisition(self, start_timestamp=None):
        """
        Simulated version of wait_for_ai_acquisition().

        :param start_timestamp: is ignored in simulated version
        :type start_timestamp: float or None
        """
        time.sleep(0.1)

    def wait_for_stabilization(self):
        """Simulated version of wait_for_stabilization(). Waits for 0.1s."""
        time.sleep(0.1)

    def preset_basic_analog(self, n=80, freq=10000, range=50.0, return_std=False):
        """
        Simulated version of preset_basic_analog. Basically does nothing.

        :param n:     number of datapoints to collect and average (default 85)
        :type n:      int
        :param freq:  analog in frequency (default 10000)
        :type freq:   int or float or None
        :param range: the voltage range for the ADC (5.0 or 50.0) (default 50.0)
        :type range:  int or float or None
        :param return_std: also returns the standard deviations (default False)
        :type return_std:  bool
        """
        self.ai.frequencySet(freq)
        self.ai.channelRangeSet(-1, int(range))
        self.basic_analog_return_std = return_std

    def close(self):
        pass

    def power_supply(self, positive=None, negative=None, enable=True):
        """Dummy method for "simulated device". See DfwController for intended use."""
        self.logger.info("power_supply method is not implemented in SimulatedDfwController")

    def write_digital(self, value, pin=None):
        """Dummy method for "simulated device". See DfwController for intended use."""
        pass

    def read_digital(self, as_list=True):
        """Dummy method for "simulated device". See DfwController for intended use."""
        if as_list:
            return [0]*16
        else:
            return 0

    def set_IO_pin_mode(self, value, pin=None):
        """Dummy method for "simulated device". See DfwController for intended use."""
        pass

    def get_IO_pin_mode(self, as_list=True):
        """Dummy method for "simulated device". See DfwController for intended use."""
        if as_list:
            return [0] * 16
        else:
            return 0


def close_all():
    """Close all Digilent "WaveForms" devices"""
    dwf.FDwfDeviceCloseAll()


def enumerate_devices():
    """
    List connected devices and their possible configurations.
    Note: Use print_device_list() to easily display the result in readable form.

    :return: list of dictionaries containing information about the devices found
    :rtype: list
    """
    devices = []
    try:
        last_err_msg = dwf.FDwfGetLastErrorMsg()
        if last_err_msg:
            logging.getLogger(__name__).warning(last_err_msg)
        # enumerate devices
        devs = dwf.DwfEnumeration()
        ch = lambda n=0, b=0: {'ch': n, 'buf': b}

        for i, device in enumerate(devs):
            dev_dict = {'info': {}, 'configs': []}
            dev_dict['info']['SN'] = device.SN()
            dev_dict['info']['deviceName'] = device.deviceName()
            dev_dict['info']['userName'] = device.userName()
            dev_dict['dev'] = device

            if device.isOpened():
                logging.getLogger(__name__).warning(f"Can't connect to device {i} ({dev_dict['info']['SN']}), a connection is already open.\n"
                                                     "Note that the list was stored in "+__name__+".devices at the moment of import.")
                dev_dict['configs'] = "Couldn't connect to device for further information"
            else:
                dwf_ai = dwf.DwfAnalogIn(device)
                channel = dwf_ai.channelCount()
                _, hzFreq = dwf_ai.frequencyInfo()
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
                dwf_ai.close()
            devices.append(dev_dict)
    except:
        from sys import exc_info
        logging.getLogger(__name__).warning("Exception occured while enumerating devices:\n", exc_info()[0])
    return devices


# Run enumerate_devices() once when loading the module to make the list available afterwards
devices = enumerate_devices()


def print_device_list(devices_list=None):
    """
    Prints the information in the list generated by enumerate_devices() in a readable form.
    If no argument is given it prints the list stored at time of importing the module.

    :param devices: the list generated by enumerate_devices() (or None (default) to print the list stored at import)
    :type devices: list
    """
    incomplete = False
    if devices_list is None:
        global devices
        devices_list = list(devices)
        incomplete = None
    for i, device in enumerate(devices_list):
        print("------------------------------")
        print("Device " + str(i) + " : ")
        print("\tdeviceName:\t" + device['info']['deviceName'])
        print("\tuserName:\t" + device['info']['userName'])
        print("\tSN:\t\t\t" + device['info']['SN'])
        if 'maxAIfreq' in device['info']:
            print("\tmaxAIfreq:\t" + str(device['info']['maxAIfreq']))
        if type(device['configs']) is str:
            print('\t'+device['configs'])
            if incomplete is not None:
                incomplete = True
        else:
            print('\tConfig AnalogIN   AnalogOUT  DigitalIN   DigitalOUT')
            for iCfg, conf in enumerate(device['configs']):
                print('\t{}      {} x {:<5}  {} x {:<5}  {:2} x {:<5}  {:2} x {:<5}'.format(
                    iCfg, conf['ai']['ch'], conf['ai']['buf'],
                          conf['ao']['ch'], conf['ao']['buf'],
                          conf['di']['ch'], conf['di']['buf'],
                          conf['do']['ch'], conf['do']['buf']))
    if incomplete:
        print("\nThe device list appears to be incomplete. "
              "Try "+__name__+".devices_list() without argument to print the list stored at time of import")


if __name__ == '__main__':

    import labphew  # import this to use labphew style logging (by importing it before matplotlib it also prevents matplotlib from printing many debugs)
    import matplotlib.pyplot as plt

    # Display a list of devices and their possible configurations
    devs = enumerate_devices()
    print_device_list(devs)

    # Create object for device number 0, with config number 0
    daq = DfwController(0, 0)

    # # Use the following line instead of the previous line for testing the simulated device
    # daq = SimulatedDfwController(0, 0)

    print("\nTo be able to read signals we're about to generate: connect W1 to 1+, W2 to 2+, and 1- and 2- to ground (down arrow)")

    # Example showing basic analog methods:

    # Apply settings for using basic analog methods.
    # Note that this is already automatically done at instantiation of the object so technically not required at this moment.
    # But if you've those changed settings (like we'll do in the advanced example below) it is necessary.
    daq.preset_basic_analog()

    t0 = time.time()
    for k in range(10):
        print(daq.read_analog())
    duration = time.time()-t0
    print(duration)

    daq.write_analog( 1.3, 0)  #  1.3V on analog out channel 0
    daq.write_analog(-0.7, 1)  # -0.7V on analog out channel 1

    daq.wait_for_stabilization()

    in0, in1 = daq.read_analog()
    print(f'\nAnalog in, channel 0 is {in0:.3f} V and channel 1 is {in1:.3f} V')

    # Note: The device reads both channels simultaneously.
    # If you only need one you can select it immediately with standard python:
    read_value = daq.read_analog()[0]


    # Example illustrating the use of (advanced) inherited methods:

    print("\nConfigure analog out channel 0")
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

    print("\nStarting output and starting acquisition")
    daq.ao.configure(ch_out, 1)
    daq.ai.configure(True, 1)
    daq.wait_for_ai_acquisition()

    print("   reading data")
    scope = daq.ai.statusData(0, n_points)

    dc = sum(scope) / len(scope)
    print("DC: " + str(dc) + "V")

    t = np.arange(daq.ai.bufferSizeGet()) / daq.ai.frequencyGet()
    plt.plot(t, scope)
    plt.show()
    plt.xlabel("time (s)")
    plt.ylabel("analog in channel 0 (V)")

    # to close the device:
    # daq.close()

    # or to close all devices:
    # close_all()

