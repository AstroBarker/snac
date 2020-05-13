import numpy as np
from astropy import units as u
from astropy import constants as const

# snac
from . import tools

"""
Module for calculating physical quantities
"""

g_to_msun = u.g.to(u.M_sun)