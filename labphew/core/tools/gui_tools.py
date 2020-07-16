"""
GUI Tools
=========

Collection of tools that might be helpful for GUIs

"""

import numpy as np
from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox


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