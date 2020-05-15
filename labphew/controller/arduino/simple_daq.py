"""
Simple DAQ Controller
=====================

Python For The Lab revolves around controlling a simple DAQ device built on top of an Arduino.
The DAQ device is capable of generating up to two analog outputs in the range 0-3.3V and to acquire
several analog inputs.

Because of the pedagogy of the course Python for the Lab, it was assumed that the device can generate
value by value and not a sequence. This forces the developer to think on how to implement a solution
purely on Python.
"""

import labphew
import serial
from time import sleep, time
import logging

from labphew import Q_
from labphew import ureg#.V as Volt

class SimpleDaq():
    """ Controller for the serial devices that ships with Python for the Lab.
    """
    DEFAULTS = {'write_termination': '\n',
                'read_termination': '\n',
                'encoding': 'ascii',
                'baudrate': 9600,
                'write_timeout': 1,
                'read_timeout': 1,
                }
    """Dictionary storing the defaults to communicate through the serial port.
    """
    rsc = None
    """Resource. It is the actual library providing low level communication. """

    def __init__(self, port):
        """ Automatically initializes the communication with the device.
        """
        self.initialize(port)

    def initialize(self, port):
        """ Opens the serial port with the DEFAULTS.
        """
        self.rsc = serial.Serial(port=port,
                                 baudrate=self.DEFAULTS['baudrate'],
                                 timeout=self.DEFAULTS['read_timeout'],
                                 write_timeout=self.DEFAULTS['write_timeout'])
        sleep(0.5)

    def idn(self):
        """Identify the device.
        """
        return self.query("IDN")

    def get_analog_value(self, channel):
        """Gets the value from an analog port.

        :param int port: Port number to read.
        :return int: The value read.
        """
        query_string = 'IN:CH{}'.format(channel)
        value = int(self.query(query_string))
        return value
        # shouldn't this be: # return value * 3.3 / 4095 * Volt

    def set_analog_value(self, channel, value):
        """ Sets a voltage to an output port.

        :param int port: Port number. Range depends on device
        :param Quantity value: The output value in Volts.
        """
        value = int(value.m_as('V')/3.3*4095)
        write_string = 'OUT:CH{}:{}'.format(channel, value)
        self.write(write_string)

    def finalize(self):
        """ Closes the communication with the device.
        """
        if self.rsc is not None:
            self.rsc.close()

    def query(self, message):
        """Sends a message to the devices an reads the output.

        :param str message: Message sent to the device. It should generate an output, or it will timeout waiting to read from it.
        :return str: The message read from the device
        """
        self.write(message)
        return self.read()

    def write(self, message):
        """ Writes a message to the device using the DEFAULT end of line and encoding.

        :param str message: The message to send to the device
        """
        if self.rsc is None:
            raise Warning("Trying to write to device before initializing")

        msg = (message + self.DEFAULTS['write_termination']).encode(self.DEFAULTS['encoding'])
        self.rsc.write(msg)
        sleep(0.1)

    def read(self):
        """ Reads from the device using the DEFAUTLS end of line and encoding.

        :return str: The message received from the device.
        """
        line = "".encode(self.DEFAULTS['encoding'])
        read_termination = self.DEFAULTS['read_termination'].encode(self.DEFAULTS['encoding'])

        t0 = time()
        new_char = "".encode(self.DEFAULTS['encoding'])
        while new_char != read_termination:
            new_char = self.rsc.read(size=1)
            line += new_char
            if time()-t0 > self.DEFAULTS['read_timeout']:
                raise Exception("Readout time reached when reading from the device")

        return line.decode(self.DEFAULTS['encoding'])


import math

class SimulatedSimpleDaq:
    """ Simulated version of the SimpleDaq class to use for testing.
        It mimics getting and setting analog values.
        Set channel 0 is "linked" to get channel 1
        Set channel 2 is "linked" to get channel 3
        Get channel 4 returns a sine
    """

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self._analog_values = {}  # empty dictionary to hold simulated analog values
        self._translate_set_to_get = {0: 1, 2: 3}  # specify to which "get channel" a "set channel" is linked
        self.logger.debug('SimulatedSimpleDaq object created')

    def __getattr__(self, item):
        """This method is called when an undefined method is called"""
        self.logger.warning(f'method {item} is not implemented in SimulatedSimpleDaq')

    # When running in PyCharm console, __len__ gets called and will result in the method above printing warnings.
    # Hence it's implemented here as an empty method
    def __len__(self):
        pass

    def idn(self):
        return 'Simulated Simple DAQ'

    def __simulate_iv_relation(self, set_value, get_channel):
        """Converts an input value to an output value as if it were an IV curve,and stores it in the internal memory"""
        self._analog_values[get_channel] = math.exp(set_value - 0.7)/20

    def get_analog_value(self, channel):
        # If channel is not specified yet, initialize it to 0
        if channel not in self._analog_values:
            self._analog_values[channel] = 0
        if channel == 4:
            self._analog_values[channel] += 0.2
            return math.sin(self._analog_values[channel]) * Q_('V')
        return self._analog_values[channel] * Q_('V')

    def set_analog_value(self, channel, value):
        if channel in self._translate_set_to_get:
            get_channel = self._translate_set_to_get[channel]
        else:
            get_channel = channel
        # print(value, type(value))
        # print(value.m_as('volt'))
        self.__simulate_iv_relation(value.m_as('V'), get_channel)

    def finalize(self):
        pass


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)  # Change logging level

    labphew.simulate_hardware = True  # change this to False for testing an actual device attached to computer

    if labphew.simulate_hardware:
        d = SimulatedSimpleDaq('/dev/ttyACM0')
    else:
        d = SimpleDaq('/dev/ttyACM0')

    print('Identification of device: ', d.idn())
    print('\nMeasuring IV curve:\nset get')
    for i in range(12):
        set_voltage = i * 0.3 * ureg.V
        d.set_analog_value(0, set_voltage)
        get_voltage = d.get_analog_value(1)
        print(set_voltage, ' -> ', get_voltage)

    print('\nChannel 4:')
    for i in range(30):
        print(d.get_analog_value(4))

    d.finalize()

