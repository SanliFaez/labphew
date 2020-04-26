"""
Start Function
==============
After installing labphew it is possible to start it directly from within the command line using `labphew.start`. It takes one argument that is the path to the configuration file.

    $ labphew.start Config/application.yml

"""

import sys

def main():
    """Starts the GUI for the application using the config file specified as system argument.
    """
    args = sys.argv[1:]
    if len(args) != 1:
        print(help_message)
        return

    from labphew.Model.application.IVscan import Operator
    from labphew.View.start import start_gui

    e = Operator()
    e.load_config(args[0])
    e.load_daq()
    start_gui(e)


help_message = \
"""
Congratulations! 
You're almost ready to run a labphew module
-----------------------------
In order to run a module with labphew, you need to insert the path to the config file.
For example, you can invoke this program as:
labphew Config/experiment_dummy.yml
"""

if __name__ == "__main__":
    main()
