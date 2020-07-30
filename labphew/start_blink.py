import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from labphew.controller.blink_controller import BlinkController
from labphew.model.blink_model import BlinkOperator
from labphew.view.blink_view import MonitorWindow, ScanWindow

def main():

    if len(sys.argv) == 2:
        config_file = sys.argv[1]  # get default_configs file from command line
    else:
        config_file = None          # or place manual path to default_configs file here or use None for default built in default_configs file
        print('Using default default_configs file {}'.format(config_file))


    instr = BlinkController()
    opr = BlinkOperator(instr)

    opr.load_config( config_file )

    app = QApplication([])
    app_icon = QIcon("../view/design/Icons/labphew_icon.png")
    app.setWindowIcon(app_icon)
    main_gui = MonitorWindow(opr)

    scan_gui = ScanWindow(opr, parent=main_gui)
    # fit_on_screen(scan_window)
    scans = {
        'Example scan 1': scan_gui
    }
    main_gui.load_scan_guis(scans)
    main_gui.show()
    app.exit(app.exec_())


if __name__ == '__main__':
    main()