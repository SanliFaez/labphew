from labphew.Model.application.IVscan import Application

e = Application()
e.load_config('Config/application.yml')
e.load_daq()
e.do_scan()
e.save_scan_data('filename.txt')