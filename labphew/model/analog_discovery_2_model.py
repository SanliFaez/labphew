# coding=utf-8
"""
Analog Discovery 2
==================


minimal:    It should have getting and setting voltages

optional:   setting output as function generator




"""
import os
import numpy as np
import yaml
from time import time, sleep, localtime, strftime

# To import the actual device:
from labphew.controller.digilent.waveforms import SimulatedDfwController as DfwController
# To import a simulated device:
# from labphew.controller.digilent.waveforms import DfwController

class Operator:
    """
    A primitive class generating a synthetic time series.
    the main purpose of this class it to provide the minimal functions required for running a view
    and can serve as the basis for a customized model
    """

    def __init__(self):
        self.instrument = DfwController()



        # initialize data buffers
        self.text_buffers = []
        self.plot_buffers = [np.array([0]), np.array([0])]
        self.image_buffers = []
        self.text_buffers_updated = False
        self.plot_buffers_updated = False
        self.image_buffers_updated = False

        self.monitor_plot_points = 100

        # self.properties = {}  # TODO: read properties from yml config file
        # self.indicator = 0  # instrument-specific value shared with another display during the scan
        # self.blinking = False  # signalling scan in progress or instrument is engaged
        # self.paused = False  # signalling scan in progress or instrument is engaged
        # self.done = False  # signal for the end of a complete scan
        # self.t0 = time()
        # self.tloop = time()
        # self.scan=[]
        # self.output=[]
        #
        # self.monitor_running = False

    # def empty_data_buffers(self):
    #     self.text_buffers = []
    #     self.plot_buffers = []
    #     self.image_buffers = []
    #     self.text_buffers_updated = False
    #     self.plot_buffers_updated = False
    #     self.image_buffers_updated = False
    #
    # def initialize_monitor(self):
    #     self.empty_data_buffers()
    #     self.plot_buffers = [{np.zeros(self.monitor_plot_points), np.zeros(self.monitor_plot_points)]
    #     self.plotting_active = True
    #
    # def update_monitor(self):
    #     for plot_buffer in self.plot_buffers:

    def initialize_monitor(self):
        """Preparations before running the monitor"""
        # For both AI channels, initialize an array filled with zeros to act as a buffer, of size self.monitor_plot_points
        self.analog_monitor_0 = np.zeros(self.monitor_plot_points)
        self.analog_monitor_1 = np.zeros(self.monitor_plot_points)

    def main_loop(self):
        analog_in = self.instrument.read_analog()  # read the two analog in channels
        # To keep the length constant, roll/shift the buffers and add the new datapoints
        self.analog_monitor_0 = np.roll(self.analog_monitor_0, -1)
        self.analog_monitor_1 = np.roll(self.analog_monitor_1, -1)
        self.analog_monitor_0[-1] = analog_in[0]
        self.analog_monitor_1[-1] = analog_in[1]
        # For now monitor_view.update_monitor() expects a single xdata array and single ydata array.
        # If xdata array is None, monitor_view.update_monitor() will generate time axis
        # At the moment it's not possible to pass the second channel
        return None, self.analog_monitor_0



    # def main_loop(self):
    #     """
    #     primitive function that is called in the MonitorWindow in blank_model,
    #     this function just tells the time
    #     """
    #     if not self.paused:
    #         self.blinking = True
    #         t = time()
    #         self.tloop = t
    #         output = strftime("%H:%M:%S", localtime(t))
    #         sleep(0.03)
    #
    #     return output

    # def pause(self):
    #     """
    #     primitive function to pause the main loop or readout
    #     """
    #     self.paused = True
    #     self.blinking = False

    # def resume(self):
    #     """
    #     primitive function to pause the main loop or readout
    #     """
    #     self.paused = False

    # def shut_down(self):
    #     """
    #     primitive function that is called in the MonitorWindow to safely close the application
    #     """
    #     print("bye bye!")

    # def do_scan(self, param=None):
    #     """
    #     primitive function for calling by the ScanWindow
    #     this functions counts down inverses down to 1/10
    #     """
    #     if self.blinking:
    #         raise Warning('Trying to start simultaneous operations')
    #     self.done = False
    #     if param == None:
    #         start, stop, step = 1, 100, 1
    #     else:
    #         pass
    #         # example of filling in variables from loaded class properties
    #         #start = self.properties['Scan']['start']
    #         #stop = self.properties['Scan']['stop']
    #         #step = self.properties['Scan']['step']
    #
    #     num_points = np.int((stop-start+1)/step)
    #     scan = np.linspace(start, stop, num_points)
    #     output = 0 * scan
    #     self.blinking = True
    #
    #     ### here comes the main actions of the scan
    #     for i in range(np.size(scan)):
    #         if not self.paused:
    #             self.indicator = scan[i]
    #             output[i] = 1/scan[i]
    #
    #     self.blinking = False
    #     if not self.paused:
    #         self.scan_finished()
    #
    #     self.scan = scan
    #     self.output = output
    #
    #     return scan, output

    # def scan_finished(self):
    #     """
    #     Here, you can put any signal that has to be returned to the parent program that has called the scan
    #     """
    #     self.done = True

    def load_config(self, filename=None):
        """
        If specified, this function loads the configuration file to generate the properties of the Scan.

        :param str filename: Path to the filename. Defaults to Model/default/blink.yml if not specified.
        """
        if filename is None:
            filename = '../core/defaults/blink.yml'

        with open(filename, 'r') as f:
            params = yaml.safe_load(f)

        self.properties = params
        self.properties['config_file'] = filename
        self.properties['User'] = self.properties['User']['name']

    def load_instrument(self, inst=None):
        """
        Loads an instrument that is necessary for performing the scan.
        :param inst: it can be a model already initailized. If not provided, loads the default instrument.
        """
        if inst is None:
            pass #TODO: put here commands for initializing a primitive controller like blink_controller
        else:
            self.instrument = inst

    # def save_scan_data(self, fname):
    #     """
    #     TODO: make proper save function
    #     :param fname:
    #     :return:
    #     """
    #     pass



if __name__ == "__main__":
    e = Operator()
    e.load_config()
    #e.load_instrument()
    x, data = e.do_scan()
    #d = e.main_loop()
    print(data)
