# coding=utf-8
"""
labphew basic blank application
================

blink_model.py contains the skeleton of a model that can be called by the default labphew windows:
- MonitorWindow: GUI and interactions for monitoring operations that run continuously
- Config_Window: Interface for updating the measurement parameters or loading/saving them from/into a config file
- Scan_Window: GUI and update inquiries for one-time operations that can be called from another window or the command line

TODO

"""
import os
import numpy as np
import yaml
from time import time, sleep, localtime, strftime

class Operator:
    """
    A primitive class generating a synthetic time series.
    the main purpose of this class it to provide the minimal functions required for running a view
    and can serve as the basis for a customized model
    """

    def __init__(self):
        self.instrument = None
        self.properties = {}  # TODO: read properties from yml config file
        self.indicator = 0  # instrument-specific value shared with another display during the scan
        self.blinking = False  # signalling scan in progress or instrument is engaged
        self.paused = False  # signalling scan in progress or instrument is engaged
        self.done = False  # signal for the end of a complete scan
        self.t0 = time()
        self.tloop = time()

    def main_loop(self):
        """
        primitive function that is called in the MonitorWindow in blank_model,
        this function just tells the time
        """
        if not self.paused:
            self.blinking = True
            t = time()
            self.tloop = t
            output = strftime("%H:%M:%S", localtime(t))
            sleep(0.03)

        return output

    def pause(self):
        """
        primitive function to pause the main loop or readout
        """
        self.paused = True
        self.blinking = False

    def resume(self):
        """
        primitive function to pause the main loop or readout
        """
        self.paused = False

    def shut_down(self):
        """
        primitive function that is called in the MonitorWindow to safely close the application
        """
        print("bye bye!")

    def do_scan(self, param=None):
        """
        primitive function for calling by the ScanWindow
        this functions counts down inverses down to 1/10
        """
        if self.blinking:
            raise Warning('Trying to start simultaneous operations')
        self.done = False
        if param == None:
            start, stop, step = 1, 10, 1
        else:
            pass
            # example of filling in variables from loaded class properties
            #start = self.properties['Scan']['start']
            #stop = self.properties['Scan']['stop']
            #step = self.properties['Scan']['step']

        num_points = np.int((stop-start+1)/step)
        scan = np.linspace(start, stop, num_points)
        output = 0 * scan
        self.blinking = True

        ### here comes the main actions of the scan
        for i in range(np.size(scan)):
            self.indicator = scan[i]
            output[i] = 1/scan[i]

        self.blinking = False
        self.scan_finished()
        return scan, output

    def scan_finished(self):
        """
        Here, you can put any signal that has to be returned to the parent program that has called the scan
        """
        self.done = True

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



if __name__ == "__main__":
    e = Operator()
    #e.load_config()
    #e.load_instrument()
    x, data = e.do_scan()
    #d = e.main_loop()
    print(data)
