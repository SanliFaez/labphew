# coding=utf-8
"""
Start GUI
=========

Convenience function to wrap the initialization of a window.
The Operator class should be created outside and passed as argument.

    >>> e = Operator()
    >>> e.load_config('filename')
    >>> e.load_daq()
    >>> start_gui(e)

"""
import sys

def start_gui(operator, config):
    """ Starts a GUI for the monitor using the provided operator.
    :param:
        operator: an operator object with a loaded config.
    """
    from PyQt5.QtWidgets import QApplication
    from labphew.View.blink_window import MonitorWindow

    ap = QApplication(sys.argv)
    m = MonitorWindow(operator)
    m.show()
    ap.exit(ap.exec_())

def start_cli(operator, config, output = None):
    """ Starts an operation from the command lines using the provided operator.
    :param operator: an operator object with a loaded config.
    """
    e = operator()
    e.load_config(config)
    e.load_daq()
    e.do_scan()
    e.save_scan_data(output)


if __name__ == '__main__':
    from labphew.Model.application import blink
    op = blink.Operator
    pa = './Model/default/blink.yml'
    f = '../tempfile.txt'
    start_cli(op, pa, output=f)