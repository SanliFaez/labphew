"""
GUI Tools
=========

Collection of tools that might be helpful for GUIs

"""

import numpy as np
from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox, QWidget, QHBoxLayout, QLineEdit, QPushButton
import os.path

def set_spinbox_stepsize(spinbox):
    """helper function that sets the stepsize of a spinbox to one order of magnitude below current value"""
    if type(spinbox) is QDoubleSpinBox:
        min_pow = - spinbox.decimals()
    elif type(spinbox) is QSpinBox:
        min_pow = 0
    else:
        return
    if spinbox.value() == 0:
        p = min_pow
    else:
        p = max(min_pow, int(np.floor(np.log10(np.abs(spinbox.value()))))-1)
    spinbox.setSingleStep(10 ** p)

class SaverWidget(QWidget):
    def __init__(self, save_button_callback):
        super().__init__()
        self.__save_button_callback = save_button_callback
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.filename = QLineEdit(r'C:\Temp\data.nc')
        self.filename.textChanged.connect(self.check_file_exists)
        self.check_file_exists()
        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save)
        layout.addWidget(self.filename)
        layout.addWidget(self.save_button)

    def save(self):
        self.__save_button_callback(self.filename.text())
        self.check_file_exists()

    def check_file_exists(self):
        if os.path.exists(self.filename.text()):
            self.filename.setStyleSheet("color: red;")
        else:
            self.filename.setStyleSheet("color: black;")
