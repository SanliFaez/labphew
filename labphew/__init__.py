from pint import UnitRegistry
ureg = UnitRegistry()
Q_ = ureg.Quantity

__version__ = '0.1.1'

simulate_hardware = False
# This acts as a global variable to switch between importing controllers of actual hardware and simulated hardware.
# To change it, use this in your file:
# import labphew
# labphew.simulate_hardware = True