# Template with the minimal structure and extra explanatory comments.
# For hyperion version 0.1

"""
=======================
Device Model Controller
=======================

Description of device controller
"""

from hyperion import logging
from hyperion.controller.base_controller import BaseController

# Preferred class name includes the model name and ends with Controller
# Use 
class DeviceModelController(BaseController):
    """ 
    More description here
    
    :param settings: This includes all the settings needed to connect to the device in question.
    :type settings: dict
    """
    
    # MANDATORY METHOD:
    def __init__(self, settings):
        """ Don't put docstring here but directly under class ClassName() """
        
        # MANDATORY LINES at beginning of __init__():
        # Call init of BaseController
        super().__init__(settings)
        # In the background, the __init__() of Basecontroller will
        # do these lines for you:
        # self._is_initialized = False
        # self._settings = settings

        # Create logger
        self.logger = logging.getLogger(__name__)
       
        self.name = 'Device Model Controller'

        # Storing the settings in internal variables.
        # If they're not specified, default values are used.

    # Note the BaseController class will add methods __enter__() and __exit__()
    # These allow the use of the with statement. __exit__() will call finalize()

    # MANDATORY METHOD
    # If you don't make it the method of the same name from BaseController will
    # be called to warn you that you've forgotten to make it.
    def initialize(self):
        """ Starts the connection to the device """
        
        # Your code to connect to the device goes here

        # MANDATORY LINE at end of initialize():
        # Set a flag to indicate the device is connected
        self._is_initialized = True

    # MANDATORY METHOD
    # If you don't make it the method of the same name from BaseController will
    # be called to warn you that you've forgotten to make it.
    def finalize(self):
        """
        This method closes the connection to the device.
        It is ran automatically if you use a with block.
        """
        
        if self._is_initialized:
            # Your code to close the connection goes here
            self.logger.debug('Doing something')
        else:
            self.logger.warning('Finalizing before initializing connection to {}'.format(self.name))

        # MANDATORY LINE at end of finalilze:
        # Reset the flag to indicate the object is not connected to the device
        self._is_initialized = False

    # strongly recommended method:
    def idn(self):
        """
        Identify command

        :return: identification for the device
        :rtype: string
        """
        self.logger.debug('Ask *IDN? to device.')
        return self.query('*IDN?')[-1]

    # common method:
    def write(self, message):
        """
        Sends the message to the device.

        :param message: the message to write to the device
        :type message: string
        """
        if not self._is_initialized:
            raise Warning('Trying to write to {} before initializing'.format(self.name))

        message += self._write_termination
        self.logger.debug('Sending to device: {}'.format(message))
        # Your code to write message to device
           
    # common method
    def read(self):
        """
        Reads the response from the device
        
        :return: message from device
        :rtype: strings
        """
        # Yout code to read from the device
        return response

    # common method
    def query(self, message):
        """
        Writes message to the device and returns the response of the device

        :param message: command to send to the device
        :type message: str
        :return: list of responses received from the device
        :rtype: list of strings
        """
        self.write(message)
        response = self.read(message)
        return response


# The dummy version of the controller class:
# Its name should be the same as the main controller class above,
# but with 'Dummy' suffix. (This allows it to be automatically found)
# It shoudl inherit from the main controller class above
class DeviceModelControllerDummy(DeviceModelController):
    """
    Device Model Controller Dummy
    =============================

    A dummy version of the Device Model Controller

    Some notes on how to use it.
    """
    
    # If you don't want to write it put this one word here.
    # In that case the dummy class is identical to the parent class.
    pass 
    
    # Otherwise remove the pass above and add methods that overwrite those from
    # the parent class. Typically you would overwrite the methods that directly
    # deal with communicating to the hardware, such as read() and write().


# Here follows code to for testing (during development)
# It is run when you run this file directly.

if __name__ == "__main__":

    # Set dummy=False to work with the real device
    dummy = False

    if dummy:
        my_class = DeviceModelControllerDummy
    else:
        my_class = DeviceModelController

    # settings for your device
    example_settings = {'port': 'COM4', 'baudrate': 9600, 'write_termination': '\n'}

    # Here we create an object of our controller class.
    # By doing it in a with statement, __exit__() and hence finalize() will be 
    # called even if the code crashes. This will ensure the connection to the 
    # device is properly closed.
    with my_class(settings = example_settings) as dev:
        dev.initialize()
        print('Start:')

        # Call methods and print result to test if the class works as expected.
        
        # No need to call dev.finalize() The with statement takes care of that.
