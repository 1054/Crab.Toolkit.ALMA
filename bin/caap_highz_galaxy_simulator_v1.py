#!/usr/bin/env python2.7
# 
# 
# Last update:
#     20170302 numpy.sqrt()*background_sigma
#     20170308 (1) we find that the image pixel rms underestimates the flux error, as there are some background variation across images like ACS, so we decide to multiply a factor of 2 to the background_sigma. 
#              (2) for down-weighting the offset/Separation with the extended-parameter, we should only apply when image S/N > 3. And the way we calculate the extended-parameter changed from S/N_(largest_ellipse) / S/N_(smallest_ellipse) to S/N_(largest ellp. S/N>2) / S/N_(smallest ellip. S/N>2). 
#              (3) fixed "== numpy.nan" thing. Because "numpy.nan == numpy.nan" is False, if a value is nan, it does not equal to itself. 
#              (4) output "Source.Photometry['ALMA S/N']" to the output text file.
#              (5) measure peak pixel position within each ellipse -- this needs to modify "caap_python_lib_image.py" "elliptical_Photometry"
# 

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
from astropy import units
from astropy.io import fits
from astropy.wcs import WCS
import wcsaxes
from pprint import pprint


from caap_python_lib_highz import *
from caap_python_lib_image import *
from caap_python_lib_telescopes import *


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
    from astropy.visualization import astropy_mpl_style
except ImportError:
    raise SystemExit("Error! Failed to import astropy_mpl_style from astropy.visualization!")

try:
    from astropy.visualization import MinMaxInterval, PercentileInterval, AsymmetricPercentileInterval, SqrtStretch, PowerStretch, ImageNormalize
except ImportError:
    raise SystemExit("Error! Failed to import MinMaxInterval, PercentileInterval, AsymmetricPercentileInterval, SqrtStretch, PowerStretch, ImageNormalize from astropy.visualization!")
# ImageNormalize requires astropy>=1.3

try: 
    import scipy
    import skimage
    from skimage.exposure import rescale_intensity
    from skimage.feature import peak_local_max
    #from skimage.morphology import is_local_maximum
except ImportError:
    raise SystemExit("Error! Failed to import skimage (scikit-image) or scipy!")

try:
    from itertools import groupby
    from operator import itemgetter
except ImportError:
    raise SystemExit("Error! Failed to import groupby from itertools!")

try:
    from copy import copy
except ImportError:
    raise SystemExit("Error! Failed to import copy from copy!")
    # this is for copying data structure, otherwise 

try:
    import shutil
except ImportError:
    raise SystemExit("Error! Failed to import shutil!")
    # for copying file with metadata

try:
    from datetime import datetime
except ImportError:
    raise SystemExit("Error! Failed to import datetime!")








pyplot.rcParams['font.family'] = 'NGC'
pyplot.rcParams['font.size'] = 13
pyplot.rcParams['axes.labelsize'] = 'large'
#pyplot.rcParams['axes.labelpad'] = 5.0
#pyplot.rcParams['ytick.major.pad'] = 10 # padding between ticks and axis
pyplot.rcParams['xtick.minor.visible'] = True # 
pyplot.rcParams['ytick.minor.visible'] = True # 
pyplot.rcParams['figure.figsize'] = 20, 18
pyplot.style.use(astropy_mpl_style)


# stretch_sqrt = SqrtStretch()
# Image2 = stretch_sqrt(Image)

# from matplotlib.colors import LogNorm
# pyplot.imshow(image_data, cmap='gray', norm=LogNorm())
























####################################################################
#                                                                  #
#                                                                  #
#                           MAIN PROGRAM                           #
#                                                                  #
#                                                                  #
####################################################################

# 
# Usage
# 
if len(sys.argv) <= 3:
    print("Usage: caap_highz_galaxy_simulator_v1.py, '[pos_xlower,pos_xupper,pos_ylower,pos_yupper]', '[flux_lower,flux_upper,distrib]', '[size_lower,size_upper,distrib]'")
    sys.exit()

# 
# Read arguments
# 
Input_Pos = sys.argv[1]
if type(Input_Pos) is str:
    Simulator_Pos = numpy.array(Input_Pos.replace('[','').replace(']','').split(',')).astype(numpy.float)
    print(Simulator_Pos, type(Simulator_Pos))
# 
Input_Flux = sys.argv[2]
if type(Input_Flux) is str:
    Simulator_Flux = numpy.array(Input_Flux.replace('[','').replace(']','').split(',')).astype(numpy.float)
    print(Simulator_Flux, type(Simulator_Flux))
# 
Input_Size = sys.argv[3]
if type(Input_Size) is str:
    Simulator_Size = numpy.array(Input_Size.replace('[','').replace(']','').split(',')).astype(numpy.float)
    print(Simulator_Size, type(Simulator_Size))

# 
# Generate simulated galaxies
# 










