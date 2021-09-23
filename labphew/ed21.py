import sys
import os
import labphew
import logging
from labphew.core.tools.gui_tools import open_config_dialog
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Optionally place the path to your default config file here:
#default_config = None
# Example for pointing to a different config file:
default_config = os.path.join(labphew.repository_path, 'examples', 'ed21.yml')
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

def main(config_file = None):
    """
    Starts the GUI of the Digilent Analog Discovery 2 example.
    Note, if config_file is not specified, or is set to '-default' or '-d',
    it will fall back to a default file specified in this module.
    Note, if '-browse' or '-b' is used for config_file, it will display a window that allows you to browse to the file.
    Note, if no config_file is specified, load_config() of the operator will be called without

    :param config_file: optional path to config file
    :type config_file: str
    """

    # If -browse (or -b) is used for config_file, display an open file dialog:
    if config_file == '-browse' or config_file == '-b':
        config_file = open_config_dialog()
    # If -default (or -d) is used for config_file, switch it out for the default specified in the top of this file:
    if config_file == '-default' or config_file == '-d':
        config_file = default_config
        print('Using default_config file specified in {}'.format(__file__))
    if config_file is None:
        print('Using Operator without specifying a config file.')

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Load your classes and create your gui:

    from labphew.controller.digilent.waveforms import DfwController  # If you were to use with real device
    # from labphew.controller.digilent.waveforms import SimulatedDfwController as DfwController  # To test with simulated device
    from labphew.model.analog_discovery_2_model import Operator
    from labphew.view.analog_discovery_2_view import MonitorWindow, ScanWindow, ScanIVWindow

    instrument = DfwController()
    opr = Operator(instrument)
    opr.load_config(default_config)

    # Create a PyQt application
    app = QApplication(sys.argv)
    app_icon = QIcon(os.path.join(labphew.package_path, 'view', 'design', 'icons', 'labphew_icon.png'))
    app.setWindowIcon(app_icon)  # set an icon
    main_gui = MonitorWindow(opr)
    # To add Scan window(s) to the Monitor window use the following code.
    scan_1 = ScanWindow(opr, parent=main_gui)
    scan_2 = ScanIVWindow(opr, parent=main_gui)
    scans = {
        'Sweep &voltage': [scan_1, {'shortcut':"Ctrl+Shift+V", 'statusTip':'Voltage sweep scan'}],  # note that the dictionary is optional
        'IV scan': [scan_2, {'shortcut': "Ctrl+Shift+I", 'statusTip': 'measure an IV curve'}]
             }
    main_gui.load_scan_guis(scans)
    main_gui.show()  # make sure the GUI will be displayed

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # This line will start the application:
    exit_code = app.exec_()
    # Print the exit code and exit unless it was run from interactive console):
    if hasattr(sys, 'ps1'):
        print('Finished with exit code', exit_code)
    else:
        sys.exit(exit_code)


if __name__ == '__main__':
    # You could use this code to change the logging level:
    logging.getLogger('labphew').setLevel(logging.INFO)

    if len(sys.argv) > 1:
        # When run from command line, this code will pass the command line
        # arguments as arguments in the main() function:
        main(sys.argv[1])
    elif hasattr(sys, 'ps1'):
        # When this file is run directly in an interactive python console it will use the default specified at the top
        main(default_config)
    else:
        main()