"""
Analog Discovery 2 Scan Example
===============================

ScanWindow class to configure and display a scan from Analog Discovery 2 Operator.
All the processes that are not relating to user interaction are handled by the Operator class in the model folder.

To change parameters the user needs to open the configuration window.  ??????

For inspiration: the initiation of scan_view routines can be implemented as buttons on the monitor_view
TODO:
    - build the UI without a design file necessary
    - connect the UI parameters to config file

"""

import pyqtgraph as pg   # used for additional plotting features
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import * # QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QSlider, QLabel, QMessageBox
from PyQt5.QtGui import QFont, QIcon
import logging

from labphew.core.tools.gui_tools import set_spinbox_stepsize, SaverWidget, ModifyConfig
from labphew.core.base.general_worker import WorkThread

# TODO: the following imports are necessary for child windows, they have to be adjusted and tested
#from .config_view import ConfigWindow  # to adjust experiment parameters
#from .scan_view import ScanWindow      # to perform single scan


class ScanWindow(QMainWindow):
    def __init__(self, operator, monitor=None, parent=None):
        self.logger = logging.getLogger(__name__)
        super().__init__(parent)
        self.setWindowTitle('Analog Discovery 2')
        self.operator = operator
        self.monitor = monitor

        # # For loading a .ui file (created with QtDesigner):
        # p = os.path.dirname(__file__)
        # uic.loadUi(os.path.join(p, 'design/UI/main_window.ui'), self)

        self.set_UI()

        # create thread and timer objects for scan
        self.scan_timer = QTimer(timeout=self.update_scan)
        self.scan_thread = WorkThread(self.operator.do_scan)

        # self.show()  # display the GUI

        # TODO: uncomment for testing the child windows
        # self.config_window = ConfigWindow(operator, parent=self)
        # self.config_window.propertiesChanged.connect(self.update_properties)
        # self.actionConfig.triggered.connect(self.config_window.show)
        #
        # self.scan_window = ScanWindow(operator)
        # self.actionScan.triggered.connect(self.scan_window.show)

    def set_UI(self):
        """
        Code-based generation of the user-interface based on PyQT
        """

        # display statusbar
        self.statusBar()
        ### The menu bar:
        mod_config_action = QAction("&Config", self, triggered=self.mod_scan_config, shortcut="Ctrl+Shift+C", statusTip='Modify the scan config')
        quit_action = QAction("&Quit", self, triggered=self.close, shortcut="Ctrl+Q", statusTip='Close the scan window')

        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(mod_config_action)
        fileMenu.addAction(quit_action)

        ### General layout
        central_widget = QWidget()
        central_layout = QHBoxLayout(central_widget)

        # Layout for left hand controls
        control_layout = QVBoxLayout()

        ### Scan box
        self.box_scan = QGroupBox('Scan')
        layout_scan = QVBoxLayout()
        self.box_scan.setLayout(layout_scan)
        control_layout.addWidget(self.box_scan)

        layout_scan_form = QFormLayout()
        layout_scan.addLayout(layout_scan_form)
        layout_scan_buttons = QHBoxLayout()
        layout_scan.addLayout(layout_scan_buttons)

        self.scan_start_spinbox = QDoubleSpinBox(suffix='V', minimum=-100, singleStep=0.001, valueChanged=self.scan_start_value)
        # self.scan_start_spinbox.valueChanged.connect(self.scan_start_value)

        self.scan_stop_spinbox = QDoubleSpinBox(suffix='V', minimum=-100, singleStep=0.001, valueChanged=self.scan_stop_value)

        self.scan_step_spinbox = QDoubleSpinBox(suffix='V', minimum=-100, singleStep=0.001, valueChanged=self.scan_step_value)

        self.scan_start_label = QLabel('start')
        self.scan_stop_label = QLabel('stop')
        self.scan_step_label = QLabel('step')
        layout_scan_form.addRow(self.scan_start_label, self.scan_start_spinbox)
        layout_scan_form.addRow(self.scan_stop_label, self.scan_stop_spinbox)
        layout_scan_form.addRow(self.scan_step_label, self.scan_step_spinbox)

        self.start_button = QPushButton('Start', clicked=self.start_scan)
        self.pause_button = QPushButton('Pause', clicked=self.pause)
        self.stop_button = QPushButton('Stop', clicked=self.stop)
        self.kill_button = QPushButton('Kill', clicked=self.kill_scan)
        # Haven't decided what names are best. Suggestions:
        # start, pause, interrupt, stop, abort, quit, kill

        layout_scan_buttons.addWidget(self.start_button)
        layout_scan_buttons.addWidget(self.pause_button)
        layout_scan_buttons.addWidget(self.stop_button)
        layout_scan_buttons.addWidget(self.kill_button)

        self.saver = SaverWidget(self.save)
        layout_scan.addWidget(self.saver)

        ### Graphs:
        self.graph_win = pg.GraphicsWindow()
        self.graph_win.resize(1000, 600)
        self.plot1 = self.graph_win.addPlot()
        self.curve1 = self.plot1.plot(pen='y')

        # Add an empty widget at the bottom of the control layout to make layout nicer
        dummy = QWidget()
        dummy.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        control_layout.addWidget(dummy)
        # Add control layout and graph window to central layout and apply central layout to window
        central_layout.addLayout(control_layout)
        central_layout.addWidget(self.graph_win)
        self.setCentralWidget(central_widget)

        self.apply_properties()
        self.reset_fields()

    def mod_scan_config(self):
        """
        Open the Modify Config window for the scan properties
        """
        conf_win = ModifyConfig(self.operator.properties['scan'], apply_callback=self.apply_properties, parent=self)
        conf_win.show()

    def apply_properties(self):
        """
        Apply properties dictionary to gui elements.
        """
        self.logger.debug('Applying config properties to gui elements')
        self.operator._set_scan_start(self.operator.properties['scan']['start'])  # this optional line checks validity
        self.scan_start_spinbox.setValue(self.operator.properties['scan']['start'])

        self.operator._set_scan_stop(self.operator.properties['scan']['stop'])  # this optional line checks validity
        self.scan_stop_spinbox.setValue(self.operator.properties['scan']['stop'])

        self.operator._set_scan_step(self.operator.properties['scan']['step'])  # this optional line checks validity
        self.scan_step_spinbox.setValue(self.operator.properties['scan']['step'])

        if 'title' in self.operator.properties['scan']:
            self.box_scan.setTitle(self.operator.properties['scan']['title'])
            self.plot1.setTitle(self.operator.properties['scan']['title'])

        self.plot1.setLabel('bottom', self.operator.properties['scan']['x_label'], units=self.operator.properties['scan']['x_units'])
        self.plot1.setLabel('left', self.operator.properties['scan']['y_label'], units=self.operator.properties['scan']['y_units'])
        self.plot1.setXRange(self.operator.properties['scan']['start'], self.operator.properties['scan']['stop'])

        if 'filename' in self.operator.properties['scan']:
            self.saver.filename.setText(self.operator.properties['scan']['filename'])

    def save(self, filename):
        self.operator.save_scan(filename)

    def scan_start_value(self):
        """
        Called when Scan Start spinbox is modified.
        Updates the parameter using a method of operator (which checks validity and also fixes the sign of step) and
        forces the (corrected) parameter in the gui elements
        """
        self.operator._set_scan_start(self.scan_start_spinbox.value())
        self.scan_start_spinbox.setValue(self.operator.properties['scan']['start'])
        self.scan_step_spinbox.setValue(self.operator.properties['scan']['step'])
        set_spinbox_stepsize(self.scan_start_spinbox)
        self.plot1.setXRange(self.operator.properties['scan']['start'], self.operator.properties['scan']['stop'])

    def scan_stop_value(self):
        """
        Called when Scan Stop spinbox is modified.
        Updates the parameter using a method of operator (which checks validity and also fixes the sign of step) and
        forces the (corrected) parameter in the gui elements
        """
        self.operator._set_scan_stop(self.scan_stop_spinbox.value())
        self.scan_stop_spinbox.setValue(self.operator.properties['scan']['stop'])
        self.scan_step_spinbox.setValue(self.operator.properties['scan']['step'])
        set_spinbox_stepsize(self.scan_stop_spinbox)
        self.plot1.setXRange(self.operator.properties['scan']['start'], self.operator.properties['scan']['stop'])

    def scan_step_value(self):
        """
        Called when Scan Step spinbox is modified.
        Updates the parameter using a method of operator (which checks validity) and forces the (corrected) parameter in the gui element
        """
        self.operator._set_scan_step(self.scan_step_spinbox.value())
        self.scan_step_spinbox.setValue(self.operator.properties['scan']['step'])
        set_spinbox_stepsize(self.scan_step_spinbox)

    def reset_fields(self):
        """
        Resets gui elements after a scan is finished, stopped or terminated.
        """
        self.start_button.setEnabled(True)
        self.pause_button.setText('Pause')
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.scan_start_spinbox.setEnabled(True)
        self.scan_stop_spinbox.setEnabled(True)
        self.scan_step_spinbox.setEnabled(True)
        # Reset all flow control flags
        self.operator._busy = False
        self.operator._pause = False
        self.operator._stop = False

    def start_scan(self):
        """
        Called when start button is pressed.
        Starts the monitor (thread and timer) and disables some gui elements
        """
        if self.operator._busy:
            self.logger.debug("Operator is busy")
            return
        else:
            self.logger.debug('Starting scan')
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            # self.operator._stop = False  # enable operator monitor loop to run
            self.scan_thread.start()  # start the operator monitor
            self.scan_timer.start(self.operator.properties['scan']['gui_refresh_time'])  # start the update timer
            self.scan_start_spinbox.setEnabled(False)
            self.scan_stop_spinbox.setEnabled(False)
            self.scan_step_spinbox.setEnabled(False)

    def pause(self):
        """
        Called when pause button is clicked.
        Signals the operator scan to pause. Updates buttons accordingly
        """
        if not self.operator._pause:
            self.operator._pause = True
            self.pause_button.setText('Continue')
        else:
            self.operator._pause = False
            self.pause_button.setText('Pause')

    def stop(self):
        """
        Stop all loop threads:
        - flags the operator to stop
        - uses the Workthread stop method to wait a bit for the operator to finish, or terminate thread if timeout occurs
        """
        self.logger.debug('Stopping operator')
        self.stop_button.setEnabled(False)
        self.operator._stop = True
        if self.scan_thread.isRunning():
            self.scan_thread.stop(self.operator.properties['scan']['stop_timeout'])
        self.operator._busy = False  # Reset in case the monitor was not stopped gracefully, but forcefully stopped
        self.reset_fields()

    def kill_scan(self):
        """
        Forcefully terminates the scan thread
        """
        self.logger.debug('Killing operator threads')
        self.operator._stop = True
        self.scan_thread.terminate()
        self.reset_fields()

    def update_scan(self):
        """
        Checks if new data is available and updates the graph.
        Checks if thread is still running and if not: stops timer and reset gui elements
        (called by timer)
        """
        if self.operator._new_scan_data:
            self.operator._new_scan_data = False
            self.curve1.setData(self.operator.scan_voltages, self.operator.measured_voltages)
        if self.scan_thread.isFinished():
            self.logger.debug('Scan thread is finished')
            self.scan_timer.stop()
            self.reset_fields()

    def closeEvent(self, event):
        """ Gets called when the window is closed. Could be used to do some cleanup before closing. """

        # # Use this bit to display an "Are you sure"-dialogbox
        # quit_msg = "Are you sure you want to exit labphew monitor?"
        # reply = QMessageBox.question(self, 'Message', quit_msg, QMessageBox.Yes, QMessageBox.No)
        # if reply == QMessageBox.No:
        #     event.ignore()
        #     return
        self.stop()  # stop scan
        self.scan_timer.stop()  # stop monitor timer, just to be nice
        # perhaps also disconnect devices
        event.accept()


if __name__ == "__main__":
    import labphew  # import this to use labphew style logging

    import sys
    from PyQt5.QtWidgets import QApplication
    from labphew.model.analog_discovery_2_model import Operator


    # To use with real device
    # from labphew.controller.digilent.waveforms import DfwController

    # To test with simulated device
    from labphew.controller.digilent.waveforms import SimulatedDfwController as DfwController

    from labphew.view.analog_discovery_2_view import MonitorWindow

    instrument = DfwController()
    opr = Operator(instrument)
    opr.load_config()

    app = QApplication(sys.argv)
    monitor_gui = MonitorWindow(opr)
    gui = ScanWindow(opr, monitor_gui)
    gui.show()
    app.exit(app.exec_())
    app.closeAllWindows()  # close any child window that might have been open


    # An example to read and display the data:
    import xarray as xr

    # manually enter the path to the file here, or grab it from the scan properties
    # filename = r'C:\Temp\Example scan.nc'
    filename = opr.properties['scan']['filename']

    dat = xr.load_dataset(filename)

    # To get a feeling for what's possible with xarray dataset, try the following things in an interactive python console:
    # (Note that if you only execute one line you don't need the print statement to see the output)

    print(dat)
    print(dat.measured_voltage)
    print(dat.measured_voltage.dims)
    print(dat.measured_voltage.coords)
    print(dat.measured_voltage.units)
    print(dat.measured_voltage.values)
    print(dat.scan_voltage)
    print(dat.scan_voltage.units)
    print(dat.scan_voltage.values)

    print(dat.attrs)

    dat.measured_voltage[10:20]

    print(dat.measured_voltage.isel(scan_voltage=2))  # 2nd point
    print(dat.measured_voltage[dict(scan_voltage=2)])  # alternative

    print(dat.measured_voltage.sel(scan_voltage=2.0))  # where scan_voltage == 2.0
    print(dat.measured_voltage.sel(scan_voltage=slice(0, 1.0))) # for scan_voltage in range 0 to 1.0

    # See also http://xarray.pydata.org/en/stable/indexing.html

    # # Note, in pycharm using both pyqt(graph) and matplotlib seems to cause trouble, but it works from command line.
    # # In the end, opening data and inspecting it should not happen in the same file as controlling the measurement.
    # import matplotlib.pyplot as plt
    # dat.measured_voltage.plot()
    # plt.show()

