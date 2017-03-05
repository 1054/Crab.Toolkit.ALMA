#!/usr/bin/env python2.7
# 
# 
# Last update:
#     20170302 numpy.sqrt()*background_sigma
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


from a_dzliu_python_lib_highz import *
from a_dzliu_python_lib_image import *
from a_dzliu_python_lib_telescopes import *


try: 
    import matplotlib
except ImportError:
    raise SystemExit("Error! Failed to import matplotlib!")

matplotlib.use('Qt5Agg')

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














# 
class CrossMatch_Identifier(object):
    # 
    def __init__(self, Source=Highz_Galaxy(), RefSource=Highz_Galaxy(), FitsImageFile="", FitsImageWavelength=0.0, FitsImageFrequency=0.0):
        self.Source = Source
        self.RefSource = RefSource
        self.FitsImageFile = ""
        self.FitsImageWavelength = 0.0
        self.FitsImageFrequency = 0.0
        self.FitsImageData = []
        self.FitsImageHeader = []
        self.FitsImageWCS = WCS()
        self.FitsImagePixScale = [0.0, 0.0]
        self.Match = {
            'Morphology': {
                'SepDist': 0.0, 
                'SepAngle': 0.0, 
                'Score': 0.0, 
                'Extended': 0.0, 
            }, 
            'Photometry': {
                'Aperture': [], 
                'Flux': 0.0, 
                'FluxError': 0.0, 
                'FluxBias': 0.0, 
                'S/N': 0.0, 
                'GrowthCurve': [], 
                'Score': 0.0, 
            }, 
            'Score': 0.0
        }
        # 
        self.World = {}
        # 
        if type(FitsImageFile) is list:
            if len(FitsImageFile)>0:
                self.FitsImageFile = FitsImageFile[0]
            else:
                print("Error! Input FitsImageFile is empty!")
                sys.exit()
        else:
            self.FitsImageFile = str(FitsImageFile)
        # 
        if self.FitsImageFile.find('*')>=0:
            FindImageFile = glob.glob(self.FitsImageFile)
            if len(FindImageFile)>0:
                self.FitsImageFile = FindImageFile[0]
            else:
                print("Error! Find no FitsImageFile according to the input \"%s\"!"%(self.FitsImageFile))
                sys.exit()
        # 
        self.FitsImageWavelength = FitsImageWavelength
        self.FitsImageFrequency = FitsImageFrequency
        # 
        # check FitsImageFile
        if not os.path.isfile(self.FitsImageFile):
            print("Error! \"%s\" was not found!\n"%(self.FitsImageFile))
            sys.exit()
        # 
        # read FitsImageData
        self.FitsImageStruct = fits.open(self.FitsImageFile)
        #print self.FitsImageStruct.info()
        for ExtId in range(len(self.FitsImageStruct)):
            if type(self.FitsImageStruct[ExtId]) is astropy.io.fits.hdu.image.PrimaryHDU:
                self.FitsImageData = self.FitsImageStruct[ExtId].data
                self.FitsImageHeader = self.FitsImageStruct[ExtId].header
                # fix NAXIS to 2 if NAXIS>2, this is useful for VLA images
                if(self.FitsImageHeader['NAXIS']>2):
                    while(self.FitsImageHeader['NAXIS']>2):
                        self.FitsImageData = self.FitsImageData[0]
                        for TempStr in ('NAXIS','CTYPE','CRVAL','CRPIX','CDELT','CUNIT','CROTA'):
                            TempKey = '%s%d'%(TempStr,self.FitsImageHeader['NAXIS'])
                            if TempKey in self.FitsImageHeader:
                                del self.FitsImageHeader[TempKey]
                                #print("del %s"%(TempKey))
                        for TempInt in range(long(self.FitsImageHeader['NAXIS'])):
                            TempKey = 'PC%02d_%02d'%(TempInt+1,self.FitsImageHeader['NAXIS'])
                            if TempKey in self.FitsImageHeader:
                                del self.FitsImageHeader[TempKey]
                                #print("del %s"%(TempKey))
                            TempKey = 'PC%02d_%02d'%(self.FitsImageHeader['NAXIS'],TempInt+1)
                            if TempKey in self.FitsImageHeader:
                                del self.FitsImageHeader[TempKey]
                                #print("del %s"%(TempKey))
                        self.FitsImageHeader['NAXIS'] = self.FitsImageHeader['NAXIS']-1
                    #print(self.FitsImageData.shape)
                    #print(self.FitsImageHeader['NAXIS'])
                    #sys.exit()
                for TempStr in ('NAXIS','CTYPE','CRVAL','CRPIX','CDELT','CUNIT','CROTA'):
                    for TempInt in (3,4):
                        TempKey = '%s%d'%(TempStr,TempInt)
                        if TempKey in self.FitsImageHeader:
                            del self.FitsImageHeader[TempKey]
                # 
                self.FitsImageWCS = WCS(self.FitsImageHeader)
                self.FitsImagePixScale = astropy.wcs.utils.proj_plane_pixel_scales(self.FitsImageWCS) * 3600.0 # arcsec
                # we take the first image <TODO> extension number
                break
    # 
    def about(self):
        # 
        # get my name 
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
    def match_morphology(self, OutputDir='results', Overwrite=False, FoV=15.0):
        if len(self.FitsImageData)>0 and self.Source and self.RefSource:
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
            if not self.Source.ID:
                print("Error! \"Source\" does not have \"ID\" info!")
                return
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
            if len(self.FitsImageFile) == 0:
                print("Error! \"FitsImageFile\" does not have valid content!")
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
            PlotOutput = OutputDir+'/'+self.Source.Field+'--'+str(self.Source.Name)+'--'+str(self.Source.SubID)+'--'+StrTelescope+'--'+StrInstrument.replace(' ','-')+'.pdf'
            TextOutput = OutputDir+'/'+self.Source.Field+'--'+str(self.Source.Name)+'--'+str(self.Source.SubID)+'--'+StrTelescope+'--'+StrInstrument.replace(' ','-')+'.txt'
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
                        #<DEBUG># if lp.find('=') >= 0:
                        #<DEBUG>#     print(lp) #<TODO># print debug info
                        if lp.startswith('Match.Score'):
                            temp_Score_Total = (lp.split('=')[1]).split('#')[0]
                        elif lp.startswith('Match.Morphology.Score'):
                            temp_Score_Morph = (lp.split('=')[1]).split('#')[0]
                        elif lp.startswith('Match.Photometry.Score'):
                            temp_Score_Photo = (lp.split('=')[1]).split('#')[0]
                        elif lp.startswith('Match.Morphology.Extended'):
                            temp_Score_Exten = (lp.split('=')[1]).split('#')[0]
                    fp.close()
                    #print(float(temp_Score_Total))
                    #print(float(temp_Score_Morph))
                    #print(float(temp_Score_Photo))
                    #print(float(temp_Score_Exten))
                    if math.isnan(float(temp_Score_Total)) or \
                       math.isnan(float(temp_Score_Morph)) or \
                       math.isnan(float(temp_Score_Photo)) or \
                       math.isnan(float(temp_Score_Exten)) :
                        print("Warning! Previous crossmatching result \"%s\" contains \"nan\"! Will redo the crossmatching!"%(TextOutput))
                        Overwrite = True
                        pyplot.pause(2.0)
                #if(TextOutput.find('22721')>=0):
                #    pyplot.pause(2.0)
                if not Overwrite:
                    print("Found previous crossmatching result: \"%s\"! Will not redo the crossmatching!"%(TextOutput))
                    return
            # 
            # do morphology check
            if True:
                print('Showing FitsImage')
                PlotDevice = pyplot.figure()
                PlotPanel = PlotDevice.add_axes([0.10, 0.10, 0.85, 0.85], projection = self.FitsImageWCS) # plot RA Dec axes #  PlotPanel = PlotDevice.add_subplot(1,1,1)
                PlotPanel.grid(False)
                PlotPanel.set_xlabel('RA')
                PlotPanel.set_ylabel('Dec')
                # 
                #normfactor = ImageNormalize(self.FitsImageData, interval=AsymmetricPercentileInterval(5,99.5)) # , stretch=SqrtStretch()
                #PlotImage = PlotPanel.imshow(self.FitsImageData, origin='lower', cmap='binary', norm=normfactor, aspect='equal') # cmap='gray' # cmap='jet' # cmap='binary'
                ##PlotDevice.colorbar(PlotImage)
                # 
                # draw the source as an Ellipse
                posxy = self.FitsImageWCS.wcs_world2pix(self.Source.RA, self.Source.Dec, 1) # 3rd arg: origin is the coordinate in the upper left corner of the image. In FITS and Fortran standards, this is 1. In Numpy and C standards this is 0.
                major = self.Source.Morphology['Major Axis'] / self.FitsImagePixScale[0] # in unit of pixel
                minor = self.Source.Morphology['Minor Axis'] / self.FitsImagePixScale[1] # in unit of pixel
                angle = self.Source.Morphology['Pos Angle']
                ellip = Ellipse(xy=posxy, width=major, height=minor, angle=angle, edgecolor='green', facecolor="none", linewidth=2, zorder=10)
                #PlotPanel.add_artist(ellip)
                #print("Plotting Source as %s"%(ellip))
                # 
                #pyplot.grid(False)
                #pyplot.draw()
                #pyplot.pause(0.15)
                # 
                # zoom the image to a zoomsize of 15 arcsec
                #zoomFoV = 15.0 # 0.0 # 15.0 #<TODO># FoV Field of View
                zoomFoV = float(FoV)
                if(zoomFoV>0.0):
                    zoomsize = zoomFoV / self.FitsImagePixScale # zoomsize in pixel unit corresponding to 7 arcsec
                    zoomrect = (numpy.round([posxy[0]-(zoomsize[0]/2.0), posxy[0]+(zoomsize[0]/2.0), posxy[1]-(zoomsize[1]/2.0), posxy[1]+(zoomsize[1]/2.0)]).astype(long))
                    zoomimage = crop(self.FitsImageData, zoomrect)
                    zoomscale = numpy.divide(numpy.array(zoomimage.shape, dtype=float), numpy.array(self.FitsImageData.shape, dtype=float))
                    zoomposxy = numpy.subtract(posxy, [zoomrect[0],zoomrect[2]])
                    zoomellip = Ellipse(xy=zoomposxy, width=major, height=minor, angle=angle, edgecolor=hex2color('#00CC00'), facecolor="none", linewidth=2, zorder=10)
                else:
                    zoomsize = self.FitsImageData.shape
                    zoomrect = numpy.array([1, self.FitsImageData.shape[0], 1, self.FitsImageData.shape[1]])
                    zoomimage = self.FitsImageData
                    zoomscale = numpy.array([1.0, 1.0])
                    zoomposxy = numpy.array(posxy)
                    zoomellip = ellip
                # 
                # add a double-size ellip
                zoomellip_large = copy(zoomellip)
                zoomellip_large.set_linewidth(1.25)
                zoomellip_large.width = zoomellip_large.width * 1.75
                zoomellip_large.height = zoomellip_large.height * 1.75
                # 
                # add a half-size ellip
                zoomellip_small = copy(zoomellip)
                zoomellip_small.set_linewidth(1.25)
                zoomellip_small.width = zoomellip_small.width * 0.25
                zoomellip_small.height = zoomellip_small.height * 0.25
                # 
                # add a blank-position ellip
                #print(zoomellip.__dict__)
                blankellip = copy(zoomellip)
                blankellip.center = blankellip.center + numpy.array(zoomimage.shape) * numpy.array([-0.22,+0.22]) # 0.22 is an arbitrary number to put the blank-position ellipse
                blankellip.set_edgecolor(hex2color('#FFFFFF'))
                # 
                # add a double-size ellip
                blankellip_large = copy(blankellip)
                blankellip_large.set_linewidth(1.25)
                blankellip_large.width = blankellip_large.width * 1.75
                blankellip_large.height = blankellip_large.height * 1.75
                # 
                # add a half-size ellip
                blankellip_small = copy(blankellip)
                blankellip_small.set_linewidth(1.25)
                blankellip_small.width = blankellip_small.width * 0.25
                blankellip_small.height = blankellip_small.height * 0.25
                # 
                normfactor = ImageNormalize(zoomimage, interval=AsymmetricPercentileInterval(19.5,99.5))
                # 
                PlotImage = PlotPanel.imshow(zoomimage, origin='lower', cmap='binary', norm=normfactor, aspect='equal')
                #PlotDevice.colorbar(PlotImage)
                # 
                # add the ellipse(s)
                PlotPanel.add_artist(blankellip_large)
                PlotPanel.add_artist(blankellip_small)
                PlotPanel.add_artist(blankellip)
                PlotPanel.add_artist(zoomellip_large)
                PlotPanel.add_artist(zoomellip_small)
                PlotPanel.add_artist(zoomellip)
                print("Plotting Source as %s in the zoomed image with zoomscale=[%s] and zoomsize=[%s]"%(zoomellip,','.join(zoomscale.astype(str)),','.join(zoomsize.astype(str))))
                # 
                # add annotation at top-left
                PlotPanel.annotate(StrTelescope+' '+StrInstrument, fontsize=15, color=hex2color('#00CC00'), 
                                   xy=(0.03, 0.95), xycoords='axes fraction', 
                                   bbox = dict(boxstyle="round,pad=0.2", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='left', verticalalignment='center')
                PlotPanel.annotate('FoV %.1f arcsec'%(zoomFoV), 
                                   xy=(0.03, 0.95-0.06), xycoords='axes fraction', color=hex2color('#00CC00'), fontsize=14, 
                                   bbox = dict(boxstyle="round,pad=0.2", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='left', verticalalignment='center')
                # 
                # add annotation at top-right
                PlotPanel.annotate(self.Source.Field+': '+str(self.Source.Name)+': '+str(self.Source.SubID), fontsize=15, color=hex2color('#00CC00'), 
                                   xy=(0.97, 0.95), xycoords='axes fraction', 
                                   bbox = dict(boxstyle="round,pad=0.2", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='right', verticalalignment='center')
                # 
                # draw the RefSource by a red cross symbol
                refposxy = self.FitsImageWCS.wcs_world2pix(self.RefSource.RA, self.RefSource.Dec, 1)
                refposxy = numpy.subtract(refposxy, [zoomrect[0],zoomrect[2]])
                PlotPanel.autoscale(False)
                PlotPanel.plot([refposxy[0]], [refposxy[1]], marker='+', markeredgewidth=1.85, 
                               markersize=numpy.mean(0.06*PlotDevice.get_size_inches()*PlotDevice.dpi), 
                               color=hex2color('#CC0000'), zorder=9)
                print("Plotting RefSource at [%s] in the zoomed image with zoomscale=[%s] and zoomsize=[%s]"%(','.join(refposxy.astype(str)),','.join(zoomscale.astype(str)),','.join(zoomsize.astype(str))))
                # 
                # add annotation
                for refname in self.RefSource.Names.keys():
                    PlotPanel.annotate(refname+': '+str(self.RefSource.Names.get(refname)), fontsize=15, color=hex2color('#CC0000'), 
                                   xy=(0.97, 0.95-0.06), xycoords='axes fraction', 
                                   bbox = dict(boxstyle="round,pad=0.2", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='right', verticalalignment='center')
                # 
                # calc Separation
                SepXY = (refposxy - zoomposxy) * self.FitsImagePixScale
                SepDist = math.sqrt( numpy.sum((SepXY)**2) ) # in arcsec
                SepAngle = numpy.arctan2(SepXY[1], SepXY[0]) / math.pi * 180.0
                PosAngle = self.Source.Morphology['Pos Angle']
                print("RefSource to Source has a SepDist=%.3f [arcsec] and SepAngle=%.1f [degree], comparing to Source Morphology PosAngle=%.1f [degree]."%(SepDist,SepAngle,self.Source.Morphology['Pos Angle']))
                # 
                # add annotation
                PlotPanel.annotate("SepDist = %.3f [arcsec]"%(SepDist), 
                                   xy=(0.97, 0.95-0.075-0.045*1), xycoords='axes fraction', color=hex2color('#CC0000'), fontsize=13, 
                                   bbox = dict(boxstyle="round,pad=0.1", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='right', verticalalignment='center')
                PlotPanel.annotate("SepAngle = %.1f [deg]"%(SepAngle), 
                                   xy=(0.97, 0.95-0.075-0.045*2), xycoords='axes fraction', color=hex2color('#CC0000'), fontsize=13, 
                                   bbox = dict(boxstyle="round,pad=0.1", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='right', verticalalignment='center')
                PlotPanel.annotate("PosAngle = %.1f [deg]"%(self.Source.Morphology['Pos Angle']), 
                                   xy=(0.97, 0.95-0.075-0.045*3), xycoords='axes fraction', color=hex2color('#00CC00'), fontsize=13, 
                                   bbox = dict(boxstyle="round,pad=0.1", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='right', verticalalignment='center')
                # 
                # calc match quality -- get a score
                self.Match['Morphology']['SepDist'] = SepDist # value ranges from 0 to Major Axis and more
                self.Match['Morphology']['SepAngle'] = numpy.min([numpy.abs(SepAngle-PosAngle),numpy.abs(SepAngle-PosAngle-360),numpy.abs(SepAngle-PosAngle+360)]) # value ranges from 0 to 180.0
                self.Match['Morphology']['Score'] = 100.0 * \
                                                    ( 1.0 - 
                                                      1.0 * (
                                                        self.Match['Morphology']['SepDist'] / (
                                                          numpy.abs(self.Source.Morphology['Major Axis']*numpy.cos(numpy.deg2rad(self.Match['Morphology']['SepAngle']))) + 
                                                          numpy.abs(self.Source.Morphology['Minor Axis']*numpy.sin(numpy.deg2rad(self.Match['Morphology']['SepAngle'])))
                                                        )
                                                      )
                                                    )
                                                    # Separation projected relative to a*cos(theta) + b*sin(theta)
                                                    # 50% means that the SepDist equals the radius of the ellipse at that SepAngle. 
                                                    # 
                PlotPanel.annotate("M. Score = %.1f [%%]"%(self.Match['Morphology']['Score']), 
                                   xy=(0.97, 0.95-0.075-0.045*4), xycoords='axes fraction', color=hex2color('#00CC00'), fontsize=13, 
                                   bbox = dict(boxstyle="round,pad=0.1", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='right', verticalalignment='center')
                # 
                # draw the image
                pyplot.grid(False)
                pyplot.draw()
                pyplot.pause(0.15)
                # 
                # check the source to be extended or not -- by doing aperture photometry
                print("Photometrying...")
                PhotAper_x0p25 = copy(zoomellip)
                PhotAper_x0p25.width = zoomellip.width*0.25
                PhotAper_x0p25.height = zoomellip.height*0.25
                PhotFlux_x0p25, PhotNPIX_x0p25 = elliptical_Photometry(zoomimage, PhotAper_x0p25)
                PhotAper_x0p50 = copy(zoomellip)
                PhotAper_x0p50.width = zoomellip.width*0.50
                PhotAper_x0p50.height = zoomellip.height*0.50
                PhotFlux_x0p50, PhotNPIX_x0p50 = elliptical_Photometry(zoomimage, PhotAper_x0p50)
                PhotAper_x0p75 = copy(zoomellip)
                PhotAper_x0p75.width = zoomellip.width*0.75
                PhotAper_x0p75.height = zoomellip.height*0.75
                PhotFlux_x0p75, PhotNPIX_x0p75 = elliptical_Photometry(zoomimage, PhotAper_x0p75)
                PhotAper_x1p00 = copy(zoomellip)
                PhotAper_x1p00.width = zoomellip.width*1.00
                PhotAper_x1p00.height = zoomellip.height*1.00
                PhotFlux_x1p00, PhotNPIX_x1p00 = elliptical_Photometry(zoomimage, PhotAper_x1p00)
                PhotAper_x1p25 = copy(zoomellip)
                PhotAper_x1p25.width = zoomellip.width*1.25
                PhotAper_x1p25.height = zoomellip.height*1.25
                PhotFlux_x1p25, PhotNPIX_x1p25 = elliptical_Photometry(zoomimage, PhotAper_x1p25)
                PhotAper_x1p50 = copy(zoomellip)
                PhotAper_x1p50.width = zoomellip.width*1.50
                PhotAper_x1p50.height = zoomellip.height*1.50
                PhotFlux_x1p50, PhotNPIX_x1p50 = elliptical_Photometry(zoomimage, PhotAper_x1p50)
                PhotAper_x1p75 = copy(zoomellip)
                PhotAper_x1p75.width = zoomellip.width*1.75
                PhotAper_x1p75.height = zoomellip.height*1.75
                PhotFlux_x1p75, PhotNPIX_x1p75 = elliptical_Photometry(zoomimage, PhotAper_x1p75)
                print("Integrated source-position flux within 0.25xFWHM is %g"%(PhotFlux_x0p25))
                print("Integrated source-position flux within 0.50xFWHM is %g"%(PhotFlux_x0p50))
                print("Integrated source-position flux within 0.75xFWHM is %g"%(PhotFlux_x0p75))
                print("Integrated source-position flux within 1.00xFWHM is %g"%(PhotFlux_x1p00))
                print("Integrated source-position flux within 1.25xFWHM is %g"%(PhotFlux_x1p25))
                print("Integrated source-position flux within 1.50xFWHM is %g"%(PhotFlux_x1p50))
                print("Integrated source-position flux within 1.75xFWHM is %g"%(PhotFlux_x1p75))
                # 
                # do another photometry at a blank position for testing
                BlankAper_x0p25 = copy(blankellip)
                BlankAper_x0p25.width = blankellip.width*0.25
                BlankAper_x0p25.height = blankellip.height*0.25
                BlankFlux_x0p25, BlankNPIX_x0p25 = elliptical_Photometry(zoomimage, BlankAper_x0p25)
                BlankAper_x0p50 = copy(blankellip)
                BlankAper_x0p50.width = blankellip.width*0.50
                BlankAper_x0p50.height = blankellip.height*0.50
                BlankFlux_x0p50, BlankNPIX_x0p50 = elliptical_Photometry(zoomimage, BlankAper_x0p50)
                BlankAper_x0p75 = copy(blankellip)
                BlankAper_x0p75.width = blankellip.width*0.75
                BlankAper_x0p75.height = blankellip.height*0.75
                BlankFlux_x0p75, BlankNPIX_x0p75 = elliptical_Photometry(zoomimage, BlankAper_x0p75)
                BlankAper_x1p00 = copy(blankellip)
                BlankAper_x1p00.width = blankellip.width*1.00
                BlankAper_x1p00.height = blankellip.height*1.00
                BlankFlux_x1p00, BlankNPIX_x1p00 = elliptical_Photometry(zoomimage, BlankAper_x1p00)
                BlankAper_x1p25 = copy(blankellip)
                BlankAper_x1p25.width = blankellip.width*1.25
                BlankAper_x1p25.height = blankellip.height*1.25
                BlankFlux_x1p25, BlankNPIX_x1p25 = elliptical_Photometry(zoomimage, BlankAper_x1p25)
                BlankAper_x1p50 = copy(blankellip)
                BlankAper_x1p50.width = blankellip.width*1.50
                BlankAper_x1p50.height = blankellip.height*1.50
                BlankFlux_x1p50, BlankNPIX_x1p50 = elliptical_Photometry(zoomimage, BlankAper_x1p50)
                BlankAper_x1p75 = copy(blankellip)
                BlankAper_x1p75.width = blankellip.width*1.75
                BlankAper_x1p75.height = blankellip.height*1.75
                BlankFlux_x1p75, BlankNPIX_x1p75 = elliptical_Photometry(zoomimage, BlankAper_x1p75)
                print("Integrated blank-position flux within 0.25xFWHM is %g"%(BlankFlux_x0p25))
                print("Integrated blank-position flux within 0.50xFWHM is %g"%(BlankFlux_x0p50))
                print("Integrated blank-position flux within 0.75xFWHM is %g"%(BlankFlux_x0p75))
                print("Integrated blank-position flux within 1.00xFWHM is %g"%(BlankFlux_x1p00))
                print("Integrated blank-position flux within 1.25xFWHM is %g"%(BlankFlux_x1p25))
                print("Integrated blank-position flux within 1.50xFWHM is %g"%(BlankFlux_x1p50))
                print("Integrated blank-position flux within 1.75xFWHM is %g"%(BlankFlux_x1p75))
                # 
                # calc background by "caap_analyze_fits_image_pixel_histogram.py"
                print("Calculating background...")
                if not os.path.isfile(self.FitsImageFile+'.pixel.statistics.txt'):
                    os.system('%s "%s"'%('caap_analyze_fits_image_pixel_histogram.py', self.FitsImageFile))
                background_flux = numpy.nan
                background_sigma = numpy.nan
                with open(self.FitsImageFile+'.pixel.statistics.txt', 'r') as fp:
                    for lp in fp:
                        if lp.startswith('Gaussian_mu'):
                            background_flux = float((lp.split('=')[1]).split('#')[0].replace(' ',''))
                        elif lp.startswith('Gaussian_sigma'):
                            background_sigma = float((lp.split('=')[1]).split('#')[0].replace(' ',''))
                # 
                # <20170224> added a check step to make sure we measure the FitGauss
                if background_sigma is numpy.nan:
                    os.system('%s "%s"'%('caap_analyze_fits_image_pixel_histogram.py', self.FitsImageFile))
                    with open(self.FitsImageFile+'.pixel.statistics.txt', 'r') as fp:
                        for lp in fp:
                            if lp.startswith('Gaussian_mu'):
                                background_flux = float((lp.split('=')[1]).split('#')[0].replace(' ',''))
                            elif lp.startswith('Gaussian_sigma'):
                                background_sigma = float((lp.split('=')[1]).split('#')[0].replace(' ',''))
                # 
                # print background flux (sigma)
                print("Median background flux is %g"%(background_flux))
                print("StdDev of the background is %g"%(background_sigma))
                # 
                # calc background-subtracted net flux
                print("Calculating background-subtracted flux...")
                BlankFlux_x0p25 = BlankFlux_x0p25 - background_flux*BlankNPIX_x0p25
                BlankFlux_x0p50 = BlankFlux_x0p50 - background_flux*BlankNPIX_x0p50
                BlankFlux_x0p75 = BlankFlux_x0p75 - background_flux*BlankNPIX_x0p75
                BlankFlux_x1p00 = BlankFlux_x1p00 - background_flux*BlankNPIX_x1p00
                BlankFlux_x1p25 = BlankFlux_x1p25 - background_flux*BlankNPIX_x1p25
                BlankFlux_x1p50 = BlankFlux_x1p50 - background_flux*BlankNPIX_x1p50
                BlankFlux_x1p75 = BlankFlux_x1p75 - background_flux*BlankNPIX_x1p75
                print("Background-subtracted blank-position flux within 0.25xFWHM is %g"%(BlankFlux_x0p25))
                print("Background-subtracted blank-position flux within 0.50xFWHM is %g"%(BlankFlux_x0p50))
                print("Background-subtracted blank-position flux within 0.75xFWHM is %g"%(BlankFlux_x0p75))
                print("Background-subtracted blank-position flux within 1.00xFWHM is %g"%(BlankFlux_x1p00))
                print("Background-subtracted blank-position flux within 1.25xFWHM is %g"%(BlankFlux_x1p25))
                print("Background-subtracted blank-position flux within 1.50xFWHM is %g"%(BlankFlux_x1p50))
                print("Background-subtracted blank-position flux within 1.75xFWHM is %g"%(BlankFlux_x1p75))
                PhotFlux_x0p25 = PhotFlux_x0p25 - PhotNPIX_x0p25*background_flux
                PhotFlux_x0p50 = PhotFlux_x0p50 - PhotNPIX_x0p50*background_flux
                PhotFlux_x0p75 = PhotFlux_x0p75 - PhotNPIX_x0p75*background_flux
                PhotFlux_x1p00 = PhotFlux_x1p00 - PhotNPIX_x1p00*background_flux
                PhotFlux_x1p25 = PhotFlux_x1p25 - PhotNPIX_x1p25*background_flux
                PhotFlux_x1p50 = PhotFlux_x1p50 - PhotNPIX_x1p50*background_flux
                PhotFlux_x1p75 = PhotFlux_x1p75 - PhotNPIX_x1p75*background_flux
                print("Background-subtracted source-position flux within 0.25xFWHM is %-10g (growth:x%.2f) (S/N:%.4g)"%(PhotFlux_x0p25,PhotFlux_x0p25/PhotFlux_x0p25,PhotFlux_x0p25/(numpy.sqrt(PhotNPIX_x0p25)*background_sigma)))
                print("Background-subtracted source-position flux within 0.50xFWHM is %-10g (growth:x%.2f) (S/N:%.4g)"%(PhotFlux_x0p50,PhotFlux_x0p50/PhotFlux_x0p25,PhotFlux_x0p50/(numpy.sqrt(PhotNPIX_x0p50)*background_sigma)))
                print("Background-subtracted source-position flux within 0.75xFWHM is %-10g (growth:x%.2f) (S/N:%.4g)"%(PhotFlux_x0p75,PhotFlux_x0p75/PhotFlux_x0p50,PhotFlux_x0p75/(numpy.sqrt(PhotNPIX_x0p75)*background_sigma)))
                print("Background-subtracted source-position flux within 1.00xFWHM is %-10g (growth:x%.2f) (S/N:%.4g)"%(PhotFlux_x1p00,PhotFlux_x1p00/PhotFlux_x0p75,PhotFlux_x1p00/(numpy.sqrt(PhotNPIX_x1p00)*background_sigma)))
                print("Background-subtracted source-position flux within 1.25xFWHM is %-10g (growth:x%.2f) (S/N:%.4g)"%(PhotFlux_x1p25,PhotFlux_x1p25/PhotFlux_x1p00,PhotFlux_x1p25/(numpy.sqrt(PhotNPIX_x1p25)*background_sigma)))
                print("Background-subtracted source-position flux within 1.50xFWHM is %-10g (growth:x%.2f) (S/N:%.4g)"%(PhotFlux_x1p50,PhotFlux_x1p50/PhotFlux_x1p25,PhotFlux_x1p50/(numpy.sqrt(PhotNPIX_x1p50)*background_sigma)))
                print("Background-subtracted source-position flux within 1.75xFWHM is %-10g (growth:x%.2f) (S/N:%.4g)"%(PhotFlux_x1p75,PhotFlux_x1p75/PhotFlux_x1p50,PhotFlux_x1p75/(numpy.sqrt(PhotNPIX_x1p75)*background_sigma)))
                # 
                # check the source to be extended or not -- finally we can determine this by the light growth curve
                MarkContinue = True
                if(MarkContinue):
                    if(MarkContinue):
                        self.Match['Morphology']['Extended']  = 0.0
                        self.Match['Photometry']['Flux']      = PhotFlux_x0p25
                        self.Match['Photometry']['FluxBias']  = PhotNPIX_x0p25*background_flux
                        self.Match['Photometry']['FluxError'] = numpy.sqrt(PhotNPIX_x0p25)*background_sigma
                        self.Match['Photometry']['Aperture']  = PhotAper_x0p25
                    else:
                        MarkContinue = False
                if(MarkContinue):
                    if( (PhotFlux_x0p50/PhotFlux_x0p25>2.0) or (PhotFlux_x0p50/(numpy.sqrt(PhotNPIX_x0p50)*background_sigma) > PhotFlux_x0p25/(numpy.sqrt(PhotNPIX_x0p25)*background_sigma)) ):
                        self.Match['Morphology']['Extended']  = PhotFlux_x0p50/PhotFlux_x0p25*0.25/3.00*100
                        self.Match['Photometry']['Flux']      = PhotFlux_x0p50
                        self.Match['Photometry']['FluxBias']  = PhotNPIX_x0p50*background_flux
                        self.Match['Photometry']['FluxError'] = numpy.sqrt(PhotNPIX_x0p50)*background_sigma
                        self.Match['Photometry']['Aperture']  = PhotAper_x0p50
                    else:
                        MarkContinue = False
                if(MarkContinue):
                    if( (PhotFlux_x0p75/PhotFlux_x0p50>2.0) or (PhotFlux_x0p75/(numpy.sqrt(PhotNPIX_x0p75)*background_sigma) > PhotFlux_x0p50/(numpy.sqrt(PhotNPIX_x0p50)*background_sigma)) ):
                        self.Match['Morphology']['Extended']  = PhotFlux_x0p75/PhotFlux_x0p50*0.50/3.00*100
                        self.Match['Photometry']['Flux']      = PhotFlux_x0p75
                        self.Match['Photometry']['FluxBias']  = PhotNPIX_x0p75*background_flux
                        self.Match['Photometry']['FluxError'] = numpy.sqrt(PhotNPIX_x0p75)*background_sigma
                        self.Match['Photometry']['Aperture']  = PhotAper_x0p75
                    else:
                        MarkContinue = False
                if(MarkContinue):
                    if( (PhotFlux_x1p00/PhotFlux_x0p75>2.0) or (PhotFlux_x1p00/(numpy.sqrt(PhotNPIX_x1p00)*background_sigma) > PhotFlux_x0p75/(numpy.sqrt(PhotNPIX_x0p75)*background_sigma)) ):
                        self.Match['Morphology']['Extended']  = PhotFlux_x1p00/PhotFlux_x0p75*0.75/3.00*100
                        self.Match['Photometry']['Flux']      = PhotFlux_x1p00
                        self.Match['Photometry']['FluxBias']  = PhotNPIX_x1p00*background_flux
                        self.Match['Photometry']['FluxError'] = numpy.sqrt(PhotNPIX_x1p00)*background_sigma
                        self.Match['Photometry']['Aperture']  = PhotAper_x1p00
                    else:
                        MarkContinue = False
                if(MarkContinue):
                    if( (PhotFlux_x1p25/PhotFlux_x1p00>2.0) or (PhotFlux_x1p25/(numpy.sqrt(PhotNPIX_x1p25)*background_sigma) > PhotFlux_x1p00/(numpy.sqrt(PhotNPIX_x1p00)*background_sigma)) ):
                        self.Match['Morphology']['Extended']  = PhotFlux_x1p25/PhotFlux_x1p00*1.00/3.00*100
                        self.Match['Photometry']['Flux']      = PhotFlux_x1p25
                        self.Match['Photometry']['FluxBias']  = PhotNPIX_x1p25*background_flux
                        self.Match['Photometry']['FluxError'] = numpy.sqrt(PhotNPIX_x1p25)*background_sigma
                        self.Match['Photometry']['Aperture']  = PhotAper_x1p25
                    else:
                        MarkContinue = False
                if(MarkContinue):
                    if( (PhotFlux_x1p50/PhotFlux_x1p25>2.0) or (PhotFlux_x1p50/(numpy.sqrt(PhotNPIX_x1p50)*background_sigma) > PhotFlux_x1p25/(numpy.sqrt(PhotNPIX_x1p25)*background_sigma)) ):
                        self.Match['Morphology']['Extended']  = PhotFlux_x1p50/PhotFlux_x1p25*1.25/3.00*100
                        self.Match['Photometry']['Flux']      = PhotFlux_x1p50
                        self.Match['Photometry']['FluxBias']  = PhotNPIX_x1p50*background_flux
                        self.Match['Photometry']['FluxError'] = numpy.sqrt(PhotNPIX_x1p50)*background_sigma
                        self.Match['Photometry']['Aperture']  = PhotAper_x1p50
                    else:
                        MarkContinue = False
                if(MarkContinue):
                    if( (PhotFlux_x1p75/PhotFlux_x1p50>2.0) or (PhotFlux_x1p75/(numpy.sqrt(PhotNPIX_x1p75)*background_sigma) > PhotFlux_x1p50/(numpy.sqrt(PhotNPIX_x1p50)*background_sigma)) ):
                        self.Match['Morphology']['Extended']  = PhotFlux_x1p75/PhotFlux_x1p50*1.50/3.00*100
                        self.Match['Photometry']['Flux']      = PhotFlux_x1p75
                        self.Match['Photometry']['FluxBias']  = PhotNPIX_x1p75*background_flux
                        self.Match['Photometry']['FluxError'] = numpy.sqrt(PhotNPIX_x1p75)*background_sigma
                        self.Match['Photometry']['Aperture']  = PhotAper_x1p75
                    else:
                        MarkContinue = False
                # 
                # store the source Photometry information
                self.Match['Photometry']['S/N'] = self.Match['Photometry']['Flux'] / self.Match['Photometry']['FluxError']
                self.Match['Photometry']['GrowthCurve'].append((0.25*major*numpy.mean(self.FitsImagePixScale), PhotFlux_x0p25, numpy.sqrt(PhotNPIX_x0p25)*background_sigma)) # tuple, radisu in unit of arcsec, flux and flux error in original pixel value unit. 
                self.Match['Photometry']['GrowthCurve'].append((0.50*major*numpy.mean(self.FitsImagePixScale), PhotFlux_x0p50, numpy.sqrt(PhotNPIX_x0p50)*background_sigma))
                self.Match['Photometry']['GrowthCurve'].append((0.75*major*numpy.mean(self.FitsImagePixScale), PhotFlux_x0p75, numpy.sqrt(PhotNPIX_x0p75)*background_sigma))
                self.Match['Photometry']['GrowthCurve'].append((1.00*major*numpy.mean(self.FitsImagePixScale), PhotFlux_x1p00, numpy.sqrt(PhotNPIX_x1p00)*background_sigma))
                self.Match['Photometry']['GrowthCurve'].append((1.25*major*numpy.mean(self.FitsImagePixScale), PhotFlux_x1p25, numpy.sqrt(PhotNPIX_x1p25)*background_sigma))
                self.Match['Photometry']['GrowthCurve'].append((1.50*major*numpy.mean(self.FitsImagePixScale), PhotFlux_x1p50, numpy.sqrt(PhotNPIX_x1p50)*background_sigma))
                self.Match['Photometry']['GrowthCurve'].append((1.75*major*numpy.mean(self.FitsImagePixScale), PhotFlux_x1p75, numpy.sqrt(PhotNPIX_x1p75)*background_sigma))
                #<test># self.Match['Photometry']['Score'] = ( 1.0 - numpy.exp( -(self.Match['Photometry']['S/N']/12.0                 ) ) ) * 50.0 
                #<test>#                                   + ( 1.0 - numpy.exp( -(self.Source.Photometry['ALMA Band 6 240 GHz S/N']/6.0) ) ) * 50.0
                self.Match['Photometry']['Score'] = ( numpy.min([self.Match['Photometry']['S/N']/12.0, 0.5]) + 
                                                      numpy.min([self.Source.Photometry['ALMA Band 6 240 GHz S/N']/12.0, 0.5])
                                                    ) * 100.0
                self.Match['Score'] = (self.Match['Morphology']['Score']*0.5 + self.Match['Photometry']['Score']*0.5)
                # 
                # plot annotation
                PlotPanel.annotate("Extended = %.1f [%%]"%(self.Match['Morphology']['Extended']), 
                                   xy=(0.97, 0.95-0.075-0.045*5), xycoords='axes fraction', color=hex2color('#00CC00'), fontsize=13, 
                                   bbox = dict(boxstyle="round,pad=0.1", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='right', verticalalignment='center')
                # 
                # plot annotation
                PlotPanel.annotate("Image S/N = %.3f"%(self.Match['Photometry']['S/N']), 
                                   xy=(0.97, 0.95-0.075-0.045*6), xycoords='axes fraction', color=hex2color('#00CC00'), fontsize=13, 
                                   bbox = dict(boxstyle="round,pad=0.1", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='right', verticalalignment='center')
                # 
                # plot annotation
                PlotPanel.annotate("ALMA S/N = %.3f"%(self.Source.Photometry['ALMA Band 6 240 GHz S/N']), 
                                   xy=(0.97, 0.95-0.075-0.045*7), xycoords='axes fraction', color=hex2color('#00CC00'), fontsize=13, 
                                   bbox = dict(boxstyle="round,pad=0.1", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='right', verticalalignment='center')
                # 
                # plot annotation
                PlotPanel.annotate("P. Score = %.1f [%%]"%(self.Match['Photometry']['Score']), 
                                   xy=(0.97, 0.95-0.075-0.045*8), xycoords='axes fraction', color=hex2color('#00CC00'), fontsize=13, 
                                   bbox = dict(boxstyle="round,pad=0.1", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='right', verticalalignment='center')
                # 
                # plot annotation
                PlotPanel.annotate("Score = %.1f [%%]"%(self.Match['Score']), 
                                   xy=(0.97, 0.95-0.075-0.045*9), xycoords='axes fraction', color=hex2color('#00CC00'), fontsize=13, 
                                   bbox = dict(boxstyle="round,pad=0.1", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='right', verticalalignment='center')
                # 
                # plot annotation
                PlotPanel.annotate("zp = %.3f"%(self.Source.Redshifts['Laigle 2015 photo-z']), 
                                   xy=(0.97, 0.95-0.075-0.045*10), xycoords='axes fraction', color=hex2color('#CC0000'), fontsize=13, 
                                   bbox = dict(boxstyle="round,pad=0.1", alpha=0.6, facecolor=hex2color('#FFFFFF'), edgecolor=hex2color('#FFFFFF'), linewidth=2), 
                                   horizontalalignment='right', verticalalignment='center')
                # 
                # show the image
                pyplot.draw()
                #pyplot.pause(3.50)
                pyplot.pause(0.20)
                #print("Click anywhere on the figure to continue")
                #pyplot.waitforbuttonpress()
                #pyplot.show()
                # 
                # save the image to disk / output the image to disk
                #PlotOutput = OutputDir+'/'+self.Source.Field+'--'+str(self.Source.Name)+'--'+str(self.Source.SubID)+'--'+StrTelescope+'--'+StrInstrument.replace(' ','-')+'.pdf'
                PlotDevice.savefig(PlotOutput)
                pyplot.close()
                print("Saved as \"%s\"!"%(PlotOutput))
                # 
                # save to text file / output to text file
                #TextOutput = OutputDir+'/'+self.Source.Field+'--'+str(self.Source.Name)+'--'+str(self.Source.SubID)+'--'+StrTelescope+'--'+StrInstrument.replace(' ','-')+'.txt'
                TextFilePtr = open(TextOutput, 'w')
                TextFilePtr.write("# %s\n"%(str(datetime.now())))
                TextFilePtr.write("Source.Name = %s\n"%(self.Source.Name))
                TextFilePtr.write("Source.ID = %ld\n"%(self.Source.ID))
                TextFilePtr.write("Source.SubID = %ld\n"%(self.Source.SubID))
                TextFilePtr.write("Match.Score = %.1f\n"%(self.Match['Score']))
                TextFilePtr.write("Match.Morphology.Score = %.1f\n"%(self.Match['Morphology']['Score']))
                TextFilePtr.write("Match.Morphology.Extended = %.1f\n"%(self.Match['Morphology']['Extended']))
                TextFilePtr.write("Match.Photometry.Score = %s\n"%(str(self.Match['Photometry']['Score'])))
                TextFilePtr.write("Match.Photometry.S/N = %.3f\n"%(self.Match['Photometry']['S/N']))
                TextFilePtr.write("Match.Photometry.Flux = %.6g\n"%(self.Match['Photometry']['Flux']))
                TextFilePtr.write("Match.Photometry.FluxError = %.6g\n"%(self.Match['Photometry']['FluxError']))
                TextFilePtr.write("Match.Photometry.GrowthCurve = %s\n"%(str(self.Match['Photometry']['GrowthCurve'])))
                TextFilePtr.close()
                print("Saved to \"%s\"!"%(TextOutput))
                print("")


















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
    print("Usage: caap_highz_galaxy_crossmatcher_v2.py \"Match_cycle2_new_detections_1.5arcsec.fits\"")
    sys.exit()

if not os.path.isfile(sys.argv[1]):
    print("Error! The input fits catalog file \"%s\" was not found!"%(sys.argv[1]))
    sys.exit()

Cat = Highz_Catalogue(sys.argv[1])
#print(Cat.TableHeaders)

for i in range(len(Cat.TableData)):
    
    # Check ID
    #if Cat.TableData[i].field('OBJECT') != '126982':
    #    continue
    #if Cat.TableData[i].field('OBJECT') != '141927':
    #    continue
    #if int(Cat.TableData[i].field('SUBID_TILE')) < 14:
    #    continue
    #if long(Cat.TableData[i].field('OBJECT')) < 187431:
    #    continue
    #if Cat.TableData[i].field('OBJECT') != '148443':
    #    continue
    #if Cat.TableData[i].field('OBJECT') != '238643':
    #    continue
    
    Overwrite=True
    
    # 
    # Create ALMA Source
    # 
    Source = Highz_Galaxy(
        Field   = 'COSMOS', 
        Name    = Cat.TableData[i].field('OBJECT'), 
        ID      = re.sub('[!@#$a-zA-Z_]', '', Cat.TableData[i].field('OBJECT')), 
        SubID   = Cat.TableData[i].field('SUBID_TILE'), 
        RA      = Cat.TableData[i].field('RA'), 
        Dec     = Cat.TableData[i].field('DEC'), 
        Morphology = {
            'Major Axis': float(Cat.TableData[i].field('FWHM_MAJ_FIT')), 
            'Minor Axis': float(Cat.TableData[i].field('FWHM_MIN_FIT')), 
            'Pos Angle':  float(Cat.TableData[i].field('POSANG_FIT')), 
        }, 
        Photometry = {
            'ALMA Band 6 240 GHz S/N': float(Cat.TableData[i].field('SNR_FIT'))
        }, 
        Redshifts = {
            'Laigle 2015 photo-z': float(Cat.TableData[i].field('PHOTOZ'))
        }, 
    )
    Source.about()
    
    # 
    # Create Counterpart Source from Laigle 2015 Catalog
    # 
    RefSource = Highz_Galaxy(
        Field = 'COSMOS', 
        Name  = Cat.TableData[i].field('NUMBER'), 
        ID    = Cat.TableData[i].field('NUMBER'), 
        RA    = Cat.TableData[i].field('ALPHA_J2000'), 
        Dec   = Cat.TableData[i].field('DELTA_J2000'), 
        Names = { 'Laigle 2015': str(Cat.TableData[i].field('NUMBER')) }
    )
    
    # 
    # Prepare cutouts and copy to CutoutOutputDir
    # 
    CutoutOutputDir = 'cutouts'
    CutoutOutputName = 'cutouts_45arcsec_'+Source.Name # Source.Name
    CutoutFileFindingStr = 'N/A'
    CutoutFilePaths = []
    if not os.path.isdir(CutoutOutputDir):
        os.mkdir(CutoutOutputDir)
    if not os.path.isdir("%s/%s"%(CutoutOutputDir, CutoutOutputName)):
        os.mkdir("%s/%s"%(CutoutOutputDir, CutoutOutputName))
        # Copy from certain other directory <TODO>
        #CutoutFileFindingStr = "/home/dzliu/aida42198_ALMA_Data/ALMA_COSMOS/cutouts/45arcsec/*/%s[._]*.fits"%(Source.Name)
        CutoutFileFindingStr = "/home/dzliu/Temp/cutouts/*/%ld[._]*.fits"%(Source.ID) # cutout fits file names always contain ID but not full names. 
        CutoutFilePaths = glob.glob(CutoutFileFindingStr)
    else:
        # Copy from certain other directory <TODO>
        CutoutFileFindingStr = "%s/%s/%s[._]*.fits"%(CutoutOutputDir, CutoutOutputName, Source.ID) # cutout fits file names always contain ID but not full names. 
        CutoutFilePaths = glob.glob(CutoutFileFindingStr)
    
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
            CutoutFileName = os.path.basename(CutoutFilePath)
            if  ( (CutoutFileName.find('_acs_I_mosaic_')>=0) or \
                 ((CutoutFileName.find('_irac_ch')>=0) and (CutoutFileName.find('_DEEP_')>=0)) or \
                  (CutoutFileName.find('_mips_24_GO3_')>=0) or \
                  (CutoutFileName.find('.J.original-psf.')>=0) or \
                  (CutoutFileName.find('.H.original_psf.')>=0) or \
                  (CutoutFileName.find('.Ks.original_psf.')>=0) or \
                  (CutoutFileName.find('_vla_20cm_dp')>=0) or \
                  (CutoutFileName.find('_vla_3ghz')>=0) 
                ) :
                # 
                CutoutFileNames.append("%s/%s/%s"%(CutoutOutputDir, CutoutOutputName, CutoutFileName))
                # 
                if not os.path.isfile("%s/%s/%s"%(CutoutOutputDir, CutoutOutputName, CutoutFileName)):
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
            FitsImageFile = CutoutFileName
        )
        IDX.about()
        IDX.match_morphology(Overwrite=Overwrite)
        #break
    
    #break












