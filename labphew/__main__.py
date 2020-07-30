"""
Start Function
==============
After installing labphew it is possible to start it directly from within the command line using `labphew.start`. It takes one argument that is the path to the configuration file.

    $ labphew.start default_configs/application.yml

"""

import labphew
import sys
import os
from importlib import import_module
from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtGui import QIcon
from time import time

def main():
    """Starts the GUI for the application using the default_configs file specified as system argument.
    """
    if len(sys.argv) < 1:
        show_help()

    try:
        mod = import_module('labphew.'+sys.argv[1])
    except:
        print('Could not find module {}'.format(sys.argv[1]))
        show_help()
        return

    if not hasattr(mod, 'main'):
        print('Modele {} does not have a main() function'.format(sys.argv[1]))
        show_help()
        return

    sys.argv.pop(1)  # remove the first command line argument

    # if no second argument (i.e. config file) was given, show open file dialog:
    if len(sys.argv) == 1:
        app = QApplication([])
        ofdlg = QFileDialog()
        config_file = ofdlg.getOpenFileName(None, 'Open config file', filter = "YAML (*.yml);;All Files (*.*)")
        ofdlg.close()
        del app
        if config_file[0]:
            sys.argv.append(config_file[0])

    # run the main() function of the requested module
    getattr(mod, 'main')()


def show_help():
    yml_path = os.path.join(labphew.repository_path, 'examples', 'default_config', 'blink_config.yml')
    print('\n'+help_message.format(yml_path))




help_message = \
"""
Congratulations! 
You're almost ready to run your labphew module
-----------------------------
In order to run a module with labphew, you need to insert the module name (and optionally the path to the config file). 
For example, you can invoke this program as:
labphew start_blink {}
If you don't specify the config file 
"""

if __name__ == "__main__":
    main()
