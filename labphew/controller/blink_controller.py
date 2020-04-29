# -*- coding: utf-8 -*-
"""
==================
Example controller
==================

This is an example of a controller with a fake (invented) device. It should help to gide
developers to create new controllers for real devices.


"""
from hyperion.core import logman as logging
from hyperion.controller.base_controller import BaseController

class ExampleController(BaseController):
    """ Example output device that does not connect to anything"""

    FAKE_RESPONSES = {'A': 1,
                     }

    def __init__(self, settings):
        """ Init of the class.

        :param settings: this includes all the settings needed to connect to the device in question.
        :type settings: dict

        """
        super().__init__(settings)  # mandatory line
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class ExampleController created.')
        self.name = 'Example Controller'

        self._amplitude = []

    def initialize(self):
        """ Starts the connection to the device in port """
        self.logger.info('Opening connection to device ExampleController (a fake connection)')
        self._is_initialized = True     # THIS IS MANDATORY!!
                                        # this is to prevent you to close the device connection if you
                                        # have not initialized it inside a with statement
        self._amplitude = self.query('A?')

    def finalize(self):
        """ This method closes the connection to the device.
        It is ran automatically if you use a with block

        """
        self.logger.info('Closing connection to device.')
        self._is_initialized = False

    def idn(self):
        """ Identify command

        :return: identification for the device
        :rtype: string
        """
        self.logger.debug('Ask IDN to device.')
        return 'ExampleController device'

    def query(self, msg):
        """ writes into the device msg

        :param msg: command to write into the device port
        :type msg: string
        """
        self.logger.debug('Writing into the example device:{}'.format(msg))
        self.write(msg)
        ans = self.read()
        return ans

    def read(self):
        """ Fake read that returns always the value in the dictionary FAKE RESULTS.
        
        :return: fake result
        :rtype: string
        """
        return self.FAKE_RESPONSES['A']

    def write(self, msg):
        """ Writes into the device
        :param msg: message to be written in the device port
        :type msg: string
        """
        self.logger.debug('Writing into the device:{}'.format(msg))


    @property
    def amplitude(self):
        """ Gets the amplitude value.

        :getter:
        :return: amplitude value in Volts
        :rtype: float
        :setter:
        :param value: value for the amplitude to set in Volts
        :type value: float

        For example, to use the getter you can do the following
        ampl = this_controller.amplitude
        For example, using the setter looks like this:
        this_controller.amplitude = 5

        """
        self.logger.debug('Getting the amplitude.')
        return self._amplitude

    @amplitude.setter
    def amplitude(self, value):
        # would be nice to add a way to check that the value is within the limits of the device.
        if self._amplitude != value:
            self.logger.info('Setting the amplitude to {}'.format(value))
            self._amplitude = value
            self.write('A{}'.format(value))
        else:
            self.logger.info('The amplitude is already {}. Not changing the value in the device.'.format(value))


class ExampleControllerDummy(ExampleController):
    """
    Example Controller Dummy
    ========================

    A dummy version of the Example Controller.

    In essence we have the same methods and we re-write the query to answer something meaningful but
    without connecting to the real device.

    """


    def query(self, msg):
        """ writes into the device msg

        :param msg: command to write into the device port
        :type msg: string
        """
        self.logger.debug('Writing into the dummy device:{}'.format(msg))
        ans = 'A general dummy answer'
        return ans



if __name__ == "__main__":

    dummy = False  # change this to false to work with the real device in the COM specified below.

    if dummy:
        my_class = ExampleControllerDummy
    else:
        my_class = ExampleController

    with my_class(settings  = {'port':'COM10', 'dummy': False}) as dev:
        dev.initialize()
        print(dev.amplitude)
        dev.amplitude = 5
        print(dev.amplitude)


