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
    Example Operator class for Digilent Analog Discovery 2.
    """

    def __init__(self, instrument, properties = {}):
        self.logger = logging.getLogger(__name__)
        self.properties = properties
        self.instrument = instrument

        # Flag controlled by operator:
        self._busy = False  # indicates the operator is busy (e.g. with scan or monitor)
        self._new_scan_data = False  # signal there's new data that could be displayed (a gui would reset this to False after retrieving the data)
        self._new_monitor_data = False  # used to flag gui that new data is available


        # Flags controlled by external gui to control flow of loops (e.g. scan or monitor)
        self._stop = False  # signal a loop to stop (whenever operator is not busy it should be False)
        self._pause = False  # signal a loop to pause (whenever operator is not busy it should be False)
        self._allow_monitor = False  # monitor should not be run from command line, a gui can set this to True


        self._monitor_start_time = 0




        self.monitor_plot_points = 100

        self.analog_in = self.instrument.read_analog  # create direct alias for this method of the instrument

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



    def analog_out(self, channel, value=None, verify_only=False):
        """
        Set analog_out.
        Forces value to be in allowed range.
        Applies the value to the output channel.
        Returns the (corrected) value.
        Note: if verify_only is set True it does not apply the value, but only return the corrected value

        :param channel: channel 1 or 2
        :type channel: int
        :param value: voltage to set (in Volt)
        :type value: float
        :param verify_only: if True it does not apply the value to the channel (default: False)
        :type verify_only: bool
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
        if not verify_only:
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

    def _verify_scan_channels(self):
        """
        Checks if channels in properties are valid and returns analog out and analog in channel.
        Note that None is returned if an error is found

        :return:  analog out and analog in channel of scan
        :rtype: (int, int)
        """
        if 'scan' not in self.properties:
            self.logger.error("'scan' not found in properties")
            return
        if 'ao_channel' not in self.properties['scan'] or self.properties['scan']['ao_channel'] not in [1,2]:
            self.logger.error("'ao_channel' not found in properties or invalid value (should be 1 or 2)")
            return
        if 'ai_channel' not in self.properties['scan'] or self.properties['scan']['ai_channel'] not in [1,2]:
            self.logger.error("'ai_channel' not found in properties or invalid value (should be 1 or 2)")
            return
        return self.properties['scan']['ao_channel'], self.properties['scan']['ai_channel']

    def _set_scan_start(self, value):
        """
        Set scan start value.
        Forces value to be in valid range and updates properties dictionary.
        Also corrects the sign of step if required.

        :param value: start value of scan (V)
        :type value: float
        """
        ao_ch, _ = self._verify_scan_channels()
        if ao_ch is None:  # if _verify_scan_channels() returns nothing that means channel is invalid or not found
            return
        value = self.analog_out(ao_ch, value, verify_only=True)
        self.properties['scan']['start'] = value
        self._set_scan_step()

    def _set_scan_stop(self, value):
        """
        Set scan stop value.
        Forces value to be in valid range and updates properties dictionary.

        :param value: stop value of scan (V)
        :type value: float
        """
        ao_ch, _ = self._verify_scan_channels()
        if ao_ch is None:  # if _verify_scan_channels() returns nothing that means channel is invalid or not found
            return
        value = self.analog_out(ao_ch, value, verify_only=True)
        self.properties['scan']['stop'] = value
        self._set_scan_step()

    def _set_scan_step(self, step=None):
        """
        Set scan step value.
        If no step value is supplied it only corrects the sign of step.

        :param step:
        :type step:
        :return:
        :rtype:
        """
        if step == 0:
            self.logger.warning('stepsize of 0 is not possible')
            return
        if step is not None:
            self.properties['scan']['step'] = step
        if np.sign(self.properties['scan']['step']) != np.sign(self.properties['scan']['stop'] - self.properties['scan']['start']):
            self.properties['scan']['step'] *= -1

    def _monitor_loop(self):
        """
        Called by GUI Monitor to start the monirot loop.
        Not intended to be called from Operator. (Which should be blocked)
        """
        # First check if monitor is allowed to start
        if self._busy or not self._allow_monitor:
            self.logger.warning('Monitor should only be run from GUI and not while Operator is busy')
            return

        try:
            # Preparations before running the monitor
            self.analog_monitor_1 = np.zeros(self.properties['monitor']['plot_points'])
            self.analog_monitor_2 = np.zeros(self.properties['monitor']['plot_points'])
            # self.analog_monitor_time = np.zeros(self.properties['monitor']['plot_points'])
            self.analog_monitor_time = np.arange(1-self.properties['monitor']['plot_points'], 1)*self.properties['monitor']['time_step']
        except:
            self.logger.error("'plot_points' or 'time_step' missing or invalid in config")
            return

        self._busy = True  # set flag to indicate operator is busy

        self._monitor_start_time = time()
        next_time = 0
        while not self._stop:
            while self._pause:
                sleep(0.05)
                if self._stop: break
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
        self._stop = False  # reset stop flag to false
        self._busy = False  # indicate the operator is not busy anymore


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


    def do_scan(self, param=None):
        """
        primitive function for calling by the ScanWindow
        this functions counts down inverses down to 1/10
        """
        # Start with various checks and warn+return if somthing is wrong
        if self._busy:
            self.logger.warning('Scan should not be started while Operator is busy.')
            return
        if 'scan' not in self.properties:
            self.logger.error("The config file or properties dict should contain 'scan' section.")
            return
        required_keys = ['start', 'stop', 'step', 'ao_channel', 'ai_channel']
        if not all(key in self.properties['scan'] for key in required_keys):
            self.logger.error("'scan' should contain: "+', '.join(required_keys))
            return
        try:
            start = self.properties['scan']['start']
            stop = self.properties['scan']['stop']
            step = self.properties['scan']['step']
            ch_ao = int(self.properties['scan']['ao_channel'])
            ch_ai = int(self.properties['scan']['ai_channel'])
        except:
            self.logger.warning("Error occured while reading scan config values")
            return
        if ch_ai not in [1,2] or ch_ao not in [1,2]:
            self.logger.warning("AI and AO channel need to be 1 or 2")
            return
        if 'stabilize_time' in self.properties['scan']:
            stabilize = self.properties['scan']['stabilize_time']
        else:
            self.logger.info("stabilize_time not found in config, using 0s")
            stabilize = 0

        num_points = np.int(round((stop-start+1)/step))  # use round to catch the occasional rounding error
        self.scan_voltages = np.linspace(start, stop, num_points)

        self.measured_voltages = 0 * self.scan_voltages

        self._busy = True  # indicate that operator is busy

        for i, voltage in enumerate(self.scan_voltages):
            if self._pause:
                while self._pause:
                    sleep(0.05)
                    if self._stop: break
            self.logger.debug('applying {} to ch {}'.format(voltage, ch_ao))
            self.analog_out(ch_ao, voltage)
            sleep(stabilize)
            measured = self.analog_in()[ch_ai - 1]
            self.measured_voltages[i] = measured
            self._new_scan_data = True
            if self._stop:
                break

        self._stop = False  # reset stop flag to false
        self._busy = False  # indicate operator is not busy anymore

        return self.scan_voltages, self.measured_voltages


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
    import labphew  # import this to use labphew style logging (by importing it before matplotlib it also prevents matplotlib from printing many debugs)
    import matplotlib.pyplot as plt

    # from labphew.controller.digilent.waveforms import DfwController

    # To import the actual device:
    from labphew.controller.digilent.waveforms import DfwController

    # To import a simulated device:
    # from labphew.controller.digilent.waveforms import SimulatedDfwController as DfwController

    instrument = DfwController()

    opr = Operator(instrument)
    opr.load_config()

    #e.load_instrument()
    x, y = opr.do_scan()
    #d = e.main_loop()
    # print(data)
    plt.plot(x,y)
