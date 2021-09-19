import sys
import os
import labphew
import logging
from labphew.core.tools.gui_tools import open_config_dialog
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Optionally place the path to your default config file here:
default_config = None
# Example for pointing to a different config file:
# default_config = os.path.join(labphew.repository_path, 'examples', 'my_own_config.yml')
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

def main(config_file = None):
    """
    Starts the GUI of the Blink example.
    Note, if config_file is not specified, or is set to '-default' or '-d',
    it will fall back to a default file specified in this module.
    Note, if '-browse' or '-b' is used for config_file, it will display a window that allows you to browse to the file.
    Note, if no config_file is specified, load_config() of the operator will be called without config filename.

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

    from labphew.controller.blink_controller import BlinkController
    from labphew.model.blink_model import BlinkOperator
    from labphew.view.blink_view import MonitorWindow, ScanWindow

    instr = BlinkController()
    opr = BlinkOperator(instr)
    opr.load_config(config_file)

    # Create a PyQt application:
    app = QApplication([])
    app_icon = QIcon(os.path.join(labphew.package_path, 'view', 'design', 'icons', 'labphew_icon.png'))
    app.setWindowIcon(app_icon)  # set an icon
    # Gui elements created now will be part of the PyQt application

    main_gui = MonitorWindow(opr)

    scan_gui = ScanWindow(opr, parent=main_gui)
    # fit_on_screen(scan_window)
    scans = {
        'Example scan 1': scan_gui
    }
    main_gui.load_scan_guis(scans)
    main_gui.show()

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
    # logging.getLogger('labphew').setLevel(logging.INFO)

    if len(sys.argv) > 1:
        # When run from command line, this code will pass the command line
        # arguments as arguments in the main() function:
        main(sys.argv[1])
    elif hasattr(sys, 'ps1'):
        # When this file is run directly in an interactive python console it will use the default specified at the top
        main(default_config)
    else:
        main()