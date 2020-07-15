__version__ = '0.1.1'

from pint import UnitRegistry
ureg = UnitRegistry()
Q_ = ureg.Quantity
import logging

# Set standard logging format and level.
# (To use this, do 'import labphew' in your module)
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)-8s: %(message)-40s  [%(lineno)d %(name)s]",
    datefmt='%H:%M:%S')

# Matplotlib uses the default logger and by setting the level to DEBUG in basicConfig, matplotlib will print a lot of
# debug statements. We prevent that by the logger used by matplotlib manually to level WARNING
logging.getLogger('matplotlib').setLevel(logging.WARNING)
