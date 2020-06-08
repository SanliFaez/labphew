"""
labphew.View.monitor_window.py
==============
The Monitor Window displays a plot that updates over time at a given rate. (TODO: or view images)
The only parameter that can be changed within the window is the delay between two consecutive reads.
To change other parameters the user needs to open the configuration window.
To execute a special routine, one should run an instance of scan_window.
For inspitration: the initiation of scan_window routines can be implemented as buttons on the monitor_window
TODO:
    - build the UI without a design file necessary
    - think about and add a default operation
"""

import os
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, uic, QtWidgets

from .general_worker import WorkThread

# TODO: the following imports are necessary for child windows, they have to be adjusted and tested
#from .config_view import ConfigWindow  # to adjust experiment parameters
#from .scan_view import ScanWindow      # to perform single scan


class MonitorWindow(QtWidgets.QMainWindow):
    def __init__(self, operator, parent=None):
        super().__init__(parent)

        self.operator = operator
        self.refresh_time = 100

        p = os.path.dirname(__file__)
        uic.loadUi(os.path.join(p, 'design/UI/main_window.ui'), self)

        self.main_plot = pg.PlotWidget()
        self.main_plot.setLabel('bottom', 'Time', units='s')

        # layout = QtWidgets.QVBoxLayout() # merked for dletion

        self.verticalLayout.addWidget(self.main_plot)

        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_monitor)
        self.running_monitor = False

        self.startButton.clicked.connect(self.start_monitor)
        self.stopButton.clicked.connect(self.stop_monitor)
        self.ydata = np.zeros((0))
        self.xdata = np.zeros((0))
        self.p = self.main_plot.plot(self.xdata, self.ydata)

        # TODO: uncomment for testing the child windows
        # self.config_window = ConfigWindow(operator, parent=self)
        # self.config_window.propertiesChanged.connect(self.update_properties)
        # self.actionConfig.triggered.connect(self.config_window.show)
        #
        # self.scan_window = ScanWindow(operator)
        # self.actionScan.triggered.connect(self.scan_window.show)

    def update_properties(self, props):
        """
        Method triggered when the signal for updating parameters is triggered.
        """
        self.operator.properties['Monitor'] = props

    def start_monitor(self):
        """
        Starts a  monitor in a separated Worker Thread. There will be a delay for the update of the plot.
        """

        if self.running_monitor:
            print('Monitor already running')
            return
        self.running_monitor = True
        self.worker_thread = WorkThread(self.operator.scan_finished)
        self.worker_thread.start()
        self.update_timer.start(self.refresh_time)

    def stop_monitor(self):
        """
        Stops the monitor and terminates the working thread.
        """
        if not self.running_monitor:
            print('Monitor not running')
            return

        self.update_timer.stop()
        self.worker_thread.terminate()
        self.running_monitor = False

    def update_monitor(self):
        """
        This method is called through a timer. It updates the data displayed in the main plot.
        """
        self.xdata = self.operator.xdata
        self.ydata = self.operator.ydata

        self.p.setData(self.xdata, self.ydata)

    def update_value(self):
        pass

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QtWidgets.QMessageBox.question(self, 'Message',
                                           quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        event.accept()

