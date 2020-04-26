# coding=utf-8
"""
    start_gui
"""

import sys
from PyQt5.QtWidgets import QApplication

from labphew.Model.application import IVscan_aquic as IVscan
from labphew.View.scan_window import ScanWindow

e = IVscan.Operator
e.load_config('Config/experiment_dummy.yml')
e.load_daq()

ap = QApplication(sys.argv)
m = ScanWindow(e)
m.show()
ap.exit(ap.exec_())