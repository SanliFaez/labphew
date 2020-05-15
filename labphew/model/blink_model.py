# coding=utf-8
"""
labphew basic blink application
================

blink.py contains a very simple operator for communicating with an arduino.
It also serves as an example for the minimal structure of an Operator class in labphew.

TODO
- make stripped version for _blank_model.py

"""
import os
import numpy as np
import yaml
from time import time, sleep

from labphew import Q_
import labphew

import logging

class Operator:
    """Class for performing a measurement of an I-V curve of a light emitting photodiode (LED).
    """

    def __init__(self, daq):
        self.logger = logging.getLogger(__name__)
        self.daq = daq
        self.properties = {}
        self.blink_state = 0
        self.blinking = False
        self.t0 = time()

        self.running_scan = False

    def read_analog(self, port: int):
        """Re-implements the function as provided by the model.

        :param int port: Port to read
        :return Quantity: The value read by the device model.
        """
        value = self.daq.get_analog_value(port)
        return value

    def do_scan(self):
        """Does a scan of an analog output while recording an analog input. It doesn't take any arguments,
        it relies on having the proper properties set in the dictionary properties['Scan']
        """
        if self.running_scan:
            raise Warning('Trying to start a second scan')

        self.logger.info('Starting IV scan')
        start = Q_(self.properties['Scan']['start'])
        stop = Q_(self.properties['Scan']['stop'])
        step = Q_(self.properties['Scan']['step'])
        channel_in = self.properties['Scan']['channel_in']
        channel_out = self.properties['Scan']['channel_out']
        delay = Q_(self.properties['Scan']['delay'])
        units = start.u
        self.logger.debug(f'Units for scan are: {units}')
        stop = stop.to(units)
        num_points = (stop - start) / step
        num_points = round(num_points.m_as('')) + 1
        scan = np.linspace(start, stop, num_points)
        self.xdata_scan = scan
        self.ydata_scan = np.zeros(num_points) * units
        i = 0
        self.running_scan = True
        self.stop_scan = False
        for value in scan:
            if self.stop_scan:
                break
            self.daq.set_analog_value(int(channel_out), value)
            sleep(delay.m_as('s'))
            self.ydata_scan[i] = self.daq.get_analog_value(int(channel_in))
            i += 1
        self.running_scan = False

    def monitor_signal(self):
        """Monitors a signal in a specific port. Doesn't take any parameters, it assumes there is
        well-configured dictionary called self.properties['Monitor']
        """
        delay = Q_(self.properties['Monitor']['time_resolution'])
        total_time = Q_(self.properties['Monitor']['total_time']).m_as('s')
        self.xdata = np.zeros((round(total_time / delay.m_as('s'))))
        self.delta_x = delay.m_as('s')
        self.ydata = np.zeros(int(total_time / delay.m_as('s')))
        self.t0 = time()
        while not self.stop_monitor:
            self.ydata = np.roll(self.ydata, -1)
            self.ydata[-1] = self.read_analog(1).m_as('V')
            self.xdata = np.roll(self.xdata, -1)
            self.xdata[-1] = time() - self.t0  # self.xdata[-2] + self.delta_x
            sleep(delay.m_as('s'))

    def load_config(self, filename=None):
        """Loads the configuration file to generate the properties of the Scan and Monitor.

        :param str filename: Path to the filename. Defaults to Model/default/blink.yml if not specified.
        """
        if filename is None:
            filename = 'Model/default/blink.yml'

        with open(filename, 'r') as f:
            params = yaml.load(f, Loader=yaml.FullLoader)

        self.properties = params
        self.properties['config_file'] = filename
        self.properties['User'] = self.properties['User']['name']

    def load_daq(self, daq_model=None):
        """
        Loads a DAQ Model already initialized or loads from yaml specifications. The DAQ that can
        be provided through the YAML are 'DummyDaq' and 'RealDaq'. There are no limitations regarding
        an already initialized DAQ provided that follows the Daq Model.

        :param daq_model: it can be a model already initailized. If not provided, loads the default.
        """
        if daq_model is None:
            if 'DAQ' in self.properties:
                name = self.properties['DAQ']['name']
                port = self.properties['DAQ']['port']
                if name == 'DummyDaq':
                    from labphew.Model.daq import DummyDaq
                    self.daq = DummyDaq(port)

                elif name == 'RealDaq':
                    from labphew.Model.daq.analog_daq import AnalogDaq
                    self.daq = AnalogDaq(port)

                elif name == 'VisaDaq':
                    from labphew.Model.daq.visa_daq import AnalogDaq
                    self.daq = AnalogDaq(port)
                else:
                    filename = self.properties['config_file']
                    raise Exception('The daq specified in {} does not exist in this program'.format(filename))
            else:
                filename = self.properties['config_file']
                raise Exception("No DAQ specified in {}".format(filename))
        else:
            self.daq = daq_model



if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)  # Change base logging level
    labphew.simulate_hardware = True

    if labphew.simulate_hardware:
        from labphew.controller.arduino.simple_daq import SimulatedSimpleDaq as SimpleDaq
    else:
        from labphew.controller.arduino.simple_daq import SimpleDaq

    daq = SimpleDaq()
    op = Operator(daq)

    # In this case we manually set the properties, but those can also be loaded from a yml file with op.load_config()
    op.properties = {'Scan': {'start': '0V', 'stop': '5V', 'step': '0.2V', 'channel_out': 0, 'channel_in': 1, 'delay': '0.1s'}}

    print('test reading channel 1: ', op.read_analog(1))
    op.do_scan()

    import matplotlib.pyplot as plt
    # Unwanted side effect of changing baselogger level to DEBUG is that matplotlib is now also printing debugs
    # Trying to modify that with command below, but it's not working yet
    plt.set_loglevel('warning')
    plt.plot(op.xdata_scan.magnitude, op.ydata_scan.magnitude)
    plt.show()

