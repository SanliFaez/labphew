# coding=utf-8
"""
Analog Discovery 2
==================

minimal:    It should have getting and setting voltages

optional:   setting output as function generator


"""
import os.path
import numpy as np
import yaml
from time import time, sleep, localtime, strftime
import logging

class Operator:
    """
    A primitive class generating a synthetic time series.
    the main purpose of this class it to provide the minimal functions required for running a view
    and can serve as the basis for a customized model
    """

    def __init__(self, instrument, properties = {}):
        self.logger = logging.getLogger(__name__)
        self.properties = properties
        self.instrument = instrument

        self._stop_monitor = True  # used externally to control monitor
        self._new_monitor_data = False  # used to flag gui that new data is available
        self._monitor_start_time = 0

        self.monitoring = False  # flag controlled by operator to indicate if busy
        self.stop = True  # flag controlled externally (e.g. by View) to control monitor loop
        self.new_data = False  # flag controlled by operator to signal there's new data that could be displayed


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



    def analog_out(self, channel, value=None):
        """
        Set analog_out.
        Forces value to be in allowed range.
        Returns the (corrected) value.

        :param channel: channel 1 or 2
        :type channel: int
        :param value: voltage to set (in Volt)
        :type value: float
        :return: the value set to the channel
        :rtype: float
        """
        if channel not in [1,2]:
            self.logger.error('incorrect channel number')
            return
        upr = self.properties['ao'][channel]['upper_limit']
        lwr = self.properties['ao'][channel]['lower_limit']
        if value > upr:
            self.logger.info(f'{value} exceeds ch{channel} limit, clipping to {upr}')
            value = upr
        elif value < lwr:
            self.logger.info(f'{value} exceeds ch{channel} limit, clipping to {lwr}')
            value = lwr
        self.instrument.write_analog(value, channel-1)
        return value

    def _set_monitor_time_step(self, time_step):
        """
        Set Monitor time step.
        Forces the value to be at least 0.01, and warns for large values

        :param time_step: time step between acquisitions in the monitor loop (seconds)
        :type time_step: float
        """
        if time_step < 0.01:
            time_step = 0.01
            self.logger.warning(f"time_step too small, setting: {time_step}s")
        elif time_step> 2:
            self.logger.warning(f"setting time_step to {time_step}s (are you sure?)")
        self.properties['monitor']['time_step'] = time_step

    def _set_monitor_plot_points(self, plot_points):
        """
        Set number of plot points for Monitor.
        Forces the value to be at least 2, and warns for large values.

        :param plot_points: time step between acquisitions in the monitor loop (seconds)
        :type plot_points: int
        """
        if plot_points < 2:
            plot_points = 2
            self.logger.warning(f"points too low, setting: {plot_points}s")
        elif plot_points > 200:
            self.logger.warning(f"setting plot_points to {plot_points}s (are you sure?)")
        self.properties['monitor']['plot_points'] = plot_points

    def _monitor_loop(self):
        """
        Calles by GUI Monitor to start the monirot loop.
        Not intended to be called from Operator. (Which should be blocked)
        """
        if self._stop_monitor:
            self.logger.warning('Monitor should only be run from GUI')
            return
        # Preparations before running the monitor
        self.analog_monitor_1 = np.zeros(self.properties['monitor']['plot_points'])
        self.analog_monitor_2 = np.zeros(self.properties['monitor']['plot_points'])
        # self.analog_monitor_time = np.zeros(self.properties['monitor']['plot_points'])
        self.analog_monitor_time = np.arange(1-self.properties['monitor']['plot_points'], 1)*self.properties['monitor']['time_step']

        self._monitor_start_time = time()
        next_time = 0
        while not self._stop_monitor:
            timestamp = time() - self._monitor_start_time
            analog_in = self.instrument.read_analog()  # read the two analog in channels
            # To keep the length constant, roll/shift the buffers and add the new datapoints
            self.analog_monitor_1 = np.roll(self.analog_monitor_1, -1)
            self.analog_monitor_2 = np.roll(self.analog_monitor_2, -1)
            self.analog_monitor_time = np.roll(self.analog_monitor_time, -1)
            self.analog_monitor_1[-1] = analog_in[0]
            self.analog_monitor_2[-1] = analog_in[1]
            self.analog_monitor_time[-1] = timestamp
            self._new_monitor_data = True
            # in stead of sleep,
            next_time += self.properties['monitor']['time_step']
            while time()-self._monitor_start_time<next_time:
                pass


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
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analog_discovery_2_config.yml')
        with open(filename, 'r') as f:
            self.properties.update(yaml.safe_load(f))

        self.properties['config_file'] = filename


    # def load_instrument(self, inst=None):
    #     """
    #     Loads an instrument that is necessary for performing the scan.
    #     :param inst: it can be a model already initailized. If not provided, loads the default instrument.
    #     """
    #     if inst is None:
    #         pass #TODO: put here commands for initializing a primitive controller like blink_controller
    #     else:
    #         self.instrument = inst

    # def save_scan_data(self, fname):
    #     """
    #     TODO: make proper save function
    #     :param fname:
    #     :return:
    #     """
    #     pass



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)  # Change root logging level

    # from labphew.controller.digilent.waveforms import DfwController

    # To import the actual device:
    # from labphew.controller.digilent.waveforms import DfwController

    # To import a simulated device:
    from labphew.controller.digilent.waveforms import SimulatedDfwController as DfwController

    instrument = DfwController()

    opr = Operator(instrument)
    opr.load_config()

    #e.load_instrument()
    # x, data = e.do_scan()
    #d = e.main_loop()
    # print(data)
