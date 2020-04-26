from labphew.Model.application.blink import Operator

e = Operator()
e.load_config('Config/application.yml')
e.load_daq()
e.do_scan()
e.save_scan_data('filename.txt')