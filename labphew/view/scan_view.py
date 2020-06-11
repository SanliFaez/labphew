"""
labphew.view.scan_window.py
===========
The main purpose of the scan_window and its derivatives is to view the progress of one-time operations
called by an operator that is already initialized in the monitor_window.
It implements a form where the user can change the input port,
and delay between measurements. It has control also over the output port and range.

TODO:
    - build the UI without a design file
    - think about and add a default operation

"""
import os
import numpy as np
import pyqtgraph as pg

from PyQt5.QtCore import Qt, QThread, QTimer
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QSlider, QLabel, QFileDialog, QAction
from PyQt5.QtGui import QFont, QIcon

from labphew.core.base.general_worker import WorkThread


class ScanWindow(QMainWindow):
    def __init__(self, operator, parent=None):

        super().__init__(parent)
        self.operator = operator
        self.setWindowTitle('labphew monitor')
        self.set_UI("plot")
        self.refresh_time = 30


        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_scan)

        self.button_start.clicked.connect(self.start_scan)
        self.button_stop.clicked.connect(self.stop_scan)
        self.button_save.clicked.connect(self.save_data)

        self.running_scan = False

    def set_UI(self, display):
        """
        code-based generation of the user-interface based on PyQT
        """
        self.central_widget = QWidget()
        self.button_start = QPushButton('Start', self.central_widget)
        self.button_stop = QPushButton('Stop', self.central_widget)
        self.button_save = QPushButton('Save', self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # self.slider = QSlider(Qt.Horizontal)
        # self.slider.setRange(1, 10)
        self.message = QLabel('Press a button!', self.central_widget)
        self.message.setFont(QFont("Arial", 12, QFont.Normal))
        self.layout.addWidget(self.message, alignment=Qt.AlignCenter)

        if display == "plot":
            self.main_view = pg.PlotWidget()
            self.layout.addWidget(self.main_view)
            self.main_view.setLabel('bottom', 'measurement')
            self.plot = self.main_view.plot([0], [0])

        self.layout.addWidget(self.button_start)
        self.layout.addWidget(self.button_stop)
        self.layout.addWidget(self.button_save)
        self.setCentralWidget(self.central_widget)


    def start_scan(self):
        """Starts the scan as defined in the Experiment model. Gets the parameters from the GUI, i.e.:
        it gets the input port and delay, the output port and range.
        It updates the plot with the proper units and ranges and creates a worker thread for running the
        scan.
        A timer will be responsible for updating the values into the plot.
        """
        if self.running_scan:
            print('Scan already running')
            return

        self.running_scan = True

        self.worker_thread = WorkThread(self.operator.do_scan)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.stop_scan)
        self.worker_thread.start()
        self.update_timer.start(self.refresh_time)

    def update_scan(self):
        """
        Displays an indicator that measurement is running
        The method also monitors whether the scan is still running or not. If it has stopped it will update
        the GUI in order to know it.
        """
        self.message.setText(self.operator.indicator)
        # self.main_view.setData(self.operator.scan, self.operator.output)
        if self.operator.done:
            self.message.setText('Scanning finished!')
            self.running_scan = False
            self.stop_scan()

    def stop_scan(self):
        """Stops the scan if it is running. It sets the proper variable to the application model in order
        to finish it in an elegant way. It stops the update timer and calls the update plot one last time
        in order to display the very last available data.
        """
        if not self.running_scan:
            return

        self.running_scan = False
        if self.operator.done:
            self.message.setText('Scanning finished!')
            self.main_view.plot(self.operator.scan, self.operator.output)
        else:
            self.message.setText('Scan paused')
            self.operator.pause()
        self.update_timer.stop()

    def save_data(self):
        """Saves the data to disk. It opens a Dialog for selecting the directory. The default filename for
        the data is 'scan_data.dat'. The application model takes care of handling the saving itself.
        """
        #self.directory = str(QFileDialog.getExistingDirectory(self, "Select Directory", self.directory))
        filename = 'scan_data.dat'

        self.operator.save_scan_data(filename)

    def closeEvent(self, event):
        print('Closing')
        super().closeEvent(event)


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
    s = ScanWindow(e)
    s.show()
    app.exit(app.exec_())