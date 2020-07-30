"""
Blink Model
===========

This module contains an example class of an Operator.
The purpose of this file is to illustrate the basic structure of an Operator.
This Operator is intended to work with labphew.controller.blink_controller.BlinkController
It may be run from command line or interacted with through a gui: labphew.view.blink_view.MonitorWindow

Example usage can be found at the bottom of the file under if __name__=='__main___'
"""
import os.path
import numpy as np
import yaml
from time import time, sleep, localtime, strftime
from datetime import datetime
import logging
import xarray as xr
import labphew


class BlinkOperator:
    """
    Example Operator class (to work with fake device)
    """
    def __init__(self, instrument, properties={}):
        """
        Create the Operator object
        The BlinkController object needs to be created before and passed as an argument.

        :param instrument: The instrument used by this Operator
        :type instrument: BlinkController object
        :param properties: optional properties dictionary, note that this can be loaded from file with load_config()
        :type properties: dict
        """
        self.logger = logging.getLogger(__name__)
        self.properties = properties
        self.instrument = instrument

        # Flags controlled by operator:
        self._busy = False  # indicates the operator is busy (e.g. with scan or monitor)
        self._new_scan_data = False  # signal there's new data that could be displayed (a gui would reset this to False after retrieving the data)
        self._new_monitor_data = False  # used to flag gui that new data is available

        # Flags controlled by external gui to control flow of loops (e.g. scan or monitor)
        self._stop = False  # signal a loop to stop (whenever operator is not busy it should be False)
        self._pause = False  # signal a loop to pause (whenever operator is not busy it should be False)
        self._allow_monitor = False  # monitor should not be run from command line, a gui can set this to True

        self._monitor_data = ('',False)  # placeholder for monitor data

    def _set_monitor_time_step(self, time_step):
        """
        Set Monitor time step.
        Forces the value to be at least 0.01, and warns for large values

        :param time_step: time step between acquisitions in the monitor loop (seconds)
        :type time_step: float
        """
        if time_step < 0.001:
            time_step = 0.001
            self.logger.warning(f"time_step too small, setting: {time_step}s")
        elif time_step> 0.1:
            self.logger.warning(f"setting time_step to {time_step}s (are you sure?)")
        self.properties['monitor']['time_step'] = time_step

    #
    # def _verify_scan_channels(self):
    #     """
    #     Checks if channels in properties are valid and returns analog out and analog in channel.
    #     Note that None is returned if an error is found
    #
    #     :return:  analog out and analog in channel of scan
    #     :rtype: (int, int)
    #     """
    #     if 'scan' not in self.properties:
    #         self.logger.error("'scan' not found in properties")
    #         return
    #     if 'ao_channel' not in self.properties['scan'] or self.properties['scan']['ao_channel'] not in [1,2]:
    #         self.logger.error("'ao_channel' not found in properties or invalid value (should be 1 or 2)")
    #         return
    #     if 'ai_channel' not in self.properties['scan'] or self.properties['scan']['ai_channel'] not in [1,2]:
    #         self.logger.error("'ai_channel' not found in properties or invalid value (should be 1 or 2)")
    #         return
    #     return self.properties['scan']['ao_channel'], self.properties['scan']['ai_channel']
    #
    # def _set_scan_start(self, value):
    #     """
    #     Set scan start value.
    #     Forces value to be in valid range and updates properties dictionary.
    #     Also corrects the sign of step if required.
    #
    #     :param value: start value of scan (V)
    #     :type value: float
    #     """
    #     ao_ch, _ = self._verify_scan_channels()
    #     if ao_ch is None:  # if _verify_scan_channels() returns nothing that means channel is invalid or not found
    #         return
    #     value = self.analog_out(ao_ch, value, verify_only=True)
    #     self.properties['scan']['start'] = value
    #     self._set_scan_step()
    #
    # def _set_scan_stop(self, value):
    #     """
    #     Set scan stop value.
    #     Forces value to be in valid range and updates properties dictionary.
    #
    #     :param value: stop value of scan (V)
    #     :type value: float
    #     """
    #     ao_ch, _ = self._verify_scan_channels()
    #     if ao_ch is None:  # if _verify_scan_channels() returns nothing that means channel is invalid or not found
    #         return
    #     value = self.analog_out(ao_ch, value, verify_only=True)
    #     self.properties['scan']['stop'] = value
    #     self._set_scan_step()
    #
    # def _set_scan_step(self, step=None):
    #     """
    #     Set scan step value. Note that it will correct the sign automatically accroding to start and stop values.
    #     If no step value is supplied it only corrects the sign of step.
    #
    #     :param step: the stepsize for the scan (V)
    #     :type step: float or None
    #     """
    #     if step == 0:
    #         self.logger.warning('stepsize of 0 is not possible')
    #         return
    #     if step is not None:
    #         self.properties['scan']['step'] = step
    #     if np.sign(self.properties['scan']['step']) != np.sign(self.properties['scan']['stop'] - self.properties['scan']['start']):
    #         self.properties['scan']['step'] *= -1

    def _monitor_loop(self):
        """
        Called by GUI Monitor to start the monitor loop.
        Not intended to be called from Operator. (Which should be blocked)
        """
        # First check if monitor is allowed to start
        if self._busy or not self._allow_monitor:
            self.logger.warning('Monitor should only be run from GUI and not while Operator is busy')
            return
        self._busy = True  # set flag to indicate operator is busy
        self._monitor_start_time = time()
        next_time = 0
        while not self._stop:
            timestamp = time() - self._monitor_start_time
            time_str = str(datetime.timedelta(seconds=timestamp))[:-3]   # (strip the last 3 digits)
            status = self.instrument.get_status()
            self._monitor_data = (time_str, status)
            self._new_monitor_data = True  # signal to a gui that new data is ready to be retrieved

            # Instead of sleep(), calculate when the next datapoint should be acquired and wait until that time arrives
            # this allows to keep the timing correct in case of slow data acquisition
            next_time += self.properties['monitor']['time_step']
            while time()-self._monitor_start_time < next_time:
                if self._stop: break  # check for stop flag while waiting to move to next point
        # Mandatory code at the end of _monitor_loop():
        self._stop = False  # reset stop flag to false
        self._busy = False  # indicate the operator is not busy anymore

    def do_scan(self, param=None):
        """
        An example of a method that performs a scan (based on parameters in the config file).
        This method can be run from a GUI, from command line or other script
        This scan sweeps the blink rate of the fake device and records its status.

        :param param: optional dictionary of parameters that will used to update the scan parameters
        :type param: dict
        :return: the AO voltage, and the measured AI voltages
        :rtype: list, list
        """
        if type(param) is dict:
            self.logger.info('Updating scan properties with supplied parameters dictionary.')
            self.properties['scan'].update(param)
        # Start with various checks and warn+return if something is wrong
        if self._busy:
            self.logger.warning('Scan should not be started while Operator is busy.')
            return
        if 'scan' not in self.properties:
            self.logger.error("The config file or properties dict should contain 'scan' section.")
            return
        required_keys = ['blink_period', 'time_between_points', 'number_of_points']
        if not all(key in self.properties['scan'] for key in required_keys):
            self.logger.error("'scan' should contain: "+', '.join(required_keys))
            return
        try:
            blink_period = self.properties['scan']['blink_period']
            print(blink_period)
            number_of_points = int(self.properties['scan']['number_of_points'])
            print(number_of_points)
            time_between_points = self.properties['scan']['time_between_points']
            print(time_between_points)
        except:
            self.logger.error("Error occured while reading scan config values")
            return

        # Apply blink_period
        self.instrument.set_blink_period(blink_period)

        self.point_number = []
        self.measured_state = []

        self._busy = True  # indicate that operator is busy

        self.logger.info("Starting scan ...")
        for i in range(number_of_points):
            self.point_number.append(i)
            state = int(self.instrument.get_status())  # get the state and convert True/False to 1/0
            self.measured_state.append(state)
            sleep(time_between_points)

            # The remainder of the loop adds functionality to plot data and pause and stop the scan when it's run from a gui:
            self._new_scan_data = True
            # before the end of the loop: halt if pause is True
            while self._pause:
                sleep(0.05)
                if self._stop: break
            # if (soft) stop was requested, break out of loop
            if self._stop:
                break

        self._stop = False  # reset stop flag to false
        self._busy = False  # indicate operator is not busy anymore
        self._pause = False  # is this necessary?

        return self.point_number, self.measured_state

    def save_scan(self, filename, metadata=None):
        """
        Store data in xarray Dataset and save to netCDF4 file.
        Optional metadata can be passed as a dict. Note that the keys should be strings and the values should be numbers or strings.
        To load data:
        import xarray as xr
        xr.load_dataset(filename)

        :param filename: full path and filename
        :type filename: str
        :param metadata: optional additional data to store (default: None)
        :type metadata: dict
        """
        # First test if the required data arrays have been generated (i.e. if the scan has run)
        if not hasattr(self, "point_number") or not hasattr(self, "measured_state"):
            self.logger.warning('no data to save yet')
            return
        if os.path.exists(filename):
            self.logger.warning('overwriting existing file: {}'.format(filename))
        data = xr.Dataset(
            coords={
                "point_number": (["point_number"], self.point_number)  # for a "coordinate" use the same name between []
            },
            data_vars={
                "measured_state": (["point_number"], self.measured_state)
            },
            attrs={
                "time": datetime.now().strftime('%d-%m-%YT%H:%M:%S'),
            }
        )
        for key in ['user', 'config_file']:
            if key in self.properties:
                data.attrs[key] = self.properties[key]
        # Add all numeric and string keys in scan
        for key, value in self.properties['scan'].items():
            if isinstance(value, (int, float, bool, str)):
                data.attrs[key] = value
        if type(metadata) is dict:
            data.attrs.update(metadata)  # add the optional metadata to the Dataset attributes
        self.data = data
        data.to_netcdf(filename)

    def load_config(self, filename=None):
        """
        If specified, this function loads properties from the configuration file and sets some settings to the instrument.

        :param filename: Path to the filename. Defaults to blink_config.yml in labphew.core.defaults
        :type filename: str
        """
        if filename is None:
            filename = os.path.join(labphew.package_path, 'core', 'defaults', 'blink_config.yml')
        with open(filename, 'r') as f:
            self.properties.update(yaml.safe_load(f))
        self.properties['config_file'] = filename

        if 'blink instrument' in self.properties:
            if 'max_blink_period' in self.properties['blink instrument']:
                self.instrument.max_blink_period = self.properties['blink instrument']['max_blink_period']
            if 'min_blink_period' in self.properties['blink instrument']:
                self.instrument.min_blink_period = self.properties['blink instrument']['min_blink_period']


if __name__ == "__main__":
    import labphew   # import this to use labphew style logging (by importing it before matplotlib it also prevents matplotlib from printing many debugs)
    import matplotlib.pyplot as plt

    # from labphew.controller.digilent.waveforms import DfwController

    # To import the actual device:
    # from labphew.controller.digilent.waveforms import DfwController

    # To import a simulated device:
    from labphew.controller.blink_controller import BlinkController

    instrument = BlinkController()

    opr = BlinkOperator(instrument)
    opr.load_config()

    import matplotlib.pyplot as plt
    t, state = opr.do_scan()
    plt.plot(t, state, '.-')
    plt.xlabel('scan time [s]')
    plt.ylabel('binary device state')

    new_scan_properties = {'blink_period': 1.0}
    t, state = opr.do_scan(new_scan_properties)
    plt.figure(2)
    plt.plot(t, state, '.-')
    plt.xlabel('scan time [s]')
    plt.ylabel('binary device state')

    # # Example of saving scan data
    # opr.save_scan(r'C:\Temp\blink7.nc')

    # # Example of reading data from file and plotting
    # import xarray as xr
    # dat = xr.load_dataset(r'C:\Temp\blink7.nc')
    # print(dat)
    # dat.measured_state.plot()


#
# # coding=utf-8
# """
# labphew blink modle
# ================
#
# blink_model.py is a minimalist class for demonstrating the concept view-model-controller to beginner
#
#
# """
# import os
# import numpy as np
# import yaml
# from time import time, sleep, localtime, strftime
#
# class Operator:
#     """
#     A primitive class generating a synthetic time series.
#     the main purpose of this class it to provide the minimal functions required for running a view
#     and can serve as the basis for a customized model
#     """
#
#     def __init__(self):
#         self.instrument = None
#         self.properties = {}  # TODO: read properties from yml config file
#         self.indicator = 0  # instrument-specific value shared with another display during the scan
#         self.blinking = False  # signalling scan in progress or instrument is engaged
#         self.paused = False  # signalling scan in progress or instrument is engaged
#         self.done = False  # signal for the end of a complete scan
#         self.t0 = time()
#
#     def main_loop(self):
#         """
#         primitive function that is called in the MonitorWindow
#         in blank_model, this function just tells the time
#         """
#         if not self.paused:
#             self.blinking = True
#             output = strftime("%H:%M:%S", localtime(time()))
#             sleep(0.03)
#
#         return output
#
#     def pause(self):
#         """
#         primitive function to pause the main loop or readout
#         """
#         self.paused = True
#         self.blinking = False
#
#     def resume(self):
#         """
#         primitive function to pause the main loop or readout
#         """
#         self.paused = False
#
#     def shut_down(self):
#         """
#         primitive function that is called in the MonitorWindow to safely close the application
#         """
#         print("bye bye!")
#
#     def do_scan(self, param=None):
#         """
#         primitive function for calling by the ScanWindow
#         """
#         if self.blinking:
#             raise Warning('Trying to start simultaneous operations')
#         self.done = False
#         if param == None:
#             start, stop, step = 1, 10, 1
#         else:
#             pass
#             # example of filling in variables from loaded class properties
#             #start = self.properties['Scan']['start']
#             #stop = self.properties['Scan']['stop']
#             #step = self.properties['Scan']['step']
#
#         num_points = np.int((stop-start)/step)
#         scan = np.linspace(start, stop, num_points)
#         output = 0 * scan
#         self.blinking = True
#
#         ### here comes the main actions of the scan
#         for i in range(np.size(scan)):
#             self.indicator = scan[i]
#             output[i] = 1/scan[i]
#
#         self.blinking = False
#         self.scan_finished()
#         return scan, output
#
#     def scan_finished(self):
#         """
#         Here, you can put any signal that has to be returned to the parent program that has called the scan
#         """
#         self.done = True
#
#     def load_config(self, filename=None):
#         """
#         If specified, this function loads the configuration file to generate the properties of the Scan.
#
#         :param str filename: Path to the filename. Defaults to Model/default/blink_config.yml if not specified.
#         """
#         if filename is None:
#             filename = '../core/defaults/blink_config.yml'
#
#         with open(filename, 'r') as f:
#             params = yaml.safe_load(f)
#
#         self.properties = params
#         self.properties['config_file'] = filename
#         self.properties['User'] = self.properties['User']['name']
#
#     def load_instrument(self, inst=None):
#         """
#         Loads an instrument that is necessary for performing the scan.
#         :param inst: it can be a model already initailized. If not provided, loads the default instrument.
#         """
#         if inst is None:
#             pass #TODO: put here commands for initializing a primitive controller like blink_controller
#         else:
#             self.instrument = inst
#
#
#
# if __name__ == "__main__":
#     e = Operator()
#     #e.load_config()
#     #e.load_instrument()
#     #x, data = e.do_scan()
#     d = e.main_loop()
#     print(d)
