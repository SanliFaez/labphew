"""
======================
Base (Meta) Instrument
======================
This file contains two base classes to be used as parent classes for Instrument classes and MetaInstrument classes.
"""
from hyperion import logging
from hyperion.tools.loading import get_class


class BaseInstrument():
    """
    Let Instrument classes inherit from this class.
    An instrument is a layer between the Controller (which takes care of hardware communication) and the user or
    Experiment. This instrument layer allows to add functionality, pint-units and may be used as an abstraction layer for
    similar controllers.


    """
    def __init__(self, settings):    # passing settings is required !
        """ Init for the class

        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class BaseInstrument created with settings: {}'.format(settings))
        self.settings = settings

        if 'dummy' in settings and settings['dummy']==True:
            if 'controller' in settings:
                if len(settings['controller']) < 5 or settings['controller'][-4]!='Dummy':
                    settings['controller'] += 'Dummy'

        self.controller_class = self.load_controller(settings)
        self.logger.debug('Controller class: {}'.format(self.controller_class))
        if 'via_serial' in settings:
            port = settings['via_serial'].split('COM')[-1]
            self.controller = self.controller_class.via_serial(port)
        elif 'via_gpib' in settings:
            self.logger.warning('NOT TESTED')
            port = settings['via_gpib'].split('COM')[-1]
            self.controller = self.controller_class.via_gpib(port) # to do
        elif 'via_usb' in settings:
            self.logger.warning('NOT TESTED')
            port = settings['via_usb'].split('COM')[-1]
            self.controller = self.controller_class.via_usb(port)  # to do
        else:
            self.controller = self.controller_class(settings)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def initialize(self):
        """ Starts the connection to the device.

        If you need to parse arguments to the initialize, make your own initialize method in
        your instrument class.
        """
        self.logger.warning('Initialization done from the BaseInstrument class.')
        self.controller.initialize()

    def finalize(self):
        """ This is to close connection to the device.

        If you need to parse arguments to the finalize, make your own finalize method in
        your instrument class.
        """
        self.logger.info('Closing connection to device.')
        self.controller.finalize()

    def idn(self):
        """ Identify command

        """
        self.logger.warning('Method used from the BaseInstrument class')
        self.logger.debug('Ask IDN to device.')
        return self.controller.idn()

    def load_controller(self, settings):
        """ Loads controller

        :param settings: dictionary with the field controller
        :type settings: dict

        :return: controller class
        :rtype: class
        """
        if 'controller' not in settings:
            raise NameError('The input dictionary needs to have a key called "controller" with a string pointing to the'
                            'right controller and the name of the class to use. ')
        else:
            self.logger.debug('Loading the controller: {}'.format(settings['controller']))
            return get_class(settings['controller'])
            ### Changed old code below for the line above
            # controller_name, class_name = settings['controller'].split('/')
            # self.logger.debug('Controller name: {}. Class name: {}'.format(controller_name, class_name))
            # my_class = getattr(importlib.import_module(controller_name), class_name)
            # return my_class

class BaseMetaInstrument():
    """
    Let MetaInstrument classes inherit from this class.
    A MetaInstrument takes other instruments as inputs (and does not use a controller)

    The finalize() method of a MetaInstrument will call the finalize() methods of the sub instruments.
    In the case of an Experiment class, the MetaInstruments don't need to be finalized because the Instruments itself
    will be finalized.
    """
    def __init__(self, settings, sub_instruments):  # passing settings is required !
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class BaseInstrument created with settings: {}'.format(settings))
        self.settings = settings
        self.sub_instruments = sub_instruments

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # A MetaInstrument should not finalize its sub classes when it exits a with statement
        pass

    def finalize(self):
        for sub_instr_key, sub_instr in self.sub_instruments.items():
            self.logger.warning('Finalizing sub instrument: {}'.format(sub_instr_key))
            sub_instr.finalize()


if __name__ == "__main__":
    print('you should not be running this file alone')


