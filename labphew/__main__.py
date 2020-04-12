"""
Start Function
==============
After installing labphew it is possible to start it directly from within the command line using `labphew.start`. It takes one argument that is the path to the configuration file.

    $ labphew.start Config/experiment.yml

"""

import sys

def main():
    """Starts the GUI for the experiment using the config file specified as system argument.
    """
    args = sys.argv[1:]
    if len(args) != 1:
        print(help_message)
        return

    from labphew.Model.experiment.IV_measurement import Experiment
    from labphew.View.start import start_gui

    experiment = Experiment()
    experiment.load_config(args[0])
    experiment.load_daq()
    start_gui(experiment)


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
    start()
