"""
Blink Window
==============
The simplest interactive window based on PyQt, used to show the elements of the GUI and test correct installation of the labphew module and its dependencies
"""

from PyQt5.QtCore import Qt, QThread, QTimer
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QSlider, QLabel
from PyQt5.QtGui import QFont

class StartWindow(QMainWindow):
    def __init__(self):

        self.central_widget = QWidget()
        self.button_start = QPushButton('Blink', self.central_widget)
        self.button_stop = QPushButton('Stop', self.central_widget)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1,10)

        self.message = QLabel('Press a button!', self.central_widget)
        self.message.setFont(QFont("Arial", 12, QFont.Normal))

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.button_start)
        self.layout.addWidget(self.button_stop)
        self.layout.addWidget(self.message)
        self.layout.addWidget(self.slider)
        self.setCentralWidget(self.central_widget)

        self.button_start.clicked.connect(self.start_blinking)
        self.button_stop.clicked.connect(self.stop_blinking)
        self.slider.valueChanged.connect(self.update_frequency)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_monitor)

        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.change_state)

        self.blinking = False
        self.blink_state = 0

    def start_blinking(self):
        self.blinking = True
        self.refresh_timer.start(30)
        self.blink_state = 1
        self.blink_timer.start(1000/self.slider.value())
        self.message.setText('blink! blink!')

    def stop_blinking(self):
        self.blinking = False
        self.blink_timer.killTimer()
        self.message.setText('blinking stopped!')
        self.message.setFont(QFont("Arial", 12, QFont.Normal))

    def change_state(self):
        self.blink_state = 1 - self.blink_state

    def refresh_monitor(self):
        if self.blinking:
            if self.blink_state:
                self.message.setFont(QFont("Arial", 12, QFont.Thin))
            else:
                self.message.setFont(QFont("Arial", 12, QFont.Bold))

    def update_frequency(self, value):
        if self.blinking:
            self.blink_timer.start(1000/self.slider.value())


if __name__ == '__main__':
    app = QApplication([])
    window = StartWindow()
    window.show()
    app.exit(app.exec_())