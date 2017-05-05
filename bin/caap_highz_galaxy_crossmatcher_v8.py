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
#     20170428 (1) now use Highz_Image class in 'caap_python_lib_highz.py', simplified code here
#              (2) now we do not directly use image S/N for P. Score, but use Source/RefSource flux ratio and only apply when image S/N >= 5.0, 
#              (3) now we do not apply a factor of 2 to the background_sigma. 
#              (4) now we do not measure a series of different size ellipses, but measure a series of ellipses distribution from Source position to RefSource position. 
#              (5) for computing ['Extended'], we do not use Outer/Inner ratio now, but use 'polyfit' 'Overall slope'. 
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
from scipy import spatial
from scipy.spatial import KDTree


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








#pyplot.rcParams['font.family'] = 'NGC'
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












# 
class Logger(object):
    # "Lumberjack class - duplicates sys.stdout to a log file and it's okay"
    # source: http://stackoverflow.com/q/616645
    # see -- http://stackoverflow.com/questions/616645/how-do-i-duplicate-sys-stdout-to-a-log-file-in-python/2216517#2216517
    # usage:
    #    Output_Logger = Logger()
    #    Output_Logger.begin_log_file()
    #    print('works all day')
    #    Output_Logger.end_log_file()
    #    Output_Logger.close()
    # 
    def __init__(self):
        self.file = None
        self.filename = ''
        self.stdout = sys.stdout
        sys.stdout = self
    
    def __del__(self):
        self.close()
    
    def __enter__(self):
        pass
    
    def __exit__(self, *args):
        self.close()
    
    def begin_log_file(self, filename="Logger.log", mode="a", buff=0):
        if self.file != None:
            self.file.close()
            self.file = None
        if filename != '':
            self.filename = filename
            self.file = open(filename, mode, buff)
            self.file.write("# %s\n\n"%(str(datetime.now()))) # write current time # datetime.isoformat(datetime.today())
    
    def end_log_file(self):
        if self.file != None:
            self.file.write("\n# %s\n"%(str(datetime.now()))) # write current time # datetime.isoformat(datetime.today())
            self.file.close()
            self.file = None
    
    def write(self, message):
        self.stdout.write(message)
        if self.file != None:
            self.file.write(message)
    
    def flush(self):
        self.stdout.flush()
        if self.file != None:
            self.file.flush()
            os.fsync(self.file.fileno())
    
    def close(self):
        if self:
            if self.stdout != None:
                sys.stdout = self.stdout
                self.stdout = None
            if self.file != None:
                self.file.close()
                self.file = None











# 20170427
# The idea of this code is to make an auto-identification 
# of two sources being the same galaxy or not. 
# So we will base on 
#     (1) InputSource position





# 
class CrossMatch_Identifier(object):
    # 
    # 
    def __init__(self, Source, RefSource, RefImage, RefCatalog=None, MatchCatalog=None, Separation=numpy.nan):
        # 
        # Prepare variables
        self.Source = Source
        self.RefSource = RefSource
        self.RefImage = RefImage
        self.RefCatalog = RefCatalog # this is a big reference catalog for calculating Crowdedness and Clean_Index. 
        self.MatchCatalog = MatchCatalog # this is the cross-match catalog with Separation, ID_1, RA_1, Dec_1, ID_2, RA_2, Dec_2, in case no input Source and RefSource. <TODO>
        # 
        # Get RefImage.FitsImageFile
        if self.RefImage.isValid():
            self.FitsImageFile = self.RefImage.FitsImageFile
        else:
            self.FitsImageFile = ''
        # 
        # Calculate Crowdedness and Clean_Index
        if self.RefCatalog is not None:
            self.Crowdedness = self.RefCatalog.calc_crowdedness(self.Source.RA, self.Source.Dec, 3.0)
            self.Clean_Index = self.RefCatalog.calc_clean_index(self.Source.RA, self.Source.Dec, 1.5)
        else:
            self.Crowdedness = numpy.nan
            self.Clean_Index = numpy.nan
        # 
        # Read Separation
        self.MatchSeparation = Separation
        self.MatchScore = -99
        # 
        # Prepare more variables
        self.Morphology = {
                'Separation': numpy.nan, 
                'Angle': numpy.nan, 
                'SepDist': numpy.nan, 
                'SepAngle': numpy.nan, 
                'Projected_Source_Radius': numpy.nan, 
                'PosAngle': numpy.nan, 
                'Extended': 0.0, 
                'Crowdedness': self.Crowdedness, 
                'Clean_Index': self.Clean_Index, 
                'Score': 0.0, 
        }
        # 
        self.Photometry = {
                'Position': [], 
                'Centroid': [], 
                'Flux': 0.0, 
                'FluxError': 0.0, 
                'FluxBias': 0.0, 
                'S/N': 0.0, 
                'Source/RefSource': 0.0, 
                'EnclosedPower': [], 
                'GrowthCurve': [], 
                'Score': 0.0, 
        }
        # 
        self.World = {}
    # 
    # 
    def about(self):
        # 
        # get variable name 
        # -- see http://stackoverflow.com/questions/1690400/getting-an-instance-name-inside-class-init
        self.World['My Name'] = ""
        self.World['My Names'] = []
        tmp_frame = inspect.currentframe().f_back
        tmp_variables = dict(tmp_frame.f_globals.items() + tmp_frame.f_locals.items())
        for tmp_name, tmp_variable in tmp_variables.items():
            if isinstance(tmp_variable, self.__class__):
                if hash(self) == hash(tmp_variable):
                    self.World['My Names'].append(tmp_name)
        if len(self.World['My Names']) > 0:
            self.World['My Name'] = self.World['My Names'][0]
        # 
        # print crossmatcher info
        tmp_str_max_length = 0
        if tmp_str_max_length < len(self.World['My Name']+' '):
            tmp_str_max_length = len(self.World['My Name']+' ')
        tmp_str_source = self.Source.Field+'--'+self.Source.Name+'--'+str(self.Source.SubID)
        if tmp_str_max_length < len(self.FitsImageFile):
            tmp_str_max_length = len(self.FitsImageFile)
        if tmp_str_max_length < len(tmp_str_source):
            tmp_str_max_length = len(tmp_str_source)
        tmp_str_format_fixedwidth = '{0:<%d}'%(tmp_str_max_length)
        tmp_str_format_filleddash = '{0:-<%d}'%(tmp_str_max_length)
        print("")
        print(' |---------------- %s-|'%( tmp_str_format_filleddash.format(self.World['My Name']+' ')         ))
        print(' |        Source | %s |'%( tmp_str_format_fixedwidth.format(tmp_str_source)                    ))
        print(' | FitsImageFile | %s |'%( tmp_str_format_fixedwidth.format(self.FitsImageFile)                ))
        print(' |-----------------%s-|'%( tmp_str_format_filleddash.format('-')                               ))
        print("")
    # 
    # 
    def match_morphology(self, OutputDir='results', OutputName='', Overwrite=False, FoV=12.0):
        # 
        if self.Source and self.RefSource and self.RefImage:
            # 
            # check output directory
            if not os.path.isdir(OutputDir):
                os.mkdir(OutputDir)
            # 
            # check Source data structure
            if not self.Source.Field:
                print("Error! \"Source\" does not have \"Field\" info!")
                return
            if not self.Source.Name:
                print("Error! \"Source\" does not have \"Name\" info!")
                return
            #if not self.Source.ID:
            #    print("Error! \"Source\" does not have \"ID\" info!")
            #    return
            if not self.Source.SubID:
                print("Error! \"Source\" does not have \"SubID\" info!")
                return
            if not 'Major Axis' in self.Source.Morphology:
                print("Error! \"Source.Morphology\" does not have \"Major Axis\" info!")
                return
            if not 'Minor Axis' in self.Source.Morphology:
                print("Error! \"Source.Morphology\" does not have \"Minor Axis\" info!")
                return
            if not 'Pos Angle' in self.Source.Morphology:
                print("Error! \"Source.Morphology\" does not have \"Pos Angle\" info!")
                return
            # 
            # check FitsImageFile
            if not self.RefImage.isValid():
                print("Error! The RefImage is invalid!")
                return
            # 
            # recognize Instrument and Telescope from the fits image file name
            StrInstrument, StrTelescope = recognize_Instrument(self.FitsImageFile)
            if len(StrInstrument) == 0 or len(StrTelescope) == 0:
                print("Error! Failed to recognize Instrument and Telescope info from the input fits image file name: \"%s\"!"%(self.FitsImageFile))
                pyplot.pause(3.0)
                return
            # 
            # prepare output figure and text file names
            if OutputName == '':
                OutputName = self.Source.Field+'--'+str(self.Source.Name)+'--'+str(self.Source.SubID)
            PlotOutput = OutputDir+'/'+OutputName+'--'+StrTelescope+'--'+StrInstrument.replace(' ','-')+'.pdf'
            TextOutput = OutputDir+'/'+OutputName+'--'+StrTelescope+'--'+StrInstrument.replace(' ','-')+'.txt'
            LoggOutput = OutputDir+'/'+OutputName+'--'+StrTelescope+'--'+StrInstrument.replace(' ','-')+'.log'
            LockOutput = OutputDir+'/'+OutputName+'--'+StrTelescope+'--'+StrInstrument.replace(' ','-')+'.lock' #<TODO># 
            # 
            # check previous crossmatch results
            if os.path.isfile(TextOutput):
                # 
                # <20170224> added a check step to make sure our scores do not have nan
                with open(TextOutput, 'r') as fp:
                    temp_Score_Total = numpy.nan
                    temp_Score_Morph = numpy.nan
                    temp_Score_Photo = numpy.nan
                    temp_Score_Exten = numpy.nan
                    for lp in fp:
                        if lp.startswith('Match.Score'):
                            temp_Score_Total = (lp.split('=')[1]).split('#')[0]
                        elif lp.startswith('Match.Morphology.Score'):
                            temp_Score_Morph = (lp.split('=')[1]).split('#')[0]
                        elif lp.startswith('Match.Photometry.Score'):
                            temp_Score_Photo = (lp.split('=')[1]).split('#')[0]
                        elif lp.startswith('Match.Morphology.Extended'):
                            temp_Score_Exten = (lp.split('=')[1]).split('#')[0]
                    fp.close()
                    if math.isnan(float(temp_Score_Total)) or \
                       math.isnan(float(temp_Score_Morph)) or \
                       math.isnan(float(temp_Score_Photo)) or \
                       math.isnan(float(temp_Score_Exten)) :
                        print("Warning! Previous crossmatching result \"%s\" contains \"nan\"! Will redo the crossmatching due to NaN values found!"%(TextOutput))
                        Overwrite = True
                        pyplot.pause(2.0)
                #if(TextOutput.find('22721')>=0):
                #    pyplot.pause(2.0)
                if not Overwrite:
                    print("Found previous crossmatching result: \"%s\"! Will not redo the crossmatching unless the \"overwrite\" option are input!"%(TextOutput))
                    return
            # 
            # begin Logger
            if 'Output_Logger' in globals():
                Output_Logger.begin_log_file(filename=LoggOutput, mode='w')
            # 
            # do morphology check
            # -- we will create a series of ellipse from Source position to RefSource position
            # -- then check the morphological extent
            if True:
                # 
                # plot image
                self.RefImage.plot(
                        zoom_size = float(FoV)/self.RefImage.PixScale, 
                        zoom_center = self.RefImage.sky2xy(self.Source.RA, self.Source.Dec)
                    )
                # 
                # add annotation at top-left
                self.RefImage.text('%s %s'%(StrTelescope,StrInstrument), fontsize=15, color=hex2color('#00CC00'), align_top_left=True)
                self.RefImage.text('FoV %.1f arcsec'%(self.RefImage.ZoomSize[1]*self.RefImage.PixScale[1]), fontsize=14, color=hex2color('#00CC00'), align_top_left=True)
                # 
                # add annotation at top-right
                self.RefImage.text('%s--%s--%s'%(self.Source.Field,str(self.Source.Name),str(self.Source.SubID)), fontsize=15, align_top_right=True, horizontalalignment='right')
                for refname in self.RefSource.Names.keys():
                    self.RefImage.text('%s ID %s'%(refname,str(self.RefSource.Names.get(refname))), color=hex2color('#FF0000'), fontsize=15, align_top_right=True, horizontalalignment='right')
                self.RefImage.text('zp = %.3f'%(self.Source.Redshifts['Laigle 2015 photo-z']), color=hex2color('#FF0000'), fontsize=14, align_top_right=True, horizontalalignment='right')
                # 
                # 
                # create source_aperture and refsource_aperture
                #diameters = numpy.array(range(1,10)) * 0.25 # x0.25 to x2.25 FWHM
                diameters = [1.0]
                for diameter in diameters:
                    if '%0.2fxFWHM'%(diameter) == '1.00xFWHM':
                        edgealpha = 1.00
                        facealpha = 0.05
                        linewidth = 2.5
                        zorder = 9
                    else:
                        edgealpha = numpy.min([diameter/1.0,1.0/diameter]) * 0.8
                        facealpha = 0.0
                        linewidth = 1.0
                        zorder = 11
                    # 
                    self.RefImage.aper(
                        radec = [ self.Source.RA, self.Source.Dec ], 
                        major = diameter * self.Source.Morphology['Major Axis'], 
                        minor = diameter * self.Source.Morphology['Minor Axis'], 
                        angle = self.Source.Morphology['Pos Angle'], 
                        edgecolor = hex2color('#00FF00'), 
                        facecolor = hex2color('#00FF00'), 
                        linewidth = linewidth, 
                        edgealpha = edgealpha, 
                        facealpha = facealpha, 
                        zorder = zorder, 
                        label = 'source position %0.2fxFWHM'%(diameter)
                    )
                # 
                # create refsource_aperture
                for diameter in diameters:
                    if '%0.2fxFWHM'%(diameter) == '1.00xFWHM':
                        linewidth = 2.5
                        color = hex2color('#FF0000')
                        draw_cross = True
                        zorder = 8
                    else:
                        linewidth = 1.0
                        color = 'none'
                        draw_cross = False
                        zorder = 12
                    # 
                    self.RefImage.aper(
                        radec = [ self.RefSource.RA, self.RefSource.Dec ], 
                        major = diameter * self.Source.Morphology['Major Axis'], 
                        minor = diameter * self.Source.Morphology['Minor Axis'], 
                        angle = self.Source.Morphology['Pos Angle'], 
                        linewidth = linewidth, 
                        color = color, 
                        draw_ellipse = False, 
                        draw_cross = draw_cross, 
                        zorder = zorder, 
                        label = 'refsource position %0.2fxFWHM'%(diameter)
                    )
                # 
                # 
                # store source_aperture and refsource_aperture
                source_aperture = self.RefImage.get_aperture_by_label('source position 1.00xFWHM')
                refsource_aperture = self.RefImage.get_aperture_by_label('refsource position 1.00xFWHM')
                # 
                # 
                # compute variables
                flux_ratio_source_to_refsource = numpy.nan
                signal_to_noise_ratio_source = numpy.nan
                signal_to_noise_ratio_refsource = numpy.nan
                surface_brightness_source = numpy.nan
                flux_ratio_source_to_refsource = (source_aperture['Flux']-source_aperture['Background']) / (refsource_aperture['Flux']-refsource_aperture['Background'])
                signal_to_noise_ratio_source = (source_aperture['Flux']-source_aperture['Background']) / (source_aperture['Noise'])
                signal_to_noise_ratio_refsource = (refsource_aperture['Flux']-refsource_aperture['Background']) / (refsource_aperture['Noise'])
                surface_brightness_source = (source_aperture['Flux']-source_aperture['Background']) / (source_aperture['Area']) # flux unit per arcsec-square
                # 
                # store into 'self.Photometry[]' data structure
                self.Photometry['Flux'] = (source_aperture['Flux']-source_aperture['Background'])
                self.Photometry['FluxError'] = source_aperture['Noise']
                self.Photometry['S/N'] = self.Photometry['Flux'] / self.Photometry['FluxError']
                self.Photometry['Position'] = [source_aperture['RA'], source_aperture['Dec']]
                self.Photometry['Centroid'] = source_aperture['Centroid']
                if signal_to_noise_ratio_source >= 3.0 or signal_to_noise_ratio_refsource >= 3.0:
                    self.Photometry['Source/RefSource'] = flux_ratio_source_to_refsource
                else:
                    self.Photometry['Source/RefSource'] = -99
                # 
                # 
                # calc the Separation between Source and RefSource
                sep_x = (refsource_aperture['X'] - source_aperture['X']) * self.RefImage.PixScale[0]
                sep_y = (refsource_aperture['Y'] - source_aperture['Y']) * self.RefImage.PixScale[1]
                SepDist = numpy.sqrt( sep_x**2 + sep_y**2 ) # in arcsec
                SepAngle = numpy.arctan2(sep_y, sep_x) / numpy.pi * 180.0
                PosAngle = self.Source.Morphology['Pos Angle']
                print("Source position %.3f %.3f"%(source_aperture['X'], source_aperture['Y']))
                print("RefSource position %.3f %.3f"%(refsource_aperture['X'], refsource_aperture['Y']))
                print("Separated distance x y %0.3f %0.3f"%(sep_x, sep_y))
                print("RefSource to Source has a SepDist=%.3f [arcsec] and SepAngle=%.1f [degree], comparing to Source Morphology PosAngle=%.1f [degree]."%(SepDist,SepAngle,self.Source.Morphology['Pos Angle']))
                if not numpy.isnan(self.MatchSeparation):
                    print("Comparing to the Catalog Separation=%.3f [arcsec]."%(self.MatchSeparation))
                # 
                # 
                # create a series of ellipses from Source position to RefSource position
                jiggle_number = 5
                self.Photometry['GrowthCurve'] = [ {
                        'PosX': source_aperture['X'], 
                        'PosY': source_aperture['Y'], 
                        'x': float(0.0)/float(jiggle_number+1), 
                        'y': (source_aperture['Flux']-source_aperture['Background']) / (source_aperture['Flux']-source_aperture['Background']), 
                        'err': (source_aperture['Noise']), 
                        'area': (source_aperture['Area'])
                } ]
                for jiggle_i in range(jiggle_number):
                    jiggle_pos_x = source_aperture['X'] + (refsource_aperture['X'] - source_aperture['X']) / (jiggle_number+1) * (jiggle_i+1)
                    jiggle_pos_y = source_aperture['Y'] + (refsource_aperture['Y'] - source_aperture['Y']) / (jiggle_number+1) * (jiggle_i+1)
                    # 
                    edgealpha = 0.8 / numpy.sqrt(jiggle_i+1)
                    facealpha = 0.0
                    linewidth = 1.0
                    zorder = 11
                    # 
                    self.RefImage.aper(
                        position = [ jiggle_pos_x, jiggle_pos_y ], 
                        major = source_aperture['Major'], 
                        minor = source_aperture['Minor'], 
                        angle = self.Source.Morphology['Pos Angle'], 
                        edgecolor = hex2color('#00FF00'), 
                        facecolor = hex2color('#00FF00'), 
                        linewidth = linewidth, 
                        edgealpha = edgealpha, 
                        facealpha = facealpha, 
                        zorder = zorder, 
                        label = 'jiggle position %d'%(jiggle_i+1)
                    )
                    # 
                    # get jiggle_aperture
                    jiggle_aperture = self.RefImage.get_aperture_by_label('jiggle position %d'%(jiggle_i+1))
                    # 
                    # store in to (self.Photometry['GrowthCurve'])
                    self.Photometry['GrowthCurve'].append( {
                        'PosX': jiggle_pos_x, 
                        'PosY': jiggle_pos_y, 
                        'x': float(jiggle_i+1)/float(jiggle_number+1), 
                        'y': (jiggle_aperture['Flux']-jiggle_aperture['Background']) / (source_aperture['Flux']-source_aperture['Background']), 
                        'err': (jiggle_aperture['Noise']), 
                        'area': (jiggle_aperture['Area'])
                    } )
                # 
                # append RefSource position photometry to the (self.Photometry['GrowthCurve'])
                self.Photometry['GrowthCurve'].append( {
                    'PosX': refsource_aperture['X'], 
                    'PosY': refsource_aperture['Y'], 
                    'x': float(jiggle_number+1)/float(jiggle_number+1), 
                    'y': (refsource_aperture['Flux']-refsource_aperture['Background']) / (source_aperture['Flux']-source_aperture['Background']), 
                    'err': (refsource_aperture['Noise']), 
                    'area': (refsource_aperture['Area'])
                } )
                # 
                # print source position photometry S/N info
                self.Photometry['EnclosedPower'] = []
                for dia in range(len(diameters)):
                    temp_aperture = self.RefImage.get_aperture_by_label('source position %0.2fxFWHM'%(diameters[dia]))
                    self.Photometry['EnclosedPower'].append( {
                        'x': diameters[dia], 
                        'y': (temp_aperture['Flux']-temp_aperture['Background']), 
                        'err': (temp_aperture['Noise']), 
                        'area': (temp_aperture['Area'])
                    } )
                    print('Source image source position major=%0.2fxFWHM aperture has flux = %0.6g +- %0.6g and S/N = %0.3f (area = %0.6g arcsec^2)'%(self.Photometry['EnclosedPower'][dia]['x'], self.Photometry['EnclosedPower'][dia]['y'], self.Photometry['EnclosedPower'][dia]['err'], self.Photometry['EnclosedPower'][dia]['y']/self.Photometry['EnclosedPower'][dia]['err'], self.Photometry['EnclosedPower'][dia]['area']))
                ## 
                ## print surface brightness S/N info, normalize (self.Photometry['GrowthCurve']) by 'surface_brightness_source'
                #for dia in range(len(diameters)):
                #    print('Source image annulus with diameter %0.2fxFWHM has surface brightness = %0.6g +- %0.6g and S/N = %0.3f (area = %0.6g)'%(self.Photometry['GrowthCurve'][dia]['x'], self.Photometry['GrowthCurve'][dia]['y'], self.Photometry['GrowthCurve'][dia]['err'], self.Photometry['GrowthCurve'][dia]['y']/self.Photometry['GrowthCurve'][dia]['err'], self.Photometry['GrowthCurve'][dia]['area']))
                # 
                # print jiggle position photometry info
                for dia in range(jiggle_number+2):
                    print('Source image jiggle position %0.2fxSep. aperture has flux = %0.6g +- %0.6g and S/N = %0.3f (area = %0.6g arcsec^2)'%(self.Photometry['GrowthCurve'][dia]['x'], self.Photometry['GrowthCurve'][dia]['y'], self.Photometry['GrowthCurve'][dia]['err'], self.Photometry['GrowthCurve'][dia]['y']/self.Photometry['GrowthCurve'][dia]['err'], self.Photometry['GrowthCurve'][dia]['area']))
                # 
                # 
                # 
                # calculate source mophological extension parameter (only when source S/N >= 3.0)
                source_extent_snr_limit = 3.0
                source_extent = {}
                source_extent['Inner slope'] = numpy.nan
                source_extent['Outer slope'] = numpy.nan
                source_extent['Middle slope'] = numpy.nan
                source_extent['Overall slope'] = numpy.nan
                if signal_to_noise_ratio_source >= source_extent_snr_limit:
                    # print info
                    print('Calculating source mophological extension parameter with surface brightness radial profile')
                    # linear regression
                    fitting_data_x = [ (t['x']) for t in self.Photometry['GrowthCurve'] ]
                    fitting_data_y = [ (t['y']) for t in self.Photometry['GrowthCurve'] ]
                    fitting_weights = [ 1.0/(t['err'])**2 for t in self.Photometry['GrowthCurve'] ]
                    fitting_poly_deg = 1
                    fitting_data_inner = numpy.array(range(long(len(fitting_data_x)/2)))
                    fitting_data_outer = numpy.array(range(long(len(fitting_data_x)/2)) + numpy.array(long(len(fitting_data_x)/2)))
                    fitting_data_middle = numpy.array(range(long(len(fitting_data_x)/2)) + numpy.array(long(len(fitting_data_x)/4)))
                    fitting_data_overall = numpy.array(range(long(len(fitting_data_x))))
                    fitting_data_inner = fitting_data_inner.astype(long)
                    fitting_data_outer = fitting_data_outer.astype(long)
                    fitting_data_middle = fitting_data_middle.astype(long)
                    fitting_data_overall = fitting_data_overall.astype(long)
                    fitting_data_x = numpy.array(fitting_data_x)
                    fitting_data_y = numpy.array(fitting_data_y)
                    fitting_weights = numpy.array(fitting_weights)
                    fitting_coeff_inner = numpy.polynomial.polynomial.polyfit(fitting_data_x[fitting_data_inner], fitting_data_y[fitting_data_inner], fitting_poly_deg, rcond=None, full=False, w=fitting_weights[fitting_data_inner])
                    fitting_coeff_outer = numpy.polynomial.polynomial.polyfit(fitting_data_x[fitting_data_outer], fitting_data_y[fitting_data_outer], fitting_poly_deg, rcond=None, full=False, w=fitting_weights[fitting_data_outer])
                    fitting_coeff_middle = numpy.polynomial.polynomial.polyfit(fitting_data_x[fitting_data_middle], fitting_data_y[fitting_data_middle], fitting_poly_deg, rcond=None, full=False, w=fitting_weights[fitting_data_middle])
                    fitting_coeff_overall = numpy.polynomial.polynomial.polyfit(fitting_data_x[fitting_data_overall], fitting_data_y[fitting_data_overall], fitting_poly_deg, rcond=None, full=False, w=fitting_weights[fitting_data_overall])
                    #pprint(self.Photometry['GrowthCurve'])
                    #pprint(fitting_coeff_inner)
                    #pprint(fitting_coeff_outer)
                    #pprint(fitting_coeff_middle)
                    #pprint(fitting_coeff_overall)
                    source_extent['Inner slope'] = fitting_coeff_inner[fitting_poly_deg] # [fitting_poly_deg] is the slope, see -- https://docs.scipy.org/doc/numpy-dev/reference/generated/numpy.polynomial.polynomial.polyfit.html
                    source_extent['Outer slope'] = fitting_coeff_outer[fitting_poly_deg]
                    source_extent['Middle slope'] = fitting_coeff_middle[fitting_poly_deg]
                    source_extent['Overall slope'] = fitting_coeff_overall[fitting_poly_deg]
                    print('Source mophological extent profile Inner slope = %0.3f, intercept = %0.6g'%(source_extent['Inner slope'],fitting_coeff_inner[0]))
                    print('Source mophological extent profile Outer slope = %0.3f, intercept = %0.6g'%(source_extent['Outer slope'],fitting_coeff_outer[0]))
                    print('Source mophological extent profile Middle slope = %0.3f, intercept = %0.6g'%(source_extent['Middle slope'],fitting_coeff_middle[0]))
                    print('Source mophological extent profile Overall slope = %0.3f, intercept = %0.6g'%(source_extent['Overall slope'],fitting_coeff_overall[0]))
                    # 
                    if fitting_poly_deg == 1:
                        #self.Morphology['Extended'] = (fitting_coeff_overall[0]+fitting_coeff_overall[1])/(fitting_coeff_overall[0]) * 100.0 # y[x=1]/y[x=0]
                        self.Morphology['Extended'] = (fitting_coeff_overall[0]+fitting_coeff_overall[1]) * 100.0 # y[x=1]/y[x=0] #<TODO># (fitting_coeff_overall[0]) sometimes is negative!
                    # 
                    print('Source mophological extent profile Aperture list: ')
                    pprint(self.Photometry['GrowthCurve'])
                    # 
                    #if False:
                    #    # 
                    #    # select only S/N>=3.0 surface brightness data points then compute the ratio between first annulus and last annulus (S/N>=3.0). 
                    #    fitting_data_x = [ (t['x'])   for t in self.Photometry['GrowthCurve'] if t['y']>=3.0*t['err'] ]
                    #    fitting_data_y = [ (t['y'])   for t in self.Photometry['GrowthCurve'] if t['y']>=3.0*t['err'] ]
                    #    fitting_errors = [ (t['err']) for t in self.Photometry['GrowthCurve'] if t['y']>=3.0*t['err'] ]
                    #    # 
                    #    if len(fitting_data_y) <= 1: 
                    #        self.Morphology['Extended'] = -99 # too low S/N in the image
                    #        print('Source mophological extent profile S/N>=3.0 Outer/Inner Aperture number is less than 2! Will not be able to do further calculation!')
                    #    else:
                    #        self.Morphology['Extended'] = fitting_data_y[-1] / fitting_data_y[0] * 100.0
                    #        print('Source mophological extent profile S/N>=3.0 Outer/Inner Aperture flux ratio = %0.3f (jiggle position %0.0f and %0.0f)'%(fitting_data_y[-1] / fitting_data_y[0], fitting_data_x[-1], fitting_data_x[0]))
                    #        print('Source mophological extent profile S/N>=3.0 Outer/Inner Aperture list: ')
                    #        pprint(self.Photometry['GrowthCurve'])
                else:
                    print('The source S/N is lower than %0.1f (undetected)! Will not be able to calcuate the source mophological extent parameter!'%(source_extent_snr_limit))
                # 
                # 
                #<20170304><dzliu><plang># down-weight the offset so as to improve the score
                offset_down_weighting = 1.0
                if signal_to_noise_ratio_source >= source_extent_snr_limit:
                    if self.Morphology['Extended'] > 0 and self.Morphology['Extended'] == self.Morphology['Extended']:
                        # -- <20170308> only down-weight if source image S/N>5.0
                        # -- <20170430> down-weight extended source Separation, so that when source is fully extended (Outer/Inner=100%), M. Score = 100. 
                        # -- <20170430> now the 'Extended' parameter is just the Outer/Inner flux ratio, 1.0 = 100% means we do not downweight the SepDist, otherwise we do the downweighting. 
                        offset_down_weighting = 1.0 / (self.Morphology['Extended']/100.0)
                        if offset_down_weighting < 0.0:
                            offset_down_weighting = 0.0
                        #if self.Morphology['Extended'] > 100.0:
                        #    offset_down_weighting = numpy.min([numpy.max([self.Morphology['Extended']/100.0, 1.0]), 3.0]) 
                        #    # <TODO> down weighting the offset (SepDist) by at most a factor of 3
                # 
                # 
                # 
                # 
                # 
                # 
                # 
                # calc match quality -- get a score
                self.Morphology['SepDist'] = SepDist # 
                self.Morphology['SepAngle'] = SepAngle # 
                self.Morphology['PosAngle'] = PosAngle # 
                self.Morphology['Separation'] = SepDist # value ranges from 0 to Major Axis and more
                self.Morphology['Angle'] = numpy.min( [ numpy.abs(SepAngle-PosAngle),numpy.abs(SepAngle-PosAngle-360), numpy.abs(SepAngle-PosAngle+360) ] ) # value ranges from 0 to 180.0
                #<DEBUG>#self.Morphology['Separation'] = self.Source.Morphology['Major Axis'] / 2.0
                #<DEBUG>#self.Morphology['Angle'] = 0.0
                self.Morphology['Projected_Source_Radius'] = numpy.abs( self.Source.Morphology['Major Axis'] * numpy.cos(numpy.deg2rad(self.Morphology['Angle'])) ) + \
                                                             numpy.abs( self.Source.Morphology['Minor Axis'] * numpy.sin(numpy.deg2rad(self.Morphology['Angle'])) )
                self.Morphology['Score'] = 100.0 * \
                                                    ( 1.0 - 
                                                      offset_down_weighting * (
                                                        self.Morphology['Separation'] / self.Morphology['Projected_Source_Radius']
                                                      )
                                                    )
                                                    # Separation projected relative to a*cos(theta) + b*sin(theta)
                                                    # 50% means that the SepDist equals the diameter of the ellipse at that SepAngle. 
                                                    # 
                print('Separation = %.3f, projected_source_radius = %.3f, offset_down_weighting = %.3f, M. Score = %.3f'%(self.Morphology['Separation'], self.Morphology['Projected_Source_Radius'], offset_down_weighting, self.Morphology['Score']))
                self.Morphology['Score'] = numpy.max([self.Morphology['Score'], 0])
                self.Morphology['Score'] = numpy.min([self.Morphology['Score'], 100])
                # 
                # 
                # 
                self.Photometry['Score'] = ( 0.85 * numpy.min( [ self.Source.Photometry['ALMA Band 6 240 GHz S/N']/12.0, 1.0 ] )
                                           ) * 100.0
                # 
                # 
                # also consider source image source position aperture photometry S/N
                if self.Photometry['Source/RefSource'] > -99 + 1e-6:
                    self.Photometry['Score'] = self.Photometry['Score'] + \
                                               ( 0.15 * numpy.min( [ self.Photometry['Source/RefSource'], 1.0 ] )
                                               ) * 100.0
                # 
                # 
                # 
                # 
                self.MatchScore = ( 0.5 * self.Morphology['Score'] + 
                                    0.5 * self.Photometry['Score'] )
                # 
                # 
                # 
                # 
                # 
                # plot annotation
                self.RefImage.text('Sep. = %.3f [arcsec]'%(self.Morphology['Separation']), 
                                    color=hex2color('#FF0000'), fontsize=13, align_top_right=True, horizontalalignment='right')
                #self.RefImage.text('Ang. = %.1f [degree]'%(self.Morphology['Angle']), 
                #                    color=hex2color('#FF0000'), fontsize=13, align_top_right=True, horizontalalignment='right')
                # 
                # plot annotation
                self.RefImage.text('M. Score = %.1f [%%]'%(self.Morphology['Score']), 
                                    color=hex2color('#00CC00'), fontsize=13, align_top_right=True, horizontalalignment='right')
                # plot annotation
                self.RefImage.text('P. Score = %.1f [%%]'%(self.Photometry['Score']), 
                                    color=hex2color('#00CC00'), fontsize=13, align_top_right=True, horizontalalignment='right')
                # plot annotation
                self.RefImage.text('Extended = %.1f [%%]'%(self.Morphology['Extended']), 
                                    color=hex2color('#00CC00'), fontsize=13, align_top_right=True, horizontalalignment='right')
                # plot annotation
                self.RefImage.text('Downweight = %.2f'%(offset_down_weighting), 
                                    color=hex2color('#00CC00'), fontsize=13, align_top_right=True, horizontalalignment='right')
                # plot annotation
                self.RefImage.text('ALMA S/N = %.3f'%(self.Source.Photometry['ALMA Band 6 240 GHz S/N']), 
                                    color=hex2color('#00CC00'), fontsize=13, align_top_right=True, horizontalalignment='right')
                # plot annotation
                self.RefImage.text('Image S/N = %.3f'%(self.Photometry['S/N']), 
                                    color=hex2color('#00CC00'), fontsize=13, align_top_right=True, horizontalalignment='right')
                # plot annotation
                self.RefImage.text('Image S/Ref = %.2f'%(self.Photometry['Source/RefSource']), 
                                    color=hex2color('#00CC00'), fontsize=13, align_top_right=True, horizontalalignment='right')
                # plot annotation
                self.RefImage.text('Score = %.1f [%%]'%(self.MatchScore), 
                                    color=hex2color('#00CC00'), fontsize=13, align_top_right=True, horizontalalignment='right')
                # 
                # 
                # 
                # show window and keep window open <DEBUG>
                #pyplot.ioff()
                #pyplot.show()
                #sys.exit()
                # 
                # 
                # 
                # show the image
                #pyplot.draw()
                #pyplot.pause(0.10)
                #print("Click anywhere on the figure to continue")
                # 
                # save the image to disk / output the image to disk
                self.RefImage.PlotDevice.savefig(PlotOutput)
                pyplot.close()
                print("")
                print("Saved as \"%s\"!"%(PlotOutput))
                # 
                # save to text file / output to text file
                #TextOutput = OutputDir+'/'+self.Source.Field+'--'+str(self.Source.Name)+'--'+str(self.Source.SubID)+'--'+StrTelescope+'--'+StrInstrument.replace(' ','-')+'.txt'
                TextFilePtr = open(TextOutput, 'w')
                TextFilePtr.write("# %s\n"%(str(datetime.now())))
                TextFilePtr.write("Source.Name = %s\n"%(self.Source.Name))
                #TextFilePtr.write("Source.ID = %ld\n"%(self.Source.ID))
                TextFilePtr.write("Source.SubID = %ld\n"%(self.Source.SubID))
                TextFilePtr.write("Source.ALMA.S/N = %.3f\n"%(self.Source.Photometry['ALMA Band 6 240 GHz S/N']))
                TextFilePtr.write("RefSource.ID = %ld\n"%(self.RefSource.ID))
                TextFilePtr.write("RefSource.Position = [%.10f, %.10f]\n"%(self.RefSource.RA, self.RefSource.Dec))
                TextFilePtr.write("Crowdedness = %.5f\n"%(self.Crowdedness))
                TextFilePtr.write("Clean_Index = %.0f\n"%(self.Clean_Index))
                TextFilePtr.write("Match.Score = %.1f\n"%(self.MatchScore))
                TextFilePtr.write("Match.Morphology.Score = %.1f\n"%(self.Morphology['Score']))
                TextFilePtr.write("Match.Morphology.Separation = %s # Source to RefSource Separation in arcsec\n"%(self.Morphology['Separation']))
                TextFilePtr.write("Match.Morphology.Angle = %s # Source to RefSource (PosAngle - SepAngle) in degree\n"%(self.Morphology['Angle']))
                TextFilePtr.write("Match.Morphology.Projected_Source_Radius = %s # Projected Source Radius at (PosAngle - SepAngle) direction in arcsec\n"%(self.Morphology['Projected_Source_Radius']))
                TextFilePtr.write("Match.Morphology.Extended = %.1f # Source morphological extent slope\n"%(self.Morphology['Extended']))
                TextFilePtr.write("Match.Photometry.Score = %s\n"%(str(self.Photometry['Score'])))
                TextFilePtr.write("Match.Photometry.Position = [%.10f, %.10f]\n"%(self.Photometry['Position'][0], self.Photometry['Position'][1]))
                TextFilePtr.write("Match.Photometry.Centroid = [%.10f, %.10f]\n"%(self.Photometry['Centroid'][0], self.Photometry['Centroid'][1]))
                TextFilePtr.write("Match.Photometry.S/N = %.3f\n"%(self.Photometry['S/N']))
                TextFilePtr.write("Match.Photometry.Flux = %.6g\n"%(self.Photometry['Flux']))
                TextFilePtr.write("Match.Photometry.FluxError = %.6g\n"%(self.Photometry['FluxError']))
                TextFilePtr.write("Match.Photometry.Source/RefSource = %.6g\n"%(self.Photometry['Source/RefSource']))
                TextFilePtr.write("Match.Photometry.GrowthCurve = %s\n"%(str(self.Photometry['GrowthCurve'])))
                TextFilePtr.close()
                print("Saved to \"%s\"!"%(TextOutput))
                print("")
            # 
            # end Logger
            if 'Output_Logger' in globals():
                Output_Logger.end_log_file()
            #temp_Logger.close()
            #del temp_Logger


















####################################################################
#                                                                  #
#                                                                  #
#                           MAIN PROGRAM                           #
#                                                                  #
#                                                                  #
####################################################################

#Source = Highz_Galaxy(Field='COSMOS', ID=500030, SubID=1, Names={'Paper1':'Name1','Paper2':'Name2'})
#Source.about()

if len(sys.argv) <= 1:
    print("Usage: caap_highz_galaxy_crossmatcher_v8.py \"Match_cycle2_new_detections_1.5arcsec.fits\"")
    sys.exit()

# 
# Read first argument -- topcat cross-matched catalog
Input_Cat = sys.argv[1]
if not os.path.isfile(Input_Cat):
    print("Error! The input fits catalog file \"%s\" was not found!"%(Input_Cat))
    sys.exit()

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
                    if tmp_str_list[0] in Cutouts_Lookmap.keys():
                        Cutouts_Lookmap[tmp_str_list[0]].append(tmp_str_list[1].replace('"','')) # use obj name (check duplication)
                    else:
                        Cutouts_Lookmap[tmp_str_list[0]] = [ tmp_str_list[1].replace('"','') ] # use obj name
                elif len(tmp_str_list)==3:
                    if tmp_str_list[1] in Cutouts_Lookmap.keys():
                        Cutouts_Lookmap[tmp_str_list[1]].append(tmp_str_list[2].replace('"','')) # use obj name (skip [0]) (check duplication)
                    else:
                        Cutouts_Lookmap[tmp_str_list[1]] = [ tmp_str_list[2].replace('"','') ] # use obj name (skip [0])
                elif len(tmp_str_list)==6:
                    if (tmp_str_list[1],tmp_str_list[2],tmp_str_list[3],tmp_str_list[4]) in Cutouts_Lookmap.keys():
                        Cutouts_Lookmap[(tmp_str_list[1],tmp_str_list[2],tmp_str_list[3],tmp_str_list[4])].append(tmp_str_list[5].replace('"','')) # use coordinate rectangle RA_Lo RA_Hi Dec_Lo Dec_Hi (check duplication)
                    else:
                        Cutouts_Lookmap[(tmp_str_list[1],tmp_str_list[2],tmp_str_list[3],tmp_str_list[4])] = [ tmp_str_list[5].replace('"','') ] # use coordinate rectangle RA_Lo RA_Hi Dec_Lo Dec_Hi
            fp.close()
            #print(Cutouts_Lookmap.keys())
else:
    Input_Cut = '/home/dzliu/Temp/cutouts'

# 
# Read 3rd and hereafter arguments -- selected sources
Input_Overwrite = False
Input_DoSources = []
Input_DoSubIDs = []
Input_DoIndexes = []
for i in range(3,len(sys.argv)):
    if sys.argv[i].lower() == 'overwrite':
        # if this argument is 'overwrite'
        Input_Overwrite = True
    elif sys.argv[i].lower().startswith('index'):
        # if this argument is index number range
        Input_DoIndexes = numpy.array(sys.argv[i].lower().replace('index','').strip().split(','))
    else:
        # if this argument is source name (and subid, if separated with --)
        if sys.argv[i].find('--') > 0:
            Input_DoSources.append(sys.argv[i].split('--')[0])
            Input_DoSubIDs.append(sys.argv[i].split('--')[1])
        else:
            Input_DoSources.append(sys.argv[i])
            Input_DoSubIDs.append('*')





# 
# Read 'ref_catalog.fits'
if os.path.isfile('ref_catalog.fits'):
    print("")
    print("Found reference catalog 'ref_catalog.fits' under current directory! We will calculate the 'Crowdedness' and 'Clean_Index' parameters!")
    print("")
    RefCat = Highz_Catalogue('ref_catalog.fits')
    #refcatalog_KDTree = KDTree()
    #refcatalog_CAT = CrabFitsTable('ref_catalog.fits')
    #refcatalog_RA = refcatalog_CAT.getColumn('RA')
    #refcatalog_DEC = refcatalog_CAT.getColumn('Dec')
else:
    print("")
    print("Warning! No reference catalog 'ref_catalog.fits' was found under current directory! Will not calculate 'Crowdedness' and 'Clean_Index'!")
    print("")
    RefCat = None



# 
# Prepare Logger
Output_Logger = Logger()



# 
# Read Catalog
Cat = Highz_Catalogue(Input_Cat)



# 
# Loop each source in the topcat cross-matched catalog
for i in range(len(Cat.TableData)):
    
    # 
    # Skip some sources that do not meet the 3rd argument, which is like "index 3~50"
    # 
    if len(Input_DoIndexes) > 0:
        Input_DoIndex_OK = False
        for Input_DoIndex in Input_DoIndexes:
            if Input_DoIndex.find('-') > 0:
                temp_str_split = Input_DoIndex.split('-')
                if len(temp_str_split) == 2:
                    if i >= long(temp_str_split[0]) and i <= long(temp_str_split[1]):
                        Input_DoIndex_OK = True
            elif Input_DoIndex.find('~') > 0:
                temp_str_split = Input_DoIndex.split('~')
                if len(temp_str_split) == 2:
                    if i >= long(temp_str_split[0]) and i <= long(temp_str_split[1]):
                        Input_DoIndex_OK = True
            elif Input_DoIndex.find(' ') > 0:
                temp_str_split = Input_DoIndex.split(' ')
                for temp_str_item in temp_str_split:
                    if i == long(temp_str_item):
                        Input_DoIndex_OK = True
            else:
                if i == long(Input_DoIndex):
                    Input_DoIndex_OK = True
        # 
        if not Input_DoIndex_OK:
            continue
    
    # 
    # Skip some sources that do not meet the 3rd argument, which is like "SOURCE-NAME--SUBID"
    # 
    if len(Input_DoSources) > 0:
        if Cat.TableData[i].field('OBJECT') not in Input_DoSources:
            Input_DoSubID = '*'
            continue
        else:
            Input_DoSubID = [DoSubID for DoSource, DoSubID in zip(Input_DoSources,Input_DoSubIDs) if DoSource == Cat.TableData[i].field('OBJECT')]
            Input_DoSubID = Input_DoSubID[0]
        # 
        if Input_DoSubID != '*':
            if Cat.TableData[i].field('SUBID_TILE') != long(Input_DoSubID):
                continue
    
    
    
    Overwrite = Input_Overwrite
    
    
    
    # 
    # Read Source Morphology
    # 
    source_maj = numpy.nan
    source_min = numpy.nan
    source_pa = numpy.nan
    if 'FWHM_MAJ_FIT' in Cat.TableHeaders and \
       'FWHM_MIN_FIT' in Cat.TableHeaders and \
       'POSANG_FIT' in Cat.TableHeaders and \
       'MINAX_BEAM' in Cat.TableHeaders and \
       'AXRATIO_BEAM' in Cat.TableHeaders and \
       'POSANG_BEAM' in Cat.TableHeaders:
        source_maj = float(Cat.TableData[i].field('FWHM_MAJ_FIT'))
        source_min = float(Cat.TableData[i].field('FWHM_MIN_FIT'))
        source_pa = float(Cat.TableData[i].field('POSANG_FIT'))
        beam_maj = float(Cat.TableData[i].field('MINAX_BEAM')) * float(Cat.TableData[i].field('AXRATIO_BEAM'))
        beam_min = float(Cat.TableData[i].field('MINAX_BEAM'))
        beam_pa = float(Cat.TableData[i].field('POSANG_BEAM'))
        # prevent source size too small
        if source_maj*source_min < beam_maj*beam_min:
            source_maj = beam_maj
            source_min = beam_min
            source_pa = beam_pa
    if source_maj != source_maj or source_min != source_min or source_pa != source_pa:
        print("")
        print("Error! Could not find appropriate columns in the input topcat cross-matched catalog!")
        print("We need 'FWHM_MAJ_FIT', 'FWHM_MIN_FIT', 'POSANG_FIT', 'MINAX_BEAM', 'AXRATIO_BEAM', 'POSANG_BEAM', etc.")
        print("Abort!")
        print("")
        sys.exit()
    
    
    
    # 
    # Read Source info from Alex Karim's Blind Extraction Catalog
    # 
    if 'OBJECT' in Cat.TableHeaders:
        source_Name = Cat.TableData[i].field('OBJECT').strip()
    if 'PROJECT' in Cat.TableHeaders:
        source_Name = Cat.TableData[i].field('PROJECT').strip()+'--'+source_Name
    if 'SUBID_TILE' in Cat.TableHeaders:
        source_SubID = Cat.TableData[i].field('SUBID_TILE')
    if 'SNR_FIT' in Cat.TableHeaders:
        source_ALMASNR = numpy.float(Cat.TableData[i].field('SNR_FIT'))
    if 'Separation' in Cat.TableHeaders:
        source_separation = numpy.float(Cat.TableData[i].field('Separation'))
    
    
    
    # 
    # Create ALMA Source
    # 
    Source = Highz_Galaxy(
        Field   = 'COSMOS', 
        Name    = source_Name, 
        SubID   = source_SubID, 
        RA      = Cat.ra(i).astype(float), 
        Dec     = Cat.dec(i).astype(float), 
        Morphology = {
            'Major Axis': source_maj, 
            'Minor Axis': source_min, 
            'Pos Angle':  source_pa, 
        }, 
        Photometry = {
            'ALMA Band 6 240 GHz S/N': source_ALMASNR
        }, 
        Redshifts = {
            'Laigle 2015 photo-z': Cat.zphot(i).astype(float)
        }, 
    )
    Source.about()
    
    # 
    # Read Counterpart Source info from the input catalog
    # 
    RefSource = Highz_Galaxy(
        Field = 'COSMOS', 
        Name  = str(Cat.object(i)).strip(), 
        ID    = long(Cat.id(i)), 
        RA    = float(Cat.ra_2(i)), 
        Dec   = float(Cat.dec_2(i)), 
        Names = {
            Cat.catalog_name(): str(Cat.object(i)).strip()
        }
    )
    
    
    
    # 
    # Prepare cutouts and copy to CutoutOutputDir
    # 
    CutoutOutputDir = 'cutouts'
    CutoutOutputName = 'cutouts_temporary' # 'cutouts_'+Source.Name #<20170320><TODO># Source.Name not unique
    CutoutFileFindingStrs = []
    CutoutFilePaths = []
    if not os.path.isdir(CutoutOutputDir):
        os.mkdir(CutoutOutputDir)
    # 
    # check if we have already cutouts for each source (from previous runs)
    # 
    if not os.path.isdir("%s/%s"%(CutoutOutputDir, CutoutOutputName)):
        os.mkdir("%s/%s"%(CutoutOutputDir, CutoutOutputName))
    # 
    # Copy cutouts from Input_Cut directory
    # 
    # -- use Cutouts_Lookmap
    #    and Cutouts_Lookmap is using Object Name to look for cutouts image file
    if len(CutoutFileFindingStrs) == 0:
        if source_Name in Cutouts_Lookmap.keys():
            CutoutFileFindingStr = Cutouts_Lookmap[source_Name] # "%s"%(Cutouts_Lookmap[source_Name])
            CutoutFileFindingStrs.append(CutoutFileFindingStr)
            print("Found cutouts in cutouts lookmap file for object name \"%s\": %s"%(source_Name, CutoutFileFindingStr))
    # -- use Cutouts_Lookmap
    #    and Cutouts_Lookmap is using Object RA Dec to look for cutouts image file
    if len(CutoutFileFindingStrs) == 0:
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
                    if Cutouts_Lookmap_Polygon.contains_point((Source.RA,Source.Dec)):
                        if len(Cutouts_Lookmap_Polygon_Center_Selected) == 0:
                            Cutouts_Lookmap_Polygon_Center_Selected = Cutouts_Lookmap_Polygon_Center
                            CutoutFileFindingStr = Cutouts_Lookmap[Cutouts_Lookmap_Key]
                        else:
                            if ((Source.RA-Cutouts_Lookmap_Polygon_Center[0])**2 + (Source.Dec-Cutouts_Lookmap_Polygon_Center[1])**2) < ((Source.RA-Cutouts_Lookmap_Polygon_Center_Selected[0])**2 + (Source.Dec-Cutouts_Lookmap_Polygon_Center_Selected[1])**2):
                                Cutouts_Lookmap_Polygon_Center_Selected = Cutouts_Lookmap_Polygon_Center
                                CutoutFileFindingStr = Cutouts_Lookmap[Cutouts_Lookmap_Key]
                        if type(CutoutFileFindingStr) is list:
                            CutoutFileFindingStrs.extend(CutoutFileFindingStr)
                        else:
                            CutoutFileFindingStrs.append(CutoutFileFindingStr)
                        print("Found cutouts in cutouts lookmap file for object RA Dec %.10f %.10f: %s"%(Source.RA, Source.Dec, CutoutFileFindingStr))
    #print(type(CutoutFileFindingStrs), len(CutoutFileFindingStrs))
    if len(CutoutFileFindingStrs) == 0:
        CutoutFileFindingStrs = [ "%s/*/%s[._]*.fits"%(Input_Cut, Source.Name) ]
    # 
    # Search for cutouts image files
    # 
    for CutoutFileFindingStr in CutoutFileFindingStrs:
        print("Searching cutouts image files with pattern \"%s\""%(CutoutFileFindingStr))
        CutoutFilePaths.extend(glob.glob(CutoutFileFindingStr))
    
    
    
    # 
    # List cutouts (Source.Name[._]*.fits)
    # 
    CutoutFileNames = []
    if len(CutoutFilePaths)==0:
        print("**********************************************************************************************************************")
        print("Error! Could not find fits image cutouts: \"%s\"! Will skip current source \"%s\"!"%(CutoutFileFindingStr, Source.Name))
        print("**********************************************************************************************************************")
        #sys.exit()
        continue
    else:
        # Copy Cutouts fits files and store file names
        for CutoutFilePath in CutoutFilePaths:
            StrInstrument, StrTelescope = recognize_Instrument(CutoutFilePath)
            CutoutFileName = os.path.basename(CutoutFilePath)
            #if  ( 
            #      (CutoutFileName.find('_acs_I_mosaic_')>=0) or \
            #      (CutoutFileName.find('.J.original-psf.')>=0) or \
            #      (CutoutFileName.find('.H.original_psf.')>=0) or \
            #      (CutoutFileName.find('.Ks.original_psf.')>=0) or \
            #      (CutoutFileName.find('_irac_ch')>=0) 
            #    ) 
            #    # 
            #    # (CutoutFileName.find('_acs_I_mosaic_')>=0)
            #    # (CutoutFileName.find('.J.original-psf.')>=0)
            #    # (CutoutFileName.find('.H.original_psf.')>=0)
            #    # (CutoutFileName.find('.Ks.original_psf.')>=0)
            #    # (CutoutFileName.find('_vla_20cm_dp')>=0)
            #    # (CutoutFileName.find('_vla_3ghz')>=0)
            #    # (CutoutFileName.find('_irac_ch')>=0)
            #    # (CutoutFileName.find('_mips_24_GO3_')>=0)
            #    # 
            if (
                 (StrInstrument.find('ACS')>=0) or \
                 (StrTelescope.find('UltraVISTA')>=0) or \
                 (StrInstrument.find('IRAC')>=0) 
               ) :
                # 
                CutoutFileNames.append("%s/%s/%s"%(CutoutOutputDir, CutoutOutputName, CutoutFileName))
                # 
                if not os.path.isfile("%s/%s/%s"%(CutoutOutputDir, CutoutOutputName, CutoutFileName)):
                    print("Copying cutouts image file \"%s\" to \"%s/%s/%s\""%(CutoutFilePath, CutoutOutputDir, CutoutOutputName, CutoutFileName))
                    shutil.copy2(CutoutFilePath, "%s/%s/%s"%(CutoutOutputDir, CutoutOutputName, CutoutFileName))
        # 
        pprint(CutoutFilePaths)
        pprint(CutoutFileNames)
        #sys.exit()
    
    
    
    # 
    # 
    # Do CrossMatching on each cutout image (i.e. each band)
    # 
    # 
    for CutoutFileName in CutoutFileNames:
        # 
        # CrossMatch_Identifier can only process one fits image at a same time
        # match_morphology() is the core function to do cross-matching
        IDX = CrossMatch_Identifier(
            Source = Source, 
            RefSource = RefSource, 
            RefImage = Highz_Image(CutoutFileName), 
            RefCatalog = RefCat, 
            Separation = source_separation, 
        )
        IDX.about()
        IDX.match_morphology(Overwrite=Overwrite, OutputName=str(i))
        #break
    
    #break












