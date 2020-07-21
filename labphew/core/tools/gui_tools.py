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
    """ Helper function that sets the stepsize of a spinbox to one order of magnitude below current value. """
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
    """
    Simple widget for saving, consisting of a line edit to enter the filename and a save button.
    It overwrites existing files without confirmation, but the line edit turns red to warn the user that the file exists.
    """
    def __init__(self, save_button_callback):
        """
        Create the saver widget. The saving method (of the operator) needs to be passed as argument.

        :param save_button_callback: the saving method to call
        :type save_button_callback: method
        """
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
        """ Calls the saving method (of operator) and then calls check_file_exists to turn the filename red."""
        self.__save_button_callback(self.filename.text())
        self.check_file_exists()

    def check_file_exists(self):
        """ Makes the filename line edit red if file exists, or black otherwise."""
        if os.path.exists(self.filename.text()):
            self.filename.setStyleSheet("color: red;")
        else:
            self.filename.setStyleSheet("color: black;")


class ModifyConfig(QDialog):
    """
    Window to modify any dictionary as if it were yaml text.
    Note that for a gui it is useful to update the gui elements affected by the changes. For that purpose the parent gui
    can pass an update method to this window through apply_callback.
    """

    def __init__(self, properties_dict, apply_callback=None, parent=None):
        """
        Create the Modify Config window.

        :param properties_dict: dictionary to be modified
        :type properties_dict: dict
        :param apply_callback: optional method to be called by apply button after updating the dictionary
        :type apply_callback: method (or None)
        :param parent: The parent window
        :type parent: QtWidget


        """
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating Modify Config window')
        super().__init__(parent=parent)
        self.resize(1000, 790)
        self._parent = parent
        self.apply_callback = apply_callback
        # self.apply_props = apply
        self.font = QFont("Courier New", 11)
        self.properties_dict = properties_dict
        self.initUI()
        self.reset_text()

    def initUI(self):
        """Create the GUI layout"""
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
        """
        Sets the correct enabled state of buttons after the text field has changed. (Is called after every change).

        Note:
        It also checks if the yaml is valid after every change (and sets button state accordingly). If that turns out to
        be too intensive, there's a suggestion for modification in the source code.
        """
        self.button_reset.setEnabled(True)
        self.button_apply.setEnabled(self.valid_yaml())
        # It might be a bit intensive to continuously check if the whole text is valid yaml.
        # If that turns out to be the case, just change it to:
        # self.button_apply.setEnabled(True)

    def reset_text(self):
        """Called by reset button. Resets the text field to the original dictionary and resets the buttons accordingly."""
        self.txt.setText(yaml.dump(self.properties_dict))
        self.button_reset.setEnabled(False)
        self.button_apply.setEnabled(False)

    def valid_yaml(self, quiet=True):
        """
        Checks if text in input field can be interpreted as valid yaml.
        Returns True for valid yaml, False otherwise
        If optional keyword quiet is set to False it will also display a warning pop-up.

        :param quiet: flag to suppress the warning pop-up (default: True)
        :type quiet: bool
        :return: yaml validity
        :rtype: bool
        """
        try:
            self._list = yaml.safe_load(self.txt.toPlainText())
            return True
        except yaml.YAMLError as exc:
            if not quiet:
                QMessageBox.warning(self, 'Invalid YAML', str(exc), QMessageBox.Ok)
            return False

    def apply(self):
        """
        Called by apply button.
        Converts the text window to dictionary (using yaml) and updates the original dictionary.
        If a apply_callback was supplied it will attempt to execute it.
        """
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
            self.properties_dict.update(dic)
            if self.apply_callback is not None:
                try:
                    self.apply_callback()
                except:
                    self.logger.error('Apply callback caused unexpected exception')
                    QMessageBox.warning(self, 'Error', 'Apply callback caused unexpected exception', QMessageBox.Ok)
                    return
            self.close()
