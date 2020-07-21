"""
GUI Tools
=========

Collection of tools that might be helpful for GUIs

"""
import logging
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import os.path
import yaml

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





class ModifyConfig(QDialog):

    def __init__(self, properties_dict, parent):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating Modify Config window')
        super().__init__(parent)
        self.resize(1000, 790)
        self._parent = parent
        self.font = QFont("Courier New", 11)
        self.properties_dict = properties_dict
        self.initUI()
        self.reset_text()

    def initUI(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        # create buttons, labels and the textedit:
        self.button_apply = QPushButton('&Apply', clicked=self.apply)
        self.button_reset = QPushButton('&Reset', clicked = self.reset_text)
        self.button_cancel = QPushButton('&Cancel', clicked = self.close)

        self.txt = QTextEdit()
        self.txt.setLineWrapMode(QTextEdit.NoWrap)
        self.txt.setFont(self.font)
        self.txt.textChanged.connect(self.changed)

        button_layout.addWidget(self.button_apply)
        button_layout.addWidget(self.button_reset)
        button_layout.addWidget(self.button_cancel)
        main_layout.addWidget(self.txt)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def changed(self):
        self.button_reset.setEnabled(True)
        self.button_apply.setEnabled(self.valid_yaml())
        # It might be a bit intensive to continuously check if the whole text is valid yaml.
        # If that turns out to be the case, just change it to:
        # self.button_apply.setEnabled(True)

    def reset_text(self):
        self.txt.setText(yaml.dump(self.properties_dict))
        self.button_reset.setEnabled(False)
        self.button_apply.setEnabled(False)

    def valid_yaml(self, quiet=True):
        try:
            self._list = yaml.safe_load(self.txt.toPlainText())
            return True
        except yaml.YAMLError as exc:
            if not quiet:
                QMessageBox.warning(self, 'Invalid YAML', str(exc), QMessageBox.Ok)
            return False

    def apply(self):
        if self.valid_yaml(False):
            try:
                # self.logger.debug('Converting text to dictionary')
                dic = yaml.safe_load(self.txt.toPlainText())
                if type(dic) is not dict:
                    raise
            except:
                self.logger.error('Converting text to dictionary failed')
                QMessageBox.warning(self, 'Reading YAML failed', 'Error while converting yaml to dictionary', QMessageBox.Ok)
                return
            try:
                self.properties_dict.update(dic)
                if not hasattr(self._parent, 'apply_properties'):
                    self.logger.warning("Parent GUI not specified or doesn't have apply_properties method")
                self._parent.apply_properties()
            except:
                self.logger.error('Call apply_properties from parent GUI was unsuccessful')
                QMessageBox.warning(self, 'Error', 'To update properties the parent GUI should have a method apply_properties', QMessageBox.Ok)
                return
            self.close()
