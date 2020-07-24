__version__ = '0.1.1'

import os
package_path = os.path.dirname(os.path.abspath(__file__))
repository_path = os.path.abspath(os.path.join(package_path, os.pardir))
parent_path = os.path.abspath(os.path.join(repository_path, os.pardir))

from pint import UnitRegistry
ureg = UnitRegistry()
Q_ = ureg.Quantity
import logging

# Set standard logging format and level.
# (To use this, do 'import labphew' in your module)
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)-8s: %(message)-50s  [%(lineno)d %(name)s]",
    datefmt='%H:%M:%S')

# Matplotlib uses the default logger and by setting the level to DEBUG in basicConfig, matplotlib will print a lot of
# debug statements. We prevent that by the logger used by matplotlib manually to level WARNING
logging.getLogger('matplotlib').setLevel(logging.WARNING)
