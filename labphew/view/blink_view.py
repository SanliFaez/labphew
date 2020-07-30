"""
Blink View
==========

An interactive window based on PyQt, used to show the elements of the GUI and test correct installation of the labphew
module and its dependencies.
This code can be used as a basis for building more complex user interfaces.
"""


import logging
import labphew
import os
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import *  # QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QSlider, QLabel, QAction
from PyQt5.QtGui import QFont, QIcon
import pyqtgraph as pg
from labphew.core.base.general_worker import WorkThread
from labphew.core.tools.gui_tools import fit_on_screen, ModifyConfig

class MonitorWindow(QMainWindow):
    def __init__(self, operator, parent=None):
        self.logger = logging.getLogger(__name__)
        super().__init__()
        self.operator = operator
        self.scan_windows = {}  # If any scan windows are loaded, they will be placed in this dict
        self.set_UI()


        # create thread and timer objects for monitor
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_monitor)
        self.monitor_thread = WorkThread(self.operator._monitor_loop)

    def set_UI(self):

        self.setWindowTitle('labphew blinks at you')

        self.statusBar()  # Statusbar at the bottom of the screen
        ### The menu bar:
        self.mainMenu = self.menuBar()
        fileMenu = self.mainMenu.addMenu('&File')
        quit_action = QAction("E&xit", self, triggered=self.close, shortcut="Alt+F4", statusTip='Close the scan window')
        fileMenu.addAction(quit_action)


        self.central_widget = QWidget()
        self.button_start = QPushButton('Start Blink Monitor', self.central_widget)
        self.button_stop = QPushButton('Stop', self.central_widget)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 10)

        self.message = QLabel('Press a button!', self.central_widget)
        self.message.setFont(QFont("Arial", 12, QFont.Normal))

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.button_start)
        self.layout.addWidget(self.button_stop)
        self.layout.addWidget(self.message, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.slider)
        self.setCentralWidget(self.central_widget)

        self.button_start.clicked.connect(self.start_monitor)
        self.button_stop.clicked.connect(self.stop_monitor)
        self.slider.valueChanged.connect(self.blink_rate)

        self.slider.setValue(5)  # Setting the slider value will also invoke self.blink_rate(value), shich will set blink rate in the device
        # Note that another (better) approach would be to first retrieve the current setting from the device and set the
        # slider to that position.

    def start_monitor(self):
        """
        Called when start button is pressed.
        Starts the monitor (thread and timer) and disables some gui elements
        """
        if self.operator._busy:
            self.logger.debug("Operator is busy")
            return
        else:
            self.logger.debug('Starting monitor')
            self.operator._allow_monitor = True  # enable operator monitor loop to run
            self.monitor_thread.start()  # start the operator monitor
            self.monitor_timer.start(self.operator.properties['monitor']['gui_refresh_time'])  # start the update timer
            self.button_start.setEnabled(False)


    def stop_monitor(self):
        """
        Called when stop button is pressed.
        Stops the monitor:
        - flags the operator to stop
        - uses the Workthread stop method to wait a bit for the operator to finish, or terminate thread if timeout occurs
        """
        if not self.monitor_thread.isRunning():
            self.logger.debug('Monitor is not running')
            return
        else:
            # set flag to to tell the operator to stop:
            self.logger.debug('Stopping monitor')
            self.operator._stop = True
            self.operator._allow_monitor = False  # disable monitor again
            self.operator._busy = False  # Reset in case the monitor was not stopped gracefully, but forcefully stopped

    def blink_rate(self, value):
        low = self.operator.properties['blink instrument']['min_blink_period']
        high = self.operator.properties['blink instrument']['max_blink_period']
        self.operator.instrument.set_blink_period( value / 9 * (high-low) )

    def update_monitor(self):
        """
        Checks if new data is available and updates the gui.
        Checks if thread is still running and if not: stops timer (and reset gui elements)
        (called by timer)
        """
        if self.operator._new_monitor_data:
            self.operator._new_monitor_data = False
            blink_time, blink_state = self.operator._monitor_data
            self.message.setText(blink_time)
            if blink_state:
                self.message.setFont(QFont("Arial", 12, QFont.Bold))
                self.message.setStyleSheet("color: red;")
            else:
                self.message.setFont(QFont("Arial", 12, QFont.Thin))
                self.message.setStyleSheet("color: white;")

        if self.monitor_thread.isFinished():
            self.logger.debug('Monitor thread is finished')
            self.monitor_timer.stop()
            self.button_start.setEnabled(True)

    def load_scan_guis(self, scan_windows):
        """
        Load scan windows and add them to a menu in this monitor window.
        Note that the scan windows should be instantiated before adding them.
        The keys of the dictionary should be strings that will act as the names in the Scan menu.
        The values of the dictionary could be the ScanWindowObjects or a list that also contains some PyQt gui settings
        in a dictionary: [ScanWindowObject, {'shortcut':"Ctrl+Shift+V", 'statusTip':'Voltage sweep scan'}]

        :param scan_windows: scan windows dict
        :type scan_windows: dict
        """
        scanMenu = self.mainMenu.addMenu('&Scans')
        for name, scan_lst in scan_windows.items():
            if type(scan_lst) is not list:
                scan_lst = [scan_lst]
            if len(scan_lst) < 2:
                scan_lst.append({})
            self.scan_windows[name] = scan_lst
            scanMenu.addAction(QAction(name, self, triggered=self.open_scan_window, **scan_lst[1]))

    def open_scan_window(self):
        """
        This metohd is called by the menu and opens Scan Windows that were "attached" to this Monitor gui with load_scan_guis().
        """
        self.stop_monitor()
        name = self.sender().text()  # get the name of the QAction (which is also the key of the scanwindow dictionary)
        self.logger.debug('Opening scan window {}'.format(name))
        self.scan_windows[name][0].show()
        fit_on_screen(self.scan_windows[name][0])

    def closeEvent(self, event):
        """ Gets called when the window is closed. Could be used to do some cleanup before closing. """

        # # Use this bit to display an "Are you sure"-dialogbox
        # quit_msg = "Are you sure you want to exit labphew monitor?"
        # reply = QMessageBox.question(self, 'Message', quit_msg, QMessageBox.Yes, QMessageBox.No)
        # if reply == QMessageBox.No:
        #     event.ignore()
        #     return
        self.stop_monitor()  # stop monitor if it was running
        self.monitor_timer.stop()  # stop monitor timer, just to be sure
        # Close all child scan windows
        for scan_win in self.scan_windows.values():
            scan_win[0].close()
        # It would be good to also disconnect any devices here
        self.operator.instrument.disconnect()
        event.accept()


class ScanWindow(QMainWindow):
    def __init__(self, operator, parent=None):
        self.logger = logging.getLogger(__name__)
        super().__init__(parent)
        self.setWindowTitle('Blink Scan')
        self.operator = operator

        # # For loading a .ui file (created with QtDesigner):
        # p = os.path.dirname(__file__)
        # uic.loadUi(os.path.join(p, 'design/UI/main_window.ui'), self)

        self.set_UI()

        # create thread and timer objects for scan
        self.scan_timer = QTimer(timeout=self.update_scan)
        self.scan_thread = WorkThread(self.operator.do_scan)

    def set_UI(self):
        """
        Code-based generation of the user-interface based on PyQT
        """

        # display statusbar
        self.statusBar()
        ### The menu bar:
        mod_config_action = QAction("Con&fig", self, triggered=self.mod_scan_config, shortcut="Ctrl+Shift+C", statusTip='Modify the scan config')
        save_action = QAction("&Save", self, triggered=self.save, shortcut="Ctrl+S", statusTip='Save the scan data')
        quit_action = QAction("&Close", self, triggered=self.close, shortcut="Ctrl+W", statusTip='Close the scan window')



        self.start_action = QAction("&Start", self, triggered=self.start_scan, shortcut="F5", statusTip='Start the Scan')
        self.pause_action = QAction("&Pause", self, triggered=self.pause, shortcut="Ctrl+P", statusTip='Pause the scan', enabled=False)
        self.stop_action = QAction("S&top", self, triggered=self.stop, shortcut="Ctrl+A", statusTip='Stop the scan after current iteration', enabled=False)
        self.kill_action = QAction("&Kill", self, triggered=self.kill_scan, shortcut="Ctrl+K", statusTip='Immediately kill the scan')


        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(mod_config_action)
        fileMenu.addAction(save_action)
        fileMenu.addAction(quit_action)
        runMenu = mainMenu.addMenu('&Run Scan')
        runMenu.addAction(self.start_action)
        runMenu.addAction(self.pause_action)
        runMenu.addAction(self.stop_action)
        runMenu.addAction(self.kill_action)

        self.graph_win = pg.GraphicsWindow()
        self.graph_win.resize(800, 500)
        self.plot1 = self.graph_win.addPlot()
        self.curve1 = self.plot1.plot(pen='w')
        self.plot1.setLabel('bottom', 'data points')
        self.plot1.setLabel('left', 'state')

        self.setCentralWidget(self.graph_win)

        #
        #
        # ### General layout
        # central_widget = QWidget()
        # central_layout = QHBoxLayout(central_widget)
        #
        # # Layout for left hand controls
        # control_layout = QVBoxLayout()
        #
        # ### Scan box
        # self.box_scan = QGroupBox('Scan')
        # layout_scan = QVBoxLayout()
        # self.box_scan.setLayout(layout_scan)
        # control_layout.addWidget(self.box_scan)
        #
        # layout_scan_form = QFormLayout()
        # layout_scan.addLayout(layout_scan_form)
        # layout_scan_buttons = QHBoxLayout()
        # layout_scan.addLayout(layout_scan_buttons)
        #
        # self.scan_start_spinbox = QDoubleSpinBox(suffix='V', minimum=-100, singleStep=0.001, valueChanged=self.scan_start_value)
        # # self.scan_start_spinbox.valueChanged.connect(self.scan_start_value)
        #
        # self.scan_stop_spinbox = QDoubleSpinBox(suffix='V', minimum=-100, singleStep=0.001, valueChanged=self.scan_stop_value)
        #
        # self.scan_step_spinbox = QDoubleSpinBox(suffix='V', minimum=-100, singleStep=0.001, valueChanged=self.scan_step_value)
        #
        # self.scan_start_label = QLabel('start')
        # self.scan_stop_label = QLabel('stop')
        # self.scan_step_label = QLabel('step')
        # layout_scan_form.addRow(self.scan_start_label, self.scan_start_spinbox)
        # layout_scan_form.addRow(self.scan_stop_label, self.scan_stop_spinbox)
        # layout_scan_form.addRow(self.scan_step_label, self.scan_step_spinbox)
        #
        # self.start_button = QPushButton('Start', clicked=self.start_scan)
        # self.pause_button = QPushButton('Pause', clicked=self.pause)
        # self.stop_button = QPushButton('Stop', clicked=self.stop)
        # self.kill_button = QPushButton('Kill', clicked=self.kill_scan)
        # # Haven't decided what names are best. Suggestions:
        # # start, pause, interrupt, stop, abort, quit, kill
        #
        # layout_scan_buttons.addWidget(self.start_button)
        # layout_scan_buttons.addWidget(self.pause_button)
        # layout_scan_buttons.addWidget(self.stop_button)
        # layout_scan_buttons.addWidget(self.kill_button)
        #
        # ### Graphs:
        # self.graph_win = pg.GraphicsWindow()
        # self.graph_win.resize(1000, 600)
        # self.plot1 = self.graph_win.addPlot()
        # self.curve1 = self.plot1.plot(pen='y')
        #
        # # Add an empty widget at the bottom of the control layout to make layout nicer
        # dummy = QWidget()
        # dummy.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        # control_layout.addWidget(dummy)
        # # Add control layout and graph window to central layout and apply central layout to window
        # central_layout.addLayout(control_layout)
        # central_layout.addWidget(self.graph_win)
        # self.setCentralWidget(central_widget)
        #
        # self.apply_properties()
        # self.reset_fields()

    def mod_scan_config(self):
        """
        Open the Modify Config window for the scan properties
        """
        conf_win = ModifyConfig(self.operator.properties['scan'], apply_callback=None, parent=self)
        conf_win.show()

    # def apply_properties(self):
    #     """
    #     Apply properties dictionary to gui elements.
    #     """
    #     self.logger.debug('Applying config properties to gui elements')
    #     self.operator._set_scan_start(self.operator.properties['scan']['start'])  # this optional line checks validity
    #     self.scan_start_spinbox.setValue(self.operator.properties['scan']['start'])
    #
    #     self.operator._set_scan_stop(self.operator.properties['scan']['stop'])  # this optional line checks validity
    #     self.scan_stop_spinbox.setValue(self.operator.properties['scan']['stop'])
    #
    #     self.operator._set_scan_step(self.operator.properties['scan']['step'])  # this optional line checks validity
    #     self.scan_step_spinbox.setValue(self.operator.properties['scan']['step'])
    #
    #     if 'title' in self.operator.properties['scan']:
    #         self.box_scan.setTitle(self.operator.properties['scan']['title'])
    #         self.plot1.setTitle(self.operator.properties['scan']['title'])
    #
    #     self.plot1.setLabel('bottom', self.operator.properties['scan']['x_label'], units=self.operator.properties['scan']['x_units'])
    #     self.plot1.setLabel('left', self.operator.properties['scan']['y_label'], units=self.operator.properties['scan']['y_units'])
    #     self.plot1.setXRange(self.operator.properties['scan']['start'], self.operator.properties['scan']['stop'])
    #
    #     if 'filename' in self.operator.properties['scan']:
    #         self.saver.filename.setText(self.operator.properties['scan']['filename'])

    def save(self):
        try:
            fname = QFileDialog.getSaveFileName(self, 'Save data as', self.operator.properties['scan']['filename'],
                                                filter="netCDF4 (*.nc);;All Files (*.*)")
        except:
            fname = QFileDialog.getSaveFileName(self, 'Save data as', os.path.join(labphew.parent_path, 'data.nc'),
                                                filter="netCDF4 (*.nc);;All Files (*.*)")
        self.operator.save_scan(fname[0])

    # def scan_start_value(self):
    #     """
    #     Called when Scan Start spinbox is modified.
    #     Updates the parameter using a method of operator (which checks validity and also fixes the sign of step) and
    #     forces the (corrected) parameter in the gui elements
    #     """
    #     self.operator._set_scan_start(self.scan_start_spinbox.value())
    #     self.scan_start_spinbox.setValue(self.operator.properties['scan']['start'])
    #     self.scan_step_spinbox.setValue(self.operator.properties['scan']['step'])
    #     set_spinbox_stepsize(self.scan_start_spinbox)
    #     self.plot1.setXRange(self.operator.properties['scan']['start'], self.operator.properties['scan']['stop'])
    #
    # def scan_stop_value(self):
    #     """
    #     Called when Scan Stop spinbox is modified.
    #     Updates the parameter using a method of operator (which checks validity and also fixes the sign of step) and
    #     forces the (corrected) parameter in the gui elements
    #     """
    #     self.operator._set_scan_stop(self.scan_stop_spinbox.value())
    #     self.scan_stop_spinbox.setValue(self.operator.properties['scan']['stop'])
    #     self.scan_step_spinbox.setValue(self.operator.properties['scan']['step'])
    #     set_spinbox_stepsize(self.scan_stop_spinbox)
    #     self.plot1.setXRange(self.operator.properties['scan']['start'], self.operator.properties['scan']['stop'])
    #
    # def scan_step_value(self):
    #     """
    #     Called when Scan Step spinbox is modified.
    #     Updates the parameter using a method of operator (which checks validity) and forces the (corrected) parameter in the gui element
    #     """
    #     self.operator._set_scan_step(self.scan_step_spinbox.value())
    #     self.scan_step_spinbox.setValue(self.operator.properties['scan']['step'])
    #     set_spinbox_stepsize(self.scan_step_spinbox)

    def reset_fields(self):
        """
        Resets gui elements after a scan is finished, stopped or terminated.
        """
        self.start_action.setEnabled(True)
        self.pause_action.setEnabled(False)
        self.stop_action.setEnabled(False)
        self.pause_action.setText('Pause')
        self.operator._busy = False
        self.operator._pause = False
        self.operator._stop = False


        # self.start_button.setEnabled(True)
        # self.pause_button.setText('Pause')
        # self.pause_button.setEnabled(False)
        # self.stop_button.setEnabled(False)
        # self.scan_start_spinbox.setEnabled(True)
        # self.scan_stop_spinbox.setEnabled(True)
        # self.scan_step_spinbox.setEnabled(True)
        # # Reset all flow control flags
        # self.operator._busy = False
        # self.operator._pause = False
        # self.operator._stop = False

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
            self.start_action.setEnabled(False)
            self.pause_action.setEnabled(True)
            self.stop_action.setEnabled(True)

            # self.start_button.setEnabled(False)
            # self.pause_button.setEnabled(True)
            # self.stop_button.setEnabled(True)
            # self.operator._stop = False  # enable operator monitor loop to run
            self.scan_thread.start()  # start the operator monitor
            # Start the update timer with time specified in config if available
            try:
                self.scan_timer.start(self.operator.properties['scan']['gui_refresh_time'])
            except:
                self.scan_timer.start(0.05)  # otherwise use default value
            # self.scan_start_spinbox.setEnabled(False)
            # self.scan_stop_spinbox.setEnabled(False)
            # self.scan_step_spinbox.setEnabled(False)

    def pause(self):
        """
        Called when pause button is clicked.
        Signals the operator scan to pause. Updates buttons accordingly
        """
        if not self.operator._pause:
            self.operator._pause = True
            self.pause_action.setText('&Continue')
        else:
            self.operator._pause = False
            self.pause_action.setText('Pause')

    def stop(self):
        """
        Stop all loop threads:
        - flags the operator to stop
        - uses the Workthread stop method to wait a bit for the operator to finish, or terminate thread if timeout occurs
        """
        self.logger.debug('Stopping operator')
        # self.stop_button.setEnabled(False)
        self.operator._stop = True
        if self.scan_thread.isRunning():
            self.scan_thread.stop()  # Stop thread with default timeout before killing it
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
            self.curve1.setData(self.operator.point_number, self.operator.measured_state)
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
        self.scan_timer.stop()  # stop scan timer, just to be sure
        # perhaps also disconnect devices
        event.accept()






if __name__ == '__main__':
    from labphew.controller.blink_controller import BlinkController
    from labphew.model.blink_model import BlinkOperator

    instr = BlinkController()
    opr = BlinkOperator(instr)
    opr.load_config()

    app = QApplication([])
    app_icon = QIcon("../view/design/Icons/labphew_icon.png")
    app.setWindowIcon(app_icon)
    window = MonitorWindow(opr)

    scan_window = ScanWindow(opr, parent = window)
    scan_window.show()
    fit_on_screen(scan_window)
    # scans = {
    #     'Example scan 1': scan_window
    # }
    # window.load_scan_guis(scans)
    # window.show()
    app.exit(app.exec_())