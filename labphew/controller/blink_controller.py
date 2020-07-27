# -*- coding: utf-8 -*-
"""
================
Blink controller
================

This is an example of a controller with a fake (invented) device. It should help to guide
developers to create new controllers for real devices.


"""
import logging
import time

class BlinkController:
    """
    Blink Controller: Fake Device to act as an example
    """
    def __init__(self, properties = {}):
        """
        Create Blink controller object which simulates a fake device.

        :param properties: optional properties dictionary
        :type properties: dict
        """
        self.logger = logging.getLogger(__name__)

        # Set parameters to simulate the device
        self.__simulated_device_blink_period= 1  #
        self.__simulated_device_start_time = time.time()
        self.__simulated_device_status = False
        self.__simulated_device_enabled = True

        # Set user parameters. Optionally get them from properties. Otherwise use hardcoded values:
        if 'max_blink_period' in properties:
            self.max_blink_period = properties['max_blink_period']
        else:
            self.max_blink_period = 2

        if 'min_blink_period' in properties:
            self.min_blink_period = properties['min_blink_period']
        else:
            self.min_blink_period = 0.2

        self.logger.debug('BlinkController object created')

    def set_blink_period(self, period_s):
        """
        Method that mimics setting a device parameter.

        :param period_s:
        :type period_s:
        """
        # You could do some checks first. For example to see if the value is in an allowed range:
        if period_s > self.max_blink_period:
            self.logger.warning(f'Blink period of {period_s}s exceeds maximum allowed. Setting period to {self.max_blink_period}s')
            period_s = self.max_blink_period
        if period_s < self.min_blink_period:
            self.logger.warning(f'Blink period of {period_s}s exceeds minimum allowed. Setting period to {self.min_blink_period}s')
            period_s = self.min_blink_period
        # Your code to communicate with the device goes here.
        # For the purpose of demonstration, this method simulates setting a parameter on a device:
        self.logger.debug('"Sending" blink period of {} to device'.format(period_s))
        self.__simulated_device_blink_period = period_s
        self.__simulated_device_start_time = time.time()
        self.__simulated_device_status = not self.__simulated_device_status

    def enable(self, enable):
        """
        Method that mimics setting a device parameter.

        :param enable: Enable device output
        :type enable: bool
        """
        # Your code to communicate with the device goes here.
        # For the purpose of demonstration, this method simulates setting a parameter on a device:
        self.__simulated_device_enabled = bool(enable)
        self.logger.debug('Device is "{}"'.format(self.__simulated_device_enabled))

    def get_status(self):
        """
        Method that mimics communicating with a device and retrieving a status.

        :return: Device is "on"
        :rtype: bool
        """
        # Your code to communicate with the device goes here.
        # For the purpose of demonstration, this method returns a simulated status:
        self.logger.debug('"Retrieving" status from device')
        if self.__simulated_device_enabled:
            return bool(int((time.time()-self.__simulated_device_start_time)/self.__simulated_device_blink_period/.5) % 2)
        else:
            self.logger.warning('Device is disabled')
            return False

if __name__ == "__main__":
    import labphew

    device = BlinkController()
    print(device.get_status())

    device.set_blink_period(3)
    device.set_blink_period(0.1)

    # import matplotlib.pyplot as plt
    # device.logger.setLevel(logging.INFO)
    # record = []
    # for i in range(100):
    #     time.sleep(0.01)
    #     record.append(device.get_status())
    # plt.plot(record)
