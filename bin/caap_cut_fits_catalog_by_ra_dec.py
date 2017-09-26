#!/usr/bin/env python2.7
# 
# Aim:
#     check whether a galaxy is within some fits images
# 
# Last update:
#     20170323
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
import astropy.io.ascii as asciitable
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import wcsaxes
from pprint import pprint

import matplotlib


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

try:
    from caap_python_lib_highz import *
except ImportError:
    raise SystemExit("Error! Failed to import caap_python_lib_highz!")





















####################################################################
#                                                                  #
#                                                                  #
#                           MAIN PROGRAM                           #
#                                                                  #
#                                                                  #
####################################################################

#Source = Highz_Galaxy(Field='COSMOS', ID=500030, SubID=1, Names={'Paper1':'Name1','Paper2':'Name2'})
#Source.about()

if len(sys.argv) <= 2:
    print("Usage: caap_cut_fits_catalog_by_ra_dec.py aaa.fits -box ra dec fov -out out.fits")
    sys.exit()

# 
# Loop arguments
Output_file=''
Input_file=''
Input_rect=[numpy.nan, numpy.nan, numpy.nan, numpy.nan] # Cen_RA, Cen_Dec, FoV_RA, FoV_Dec
i=1
while i<len(sys.argv):
    print i
    if sys.argv[i] == '-out':
        i=i+1
        if i<len(sys.argv):
            Output_file = sys.argv[i]
        else:
            continue
    elif sys.argv[i] == '-box':
        i=i+1
        if i<len(sys.argv):
            if sys.argv[i].replace('.','',1).replace('e','',1).replace('+','').replace('-','').isdigit():
                Input_rect[0] = float(sys.argv[i])
            else:
                continue
        else:
            continue
        i=i+1
        if i<len(sys.argv):
            if sys.argv[i].replace('.','',1).replace('e','',1).replace('+','').replace('-','').isdigit():
                Input_rect[1] = float(sys.argv[i])
            else:
                continue
        else:
            continue
        i=i+1
        if i<len(sys.argv):
            if sys.argv[i].replace('.','',1).replace('e','',1).replace('+','').replace('-','').isdigit():
                Input_rect[2] = float(sys.argv[i])
            else:
                continue
        else:
            continue
        i=i+1
        if i<len(sys.argv):
            if sys.argv[i].replace('.','',1).replace('e','',1).replace('+','').replace('-','').isdigit():
                Input_rect[3] = float(sys.argv[i])
            else:
                continue
        else:
            continue
    else: 
        Input_file=sys.argv[i]
    i=i+1

# 
# check Input arguments
Input_check = True
if Output_file == '':
    print('Error! Output file was not given! Please set -out some_name.fits!')
    Input_check = False
if Input_file == '':
    print('Error! Input file was not given! Please input one FITS catalog file!')
    Input_check = False
if numpy.isnan(Input_rect[0]):
    print('Error! Input box was not given! Please input -box ra_degree dec_degree fov_arcsec!')
    Input_check = False
if numpy.isnan(Input_rect[3]) and Input_check:
    Input_rect[3] = Input_rect[2]
if not Input_check:
    sys.exit()

# 
# print message
print('Output FITS file: %s'%(Output_file))
print('Input FITS file: %s'%(Input_file))
print('Input BOX (cen_RA, cen_Dec, FoV_RA, FoV_Dec): %0.8f, %0.8f, %0.3f x %0.3f arcsec'%(Input_rect[0], Input_rect[1], Input_rect[2], Input_rect[3]))

# 
# Read input catalog
Input_Cat = Input_file
if not os.path.isfile(Input_Cat):
    print("Error! The input fits catalog file \"%s\" was not found!"%(Input_Cat))
    sys.exit()

if Input_Cat.endswith('.fits'):
    Cat = Highz_Catalogue(Input_Cat)
    Cat_datatable = Cat.TableData
    Cat_headers = Cat.TableHeaders
else:
    Cat = asciitable.read(Input_Cat, Reader=asciitable.CommentedHeader)
    Cat_datatable = Cat
    Cat_headers = Cat.dtype.names

pprint(Cat.TableData)

# 
# compute distance
Source_ID = Cat.id()
Source_RA = Cat.ra()
Source_Dec = Cat.dec()
#Source_zphot = Cat.zphot()

Sep_RA = (Source_RA - Input_rect[0]) * 3600.0 * numpy.cos(Input_rect[1]/180.0*numpy.pi)
Sep_Dec = (Source_Dec - Input_rect[1]) * 3600.0
Sep_RA_OK = (numpy.fabs(Sep_RA)<=(Input_rect[2]))
Sep_Dec_OK = (numpy.fabs(Sep_Dec)<=(Input_rect[3]))
Sep_OK = (Sep_RA_OK & Sep_Dec_OK)

Index_OK = ((numpy.where(Sep_OK))[0]) # which is the same thing as numpy.where(mask==True). -- see -- https://stackoverflow.com/questions/8218032/how-to-turn-a-boolean-array-into-index-array-in-numpy

print('len(Index_OK) = %d'%(len(Index_OK)))
#print(type(Source_ID))
#print(type(Source_RA))
#print(type(Source_Dec))
#print(type(Index_OK))

Select_ID = Source_ID[Index_OK]
Select_RA = Source_RA[Index_OK]
Select_Dec = Source_Dec[Index_OK]

#pprint((Select_ID, Select_RA, Select_Dec))

Output_Cat = Highz_Catalogue()
Output_Cat.create(length=len(Select_ID))
Output_Cat.addCol('ID', Select_ID) # make sure there have ID RA Dec
Output_Cat.addCol('RA', Select_RA) # make sure there have ID RA Dec
Output_Cat.addCol('Dec', Select_Dec) # make sure there have ID RA Dec
for i in range(len(Cat.TableHeaders)):
    Select_Var = (Cat.TableData[Cat.TableHeaders[i]])[Index_OK]
    Output_Cat.addCol(Cat.TableHeaders[i], Select_Var, Select_Var.dtype)
    print('addCol %s %s'%(Cat.TableHeaders[i],Select_Var.dtype))

pprint(Output_Cat.TableData)

Output_Cat.save(Output_file, overwrite=True)









