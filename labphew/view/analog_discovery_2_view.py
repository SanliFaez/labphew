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
from PyQt5.QtWidgets import * # QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QSlider, QLabel, QMessageBox
from PyQt5.QtGui import QFont, QIcon

from labphew.core.base.general_worker import WorkThread

import logging

# TODO: the following imports are necessary for child windows, they have to be adjusted and tested
#from .config_view import ConfigWindow  # to adjust experiment parameters
#from .scan_view import ScanWindow      # to perform single scan


class MonitorWindow(QMainWindow):
    def __init__(self, operator, parent=None):
        self.logger = logging.getLogger(__name__)
        super().__init__(parent)

        self.operator = operator
        self.refresh_time = 100

        self.setWindowTitle('labphew monitor')
        self.set_UI()

        # p = os.path.dirname(__file__)
        # uic.loadUi(os.path.join(p, 'design/UI/main_window.ui'), self)


        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_monitor)

        self.monitor_thread = WorkThread(self.operator._monitor_loop)

        # self.running_monitor = False
        #
        # self.button_start.clicked.connect(self.start_monitor)
        # self.button_stop.clicked.connect(self.stop_monitor)

        self.show()

        # TODO: uncomment for testing the child windows
        # self.config_window = ConfigWindow(operator, parent=self)
        # self.config_window.propertiesChanged.connect(self.update_properties)
        # self.actionConfig.triggered.connect(self.config_window.show)
        #
        # self.scan_window = ScanWindow(operator)
        # self.actionScan.triggered.connect(self.scan_window.show)

    def set_UI(self):
        """
        code-based generation of the user-interface based on PyQT
        """

        ### Graphs:
        self.graph_win = pg.GraphicsWindow()
        self.graph_win.resize(1000, 600)


        self.plot1 = self.graph_win.addPlot()
        self.curve1 = self.plot1.plot(pen='y')
        self.graph_win.nextRow()
        self.plot2 = self.graph_win.addPlot()
        self.curve2 = self.plot2.plot(pen='c')
        # self.plot2.hide()

        control_layout = QVBoxLayout()

        ### Analog Out
        box_ao = QGroupBox('Analog Out')
        layout_ao = QFormLayout()
        box_ao.setLayout(layout_ao)
        control_layout.addWidget(box_ao)

        self.ao1_spinbox = QDoubleSpinBox()
        self.ao1_spinbox.setSuffix('V')
        self.ao1_spinbox.setMinimum(-100)  # limits are checked by the Operator
        self.ao1_spinbox.valueChanged.connect(self.ao1_value)
        self.ao1_spinbox.setSingleStep(0.1)

        self.ao2_spinbox = QDoubleSpinBox()
        self.ao2_spinbox.setSuffix('V')
        self.ao2_spinbox.setMinimum(-100)  # limits are checked by the Operator
        self.ao2_spinbox.valueChanged.connect(self.ao2_value)
        self.ao2_spinbox.setSingleStep(0.1)

        self.ao1_label = QLabel()
        self.ao2_label = QLabel()
        layout_ao.addRow(self.ao1_label, self.ao1_spinbox)
        layout_ao.addRow(self.ao2_label, self.ao2_spinbox)


        ### Monitor
        box_monitor = QGroupBox('Monitor')
        layout_monitor = QFormLayout()
        box_monitor.setLayout(layout_monitor)
        control_layout.addWidget(box_monitor)

        self.time_step_spinbox = QDoubleSpinBox()
        self.time_step_spinbox.setSuffix('s')
        self.time_step_spinbox.setMinimum(.01)
        self.time_step_spinbox.valueChanged.connect(self.time_step)
        self.time_step_spinbox.setSingleStep(0.01)
        layout_monitor.addRow(QLabel('Time step'), self.time_step_spinbox)

        self.plot_points_spinbox = QSpinBox()
        self.plot_points_spinbox.setMinimum(2)
        self.plot_points_spinbox.setMaximum(1000)
        self.plot_points_spinbox.valueChanged.connect(self.plot_points)
        self.plot_points_spinbox.setSingleStep(10)
        layout_monitor.addRow(QLabel('Plot points'), self.plot_points_spinbox)

        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.start_monitor)
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_monitor)
        layout_monitor.addRow(self.start_button, self.stop_button)

        ### General layout
        central_widget = QWidget()
        central_layout = QHBoxLayout(central_widget)

        central_layout.addLayout(control_layout)
        central_layout.addWidget(self.graph_win)

        self.setCentralWidget(central_widget)

        # self.ai_combo = QComboBox(items=['together', 'Ch1', 'Ch2', 'both'])

        #
        # self.layout.addWidget(self.button_start)
        # self.layout.addWidget(self.button_stop)
        self.apply_properties(self.operator.properties)


    def apply_properties(self, props):
        self.ao1_label.setText(props['ao'][1]['name'])
        self.ao2_label.setText(props['ao'][2]['name'])

        self.time_step_spinbox.setValue(props['monitor']['time_step'])
        self.plot_points_spinbox.setValue(props['monitor']['plot_points'])

        self.plot1.setTitle(props['monitor'][1]['name'])
        self.plot2.setTitle(props['monitor'][2]['name'])

    def ao1_value(self):
        value = self.operator.analog_out(1, self.ao1_spinbox.value())
        self.ao1_spinbox.setValue(value)

    def ao2_value(self):
        value = self.operator.analog_out(2, self.ao2_spinbox.value())
        self.ao2_spinbox.setValue(value)

    def time_step(self):
        self.operator._set_monitor_time_step(self.time_step_spinbox.value())
        self.time_step_spinbox.setValue(self.operator.properties['monitor']['time_step'])

    def plot_points(self):
        self.operator._set_monitor_plot_points(self.plot_points_spinbox.value())
        self.plot_points_spinbox.setValue(self.operator.properties['monitor']['plot_points'])



    def start_monitor(self):
        if self.monitor_thread.isRunning():
            self.logger.debug("Monitor is already running")
            return
        else:
            self.operator._stop_monitor = False  # enable operator monitor loop to run
            self.monitor_thread.start()  # start the operator monitor
            self.monitor_timer.start(self.operator.properties['monitor']['gui_refresh_time'])  # start the update timer
            self.plot_points_spinbox.setEnabled(False)
            self.start_button.setEnabled(False)

    def stop_monitor(self):
        if not self.monitor_thread.isRunning():
            self.logger.debug('Monitor is not running')
            return
        else:
            # set flag to to tell the operator to stop:
            self.operator._stop_monitor = True
            self.monitor_thread.stop(self.operator.properties['monitor']['stop_timeout'])

    def update_monitor(self):
        if self.monitor_thread.isFinished():
            self.logger.debug('monitor_thread is finished')
            self.monitor_timer.stop()
            self.plot_points_spinbox.setEnabled(True)
            self.start_button.setEnabled(True)
        elif self.operator._new_monitor_data:
            self.operator._new_monitor_data = False
            self.curve1.setData(self.operator.analog_monitor_time, self.operator.analog_monitor_1)
            self.curve2.setData(self.operator.analog_monitor_time, self.operator.analog_monitor_2)



    # def update_monitor(self):
    #     """
    #     This method is called through a timer. It updates the data displayed in the main plot.
    #     """
    #     if self.operator.new_data:
    #         self.plot.setData(xdata, ydata)
    #     msg = self.operator.main_loop()
    #     self.message.setText(msg)
    #     # self.plot.setData(xdata, ydata)


    def closeEvent(self, event):
        # # Use this bit to display an "Are you sure"-dialogbox
        # quit_msg = "Are you sure you want to exit labphew monitor?"
        # reply = QMessageBox.question(self, 'Message', quit_msg, QMessageBox.Yes, QMessageBox.No)
        # if reply == QMessageBox.No:
        #     event.ignore()
        #     return
        self.stop_monitor()  # stop monitor if it was running
        # perhaps also disconnect devices
        event.accept()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)  # Change root logging level

    import sys
    from PyQt5.QtWidgets import QApplication
    from labphew.model.analog_discovery_2_model import Operator

    # To use with real device
    # from labphew.controller.digilent.waveforms import DfwController

    # To test with simulated device
    from labphew.controller.digilent.waveforms import SimulatedDfwController as DfwController




    instrument = DfwController()
    opr = Operator(instrument)
    opr.load_config()

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
    gui = MonitorWindow(opr)
    app.exit(app.exec_())