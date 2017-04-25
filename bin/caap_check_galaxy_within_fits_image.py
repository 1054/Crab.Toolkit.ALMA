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
    print("Usage: caap_check_galaxy_within_fits_image.py \"Input_source_catalog[.fits|.txt]\" \"Image_lookmap.txt\"")
    sys.exit()

# 
# Read first argument -- topcat cross-matched catalog
Input_Cat = sys.argv[1]
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
print(Cat_datatable)

# 
# Read second argument -- cutout directory or cutout lookmap file
# <Added><20170320> -- the cutout lookmap file should contain two or three columns
#                      if two columns, should be OBJECT and cutouts file basename
#                      if three columns, should be OBJECT, DATE-OBS and cutouts file basename
Cutouts_Lookmap = {} #<Added><20170320># 
if len(sys.argv) > 2:
    Input_Cut = sys.argv[2]
    if not os.path.isfile(Input_Cut):
        if not os.path.isdir(Input_Cut):
            print("Warning! The input cutouts directory \"%s\" was not found!"%(Input_Cut))
    else:
        print("Using the input cutouts lookmap file \"%s\""%(Input_Cut))
        with open(Input_Cut,'r') as fp:
            for lp in fp:
                tmp_str_list = lp.strip().split()
                #print(len(tmp_str_list))
                if len(tmp_str_list)==2:
                    Cutouts_Lookmap[tmp_str_list[0]] = tmp_str_list[1] # use obj_name fits_image
                elif len(tmp_str_list)==3:
                    Cutouts_Lookmap[tmp_str_list[1]] = tmp_str_list[2] # use obj_name ra_lower ra_upper dec_lower dec_upper fits_image
                elif len(tmp_str_list)==6:
                    Cutouts_Lookmap[(tmp_str_list[1],tmp_str_list[2],tmp_str_list[3],tmp_str_list[4])] = tmp_str_list[5] # 
            fp.close()
else:
    print("Error! The 2nd input argument is not given!")
    sys.exit()
#print(Cutouts_Lookmap)


# 
# Loop each source in the topcat cross-matched catalog
for i in range(len(Cat_datatable)):
    
    # 
    # Get source RA Dec
    # 
    source_RA = numpy.nan
    source_DEC = numpy.nan
    source_Name = ''
    
    if 'Source' in Cat_headers:
        source_Name = Cat_datatable['Source'][i]
    if 'RA' in Cat_headers:
        source_RA = Cat_datatable['RA'][i]
    if '_ra' in Cat_headers:
        source_RA = Cat_datatable['_ra'][i]
    if 'DEC' in Cat_headers:
        source_DEC = Cat_datatable['Dec'][i]
    if 'Dec' in Cat_headers:
        source_DEC = Cat_datatable['Dec'][i]
    if '_de' in Cat_headers:
        source_DEC = Cat_datatable['_de'][i]
    
    if str(source_RA).find(':')>0 and str(source_DEC).find(':')>0:
        source_SkyCoord = SkyCoord(str(source_RA)+' '+str(source_DEC), unit=(units.hourangle, units.deg))
        source_RA = source_SkyCoord.ra.degree
        source_DEC = source_SkyCoord.dec.degree
    else:
        source_RA = numpy.float(source_RA)
        source_DEC = numpy.float(source_DEC)
    
    print('Source RA Dec %0.7f %0.7f'%(source_RA, source_DEC))
    
    if numpy.isnan(source_RA) or numpy.isnan(source_DEC):
        print("Error! Could not read source RA Dec from the input source catalog!")
        continue
    
    # 
    # Check whether the source is within cutout image (by matching OBJECT or RA Dec)
    # 
    CutoutFileFindingStr = 'N/A'
    # -- use Cutouts_Lookmap
    #    and Cutouts_Lookmap is using Object Name to look for cutouts image file
    if CutoutFileFindingStr == 'N/A':
        if len(source_Name) > 0:
            if source_Name in Cutouts_Lookmap.keys():
                print("Found cutouts in cutouts lookmap file for object name \"%s\""%(source_Name))
                CutoutFileFindingStr = "%s"%(Cutouts_Lookmap[source_Name])
    # -- use Cutouts_Lookmap
    #    and Cutouts_Lookmap is using Object RA Dec to look for cutouts image file
    if CutoutFileFindingStr == 'N/A':
        Cutouts_Lookmap_Polygon_Center_Selected = []
        for Cutouts_Lookmap_Key in Cutouts_Lookmap.keys():
            if type(Cutouts_Lookmap_Key) is tuple:
                if len(Cutouts_Lookmap_Key) == 4:
                    Cutouts_Lookmap_Rectangle = numpy.array(Cutouts_Lookmap_Key).astype(numpy.float)
                    #print(Cutouts_Lookmap_Rectangle, len(Cutouts_Lookmap_Rectangle))
                    Cutouts_Lookmap_Polygon_Center = (
                        (Cutouts_Lookmap_Rectangle[0]+Cutouts_Lookmap_Rectangle[1])/2.0, \
                        (Cutouts_Lookmap_Rectangle[2]+Cutouts_Lookmap_Rectangle[3])/2.0
                        )
                    Cutouts_Lookmap_Polygon = matplotlib.path.Path([ \
                        [Cutouts_Lookmap_Rectangle[0],Cutouts_Lookmap_Rectangle[2]], \
                        [Cutouts_Lookmap_Rectangle[0],Cutouts_Lookmap_Rectangle[3]], \
                        [Cutouts_Lookmap_Rectangle[1],Cutouts_Lookmap_Rectangle[3]], \
                        [Cutouts_Lookmap_Rectangle[1],Cutouts_Lookmap_Rectangle[2]], \
                        [Cutouts_Lookmap_Rectangle[0],Cutouts_Lookmap_Rectangle[2]] \
                        ])
                    #print(Cutouts_Lookmap_Polygon)
                    if Cutouts_Lookmap_Polygon.contains_point((source_RA,source_DEC)):
                        print("Found cutouts in cutouts lookmap file for object RA Dec %.7f %.7f"%(source_RA, source_DEC))
                        if len(Cutouts_Lookmap_Polygon_Center_Selected) == 0:
                            Cutouts_Lookmap_Polygon_Center_Selected = Cutouts_Lookmap_Polygon_Center
                            CutoutFileFindingStr = "%s"%(Cutouts_Lookmap[Cutouts_Lookmap_Key])
                        else:
                            if ((source_RA-Cutouts_Lookmap_Polygon_Center[0])**2 + (source_DEC-Cutouts_Lookmap_Polygon_Center[1])**2) < ((source_RA-Cutouts_Lookmap_Polygon_Center_Selected[0])**2 + (source_DEC-Cutouts_Lookmap_Polygon_Center_Selected[1])**2):
                                Cutouts_Lookmap_Polygon_Center_Selected = Cutouts_Lookmap_Polygon_Center
                                CutoutFileFindingStr = "%s"%(Cutouts_Lookmap[Cutouts_Lookmap_Key])
    if CutoutFileFindingStr == 'N/A':
        CutoutFileFindingStr = 'N/A'
    # 
    # Search for cutouts image files
    # 
    print("Searching cutouts image files with pattern \"%s\""%(CutoutFileFindingStr))
    CutoutFilePaths = glob.glob(CutoutFileFindingStr)
    
    
    # 
    # List cutouts (Source.Name[._]*.fits)
    # 
    CutoutFileNames = []
    if len(CutoutFilePaths)==0:
        print("****************************************************************************************************")
        print("Error! Could not find fits image that contains current source index %d name \"%s\"!"%(i, source_Name))
        print("****************************************************************************************************")
        #sys.exit()
        continue
    else:
        # Copy Cutouts fits files and store file names
        for CutoutFilePath in CutoutFilePaths:
            #CutoutFileName = os.path.basename(CutoutFilePath)
            #CutoutFileNames.append("%s/%s/%s"%(CutoutOutputDir, CutoutOutputName, CutoutFileName))
            print("Found fits image \"%s\" that contains current source with index %d name \"%s\"!"%(CutoutFilePath, i, source_Name))
        # 
        #pprint(CutoutFilePaths)
        #pprint(CutoutFileNames)
        #sys.exit()












