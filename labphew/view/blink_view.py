"""
Blink View
==========

An interactive window based on PyQt, used to show the elements of the GUI and test correct installation of the labphew
module and its dependencies.
This code can be used as a basis for building more complex user interfaces.
"""

import logging
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QSlider, QLabel, QAction
from PyQt5.QtGui import QFont, QIcon
from labphew.core.base.general_worker import WorkThread
from labphew.core.tools.gui_tools import fit_on_screen

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
    window.show()
    app.exit(app.exec_())