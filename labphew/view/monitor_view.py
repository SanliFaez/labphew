"""
labphew.view.monitor_view.py
==============
The MonitorWindow class displays a plot or other data that updates over time at a given rate. (TODO: or view images)
All the processes that are not relating to user interaction are handled by the Operator class in the model folder

To change parameters the user needs to open the configuration window.
To execute a special routine, one should run an instance of scan_view.
For inspiration: the initiation of scan_view routines can be implemented as buttons on the monitor_view
TODO:
    - build the UI without a design file necessary
    - connect the UI parameters to config file

"""

import os
import numpy as np
import pyqtgraph as pg   # used for additional plotting features

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QSlider, QLabel, QMessageBox
from PyQt5.QtGui import QFont, QIcon

from labphew.core.base.general_worker import WorkThread

# TODO: the following imports are necessary for child windows, they have to be adjusted and tested
#from .config_view import ConfigWindow  # to adjust experiment parameters
#from .scan_view import ScanWindow      # to perform single scan


class MonitorWindow(QMainWindow):
    def __init__(self, operator, display = 'text', parent=None):


        super().__init__(parent)

        self.operator = operator
        self.refresh_time = 100

        self.setWindowTitle('labphew monitor')
        self.set_UI(display)

        # p = os.path.dirname(__file__)
        # uic.loadUi(os.path.join(p, 'design/UI/main_window.ui'), self)

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_monitor)
        self.running_monitor = False

        self.button_start.clicked.connect(self.start_monitor)
        self.button_stop.clicked.connect(self.stop_monitor)

        # TODO: uncomment for testing the child windows
        # self.config_window = ConfigWindow(operator, parent=self)
        # self.config_window.propertiesChanged.connect(self.update_properties)
        # self.actionConfig.triggered.connect(self.config_window.show)
        #
        # self.scan_window = ScanWindow(operator)
        # self.actionScan.triggered.connect(self.scan_window.show)

    def set_UI(self, display):
        """
        code-based generation of the user-interface based on PyQT
        """
        self.central_widget = QWidget()
        self.button_start = QPushButton('Start', self.central_widget)
        self.button_stop = QPushButton('Stop', self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # self.slider = QSlider(Qt.Horizontal)
        # self.slider.setRange(1, 10)
        if display == "text":
            self.message = QLabel('Press a button!', self.central_widget)
            self.message.setFont(QFont("Arial", 32, QFont.Normal))
            self.layout.addWidget(self.message, alignment=Qt.AlignCenter)

        if display == "plot":
            self.main_view = pg.PlotWidget()
            self.layout.addWidget(self.main_view)
            self.main_view.setLabel('bottom', 'time', units='s')
            self.plot = self.main_view.plot([0], [0])
        elif display == "image":
            self.main_view = pg.ImageView(view=pg.PlotItem())
            self.layout.addWidget(self.main_view)

        self.layout.addWidget(self.button_start)
        self.layout.addWidget(self.button_stop)
        self.setCentralWidget(self.central_widget)

    def update_properties(self, props):

        self.operator.properties['Monitor'] = props

    def start_monitor(self):
        """
        Starts a  monitor in a separated Worker Thread. There will be a delay for the update of the plot.
        """

        if self.running_monitor:
            print('Monitor already running')
            return
        self.running_monitor = True
        self.worker_thread = WorkThread(self.operator.main_loop)
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
        msg = self.operator.main_loop()
        self.message.setText(msg)
        # self.plot.setData(xdata, ydata)


    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit labphew monitor?"
        reply = QMessageBox.question(self, 'Message',
                                           quit_msg, QMessageBox.Yes, QMessageBox.No)
        event.accept()

if __name__ == "__main__":
    """

    """
    import sys
    from PyQt5.QtWidgets import QApplication
    from labphew.model.blank_model import Operator

    e = Operator()

    ### Example of putting in parameters for the operator
    # session = {'port_monitor': 1,
    #            'time_resolution': Q_('1ms'),
    #            'refresh_time': Q_('100ms'),
    #            'total_time': Q_('15s'),
    #            'scan_port_out': 1,
    #            'scan_start': Q_('0.1V'),
    #            'scan_stop': Q_('0.7V'),
    #            'scan_step': Q_('0.1V'),
    #            'scan_port_in': 2,
    #            'scan_delay': Q_('10ms'),
    #            }
    # e.properties = session

    app = QApplication(sys.argv)
    s = MonitorWindow(e)
    s.show()
    app.exit(app.exec_())