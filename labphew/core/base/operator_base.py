# coding=utf-8
"""
Operator Base Class
===================

Base class for operators.
- When the object of the child class is created the base class checks if required and recommended methods are present
  in the child class (and in the base class itself).
- By inheriting, methods from this base class will be used if they are missing in the child class. This allows to
  implement some fallback functionality and to warn the user.
- In addition it implements the __enter__ and __exit__ methods to allow the class to be used in a python with block.

Example usage can be found at the bottom of the file under if __name__=='__main___'
"""

import labphew
import logging
import os.path
import yaml


def _check_method_presence(cls, base, method):
    """
    Test is a method is present in a class and whether it's inherited, overwritten, or "new".
    Table to explain return values:
    (cls, base)
    False, False    Neither child nor base has the method
    False, True     The child class inherits the method from the base class
    True,  False    The child has the method, the base doesn't
    True,  True     Both classes have the method, but the child has overwritten the one from the base

    :param cls: The child class
    :type cls: class
    :param base: The parent or base class from which the child inherits
    :type base: class
    :param method: name of the method to test
    :type method: str
    :return: uniquely present in cls, present in base
    :rtype: bool, bool
    """
    if not hasattr(cls, method):
        # Neither cls nor base has the method
        return False, False
    elif not hasattr(base, method):
        # Only cls has the method
        return True, False
    elif getattr(cls, method) is getattr(base, method):
        # Only base has the method and cls inherits the identical method
        return False, True
    else:
        # last option: cls has a different implementation of the method
        return True, True

class OperatorBase:
    def __new__(cls, *args, **kwargs):
        """
        Get's called before the object (of the child class) is created and warns if required or
        recommended methods are missing in that class.
        Note that required and recommended methods may exist in this Base class.
        """
        required = ['__init__']
        recommended = ['load_config', 'disconnect_devices', '_monitor_loop', 'save_scan', 'do_scan']

        base = cls.mro()[1]
        missing_required = []
        for method in required:
            if _check_method_presence(cls, base, method)[0] != True:
                print('MISSING required method [{}] in class [{}]'.format(method, cls.__name__))
                missing_required.append(method)
        for method in recommended:
            c, b = _check_method_presence(cls, base, method)
            if not c:
                if b:
                    print('MISSING required method [{}] in class [{}], falling back on base class method'.format(method, cls.__name__))
                else:
                    print('MISSING required method [{}] in class [{}], ALSO MISSING in base class'.format(method, cls.__name__))
                    missing_required.append(method)
        if missing_required:
            raise NotImplementedError(missing_required)
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.logger.warning("Your Operator class should have an __init__ method")
        raise NotImplementedError("You must override __init__")

    def _monitor_loop(self, *args, **kwargs):
        self.logger.warning("If you want to use your Operator in a MonitorWindow, your Operator should have a _monitor_loop method")
        raise NotImplementedError("Must override _monitor_loop to use it")

    def load_config(self, filename, *args, **kwargs):
        self.logger.warning("Your Operator class should have a load_config method. Using method from OperatorBase")

        if not hasattr(self, 'properties'):
            self.logger.warning("Your Operator does't have a properties dictionary yet: creating one")
            self.properties = {}
        if filename and not os.path.isfile(filename):
            self.logger.error('Config file not found: {}, falling back to default'.format(filename))
            return
        with open(filename, 'r') as f:
            self.properties.update(yaml.safe_load(f))
        self.properties['config_file'] = filename

    def do_scan(self, *args, **kwargs):
        self.logger.info("""
        do_scan is the default name for a scan method of an Operator. If you see this message that means you're trying to
        run do_scan() without having created it in your Operator. Note that you could use a different name, or create 
        multiple scan methods, but that you have to modify your GUI to actually  start those methods. 
        """)

    def save_scan(self, *args, **kwargs):
        self.logger.info("""
        save_scan is the default name for method of an Operator to save scan data. If you see this message that means 
        you're trying to call it (perhaps from a ScanWindow?) without having created it in your Operator. Note that you 
        could use a different name, or create multiple save methods (for multiple scans?), but that you have to modify 
        your GUI to actually use those save methods. 
        """)

    def disconnect_devices(self):
        self.logger.warning("Your Operator is missing the disconnect_devices method. Use that to disconnect from your devices when required.")

    # the next two methods are needed so the context manager 'with' works.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ This method get's called when exiting a python with block (when the code completed but also when an error occured)"""
        self.logger.debug('Calling disconnect_devices() before exiting with block')
        self.disconnect_devices()
