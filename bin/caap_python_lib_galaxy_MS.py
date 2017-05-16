#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# 

################################
# 
# class calc_MS_SFR()
# 
#   Example: 
#            TODO
# 
################################

try:
    import pkg_resources
except ImportError:
    raise SystemExit("Error! Failed to import pkg_resources!")

pkg_resources.require("numpy")
pkg_resources.require("astropy>=1.3")
pkg_resources.require("matplotlib")
pkg_resources.require("wcsaxes") # http://wcsaxes.readthedocs.io/en/latest/getting_started.html

import os
import sys
import re
import glob
import inspect
import math
import numpy
import astropy
import astropy.io.ascii as asciitable
#from astropy import units
#from astropy.io import fits
#from astropy.wcs import WCS
#import wcsaxes
#from scipy import spatial
#from scipy.spatial import KDTree


try: 
    import matplotlib
except ImportError:
    raise SystemExit("Error! Failed to import matplotlib!")

import platform
if platform.system() == 'Darwin':
    matplotlib.use('Qt5Agg')
else:
    matplotlib.use('TkAgg')

try: 
    from matplotlib import pyplot
except ImportError:
    raise SystemExit("Error! Failed to import pyplot from matplotlib!")

try: 
    from matplotlib.colors import hex2color, rgb2hex
except ImportError:
    raise SystemExit("Error! Failed to import hex2color, rgb2hex from matplotlib.colors!")

try:
    from matplotlib.patches import Ellipse, Circle, Rectangle
except ImportError:
    raise SystemExit("Error! Failed to import Ellipse, Circle, Rectangle from matplotlib.patches!")

try:
    from astropy.visualization import MinMaxInterval, PercentileInterval, AsymmetricPercentileInterval, SqrtStretch, PowerStretch, ImageNormalize
except ImportError:
    raise SystemExit("Error! Failed to import MinMaxInterval, PercentileInterval, AsymmetricPercentileInterval, SqrtStretch, PowerStretch, ImageNormalize from astropy.visualization!")
# ImageNormalize requires astropy>=1.3



import warnings

warnings.filterwarnings("ignore",".*GUI is implemented.*")










# 
def calc_MS_SFR(MS_name = 'Sargent', z = 0.0, Mstar = []):
    MS_dir = '%s/data/Galaxy_MS'%(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    MS_file = ''
    MS_func_refer = ''
    MS_func_format = ''
    # 
    # Choose Galaxy MS
    if MS_name.lower().find('sargent')>=0:
        MS_func_refer = 'Sargent2014'
        MS_func_format = 'Sargent2014'
    if MS_name.lower().find('schreiber')>=0:
        MS_func_refer = 'Schreiber2014'
        MS_func_format = 'Schreiber2014'
    if MS_name.lower().find('bethermin')>=0:
        MS_func_refer = 'Bethermin2015'
        MS_func_format = 'Bethermin2015'
    # 
    # Print info
    print("Loading galaxy star-forming main sequence correlation: %s"%(MS_func_refer))
    # 
    # Compute MS SFR
    if MS_func_format == 'Sargent2014':
        # Sargent2014
        MS_sSFR = 0.095 * 10**(-0.21*(numpy.log10(Mstar)-numpy.log10(5e10))) * numpy.exp(2.05*z/(1.0+0.16*z**1.54))
        MS_SFR = MS_sSFR / 1e9 * Mstar
        return MS_SFR
    elif MS_func_format == 'Schreiber2014':
        # 2015A&A...575A..74S
        # They are Salpeter IMF, but the input are Chabrier IMF
        lg_Mstar = numpy.log10(Mstar) + numpy.log10(1.73)
        MS_SFR_comp1 = lg_Mstar-9.0-0.50+1.5*numpy.log10(z+1.0)
        MS_SFR_comp2 = lg_Mstar-9.0-0.36-2.5*numpy.log10(z+1.0)
        MS_SFR_comp2 = MS_SFR_comp2 * (MS_SFR_comp2>0)
        MS_SFR = MS_SFR_comp1 + MS_SFR_comp2
        MS_SFR = MS_SFR - numpy.log10(1.73)
        MS_SFR = 10**MS_SFR
        return MS_SFR
    elif MS_func_format == 'Bethermin2015':
        # http://arxiv.org/pdf/1409.5796v2
        # section 4.2
        # paragraph 1 -- (0.061±0.006Gyr**{−1})*(1+z)**{2.82±0.12} at z<2 and as (1+z)**{2.2±0.3} at z>2.
        sSFR_comp1 = (0.061*(1+z)**2.82)
        sSFR_comp1 = sSFR_comp1 * (z<2)
        sSFR_comp2 = ((1+z)**2.2)/10.0
        sSFR_comp2 = sSFR_comp2 * (z>=2)
        sSFR = sSFR_comp1 + sSFR_comp2
        MS_SFR = sSFR / 1e9 * Mstar
        return MS_SFR


















