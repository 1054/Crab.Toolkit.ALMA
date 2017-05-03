#!/usr/bin/env python2.7
# 

################################
# 
# class CrabFitsTable
# 
# class Highz_Galaxy
# 
# class Highz_Catalogue
# 
#   Example: 
#            Cat = Highz_Catalogue('.fits')
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
from astropy import units
from astropy.io import fits
from astropy.wcs import WCS
import wcsaxes
from scipy import spatial
from scipy.spatial import KDTree


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
    from astropy.visualization import MinMaxInterval, PercentileInterval, AsymmetricPercentileInterval, SqrtStretch, PowerStretch, ImageNormalize
except ImportError:
    raise SystemExit("Error! Failed to import MinMaxInterval, PercentileInterval, AsymmetricPercentileInterval, SqrtStretch, PowerStretch, ImageNormalize from astropy.visualization!")
# ImageNormalize requires astropy>=1.3



import warnings

warnings.filterwarnings("ignore",".*GUI is implemented.*")










# 
class CrabFitsTable(object):
    # 
    def __init__(self, FitsTableFile, FitsTableNumb=0):
        self.FitsTableFile = FitsTableFile
        print "Reading Fits Table: %s"%(self.FitsTableFile)
        self.FitsStruct = fits.open(self.FitsTableFile)
        self.TableColumns = []
        self.TableData = []
        self.TableHeaders = []
        self.World = {}
        #print TableStruct.info()
        TableCount = 0
        for TableId in range(len(self.FitsStruct)):
            if type(self.FitsStruct[TableId]) is astropy.io.fits.hdu.table.BinTableHDU:
                if TableCount == FitsTableNumb:
                    self.TableColumns = self.FitsStruct[TableId].columns
                    self.TableData = self.FitsStruct[TableId].data
                TableCount = TableCount + 1
        if(TableCount==0):
            print "Error! The input FitsTableFile does not contain any data table!"
        else:
            self.TableHeaders = self.TableColumns.names
        #print a column
        #print(self.TableData.field('FWHM_MAJ_FIT'))
    # 
    def getData(self):
        return self.TableData
    # 
    def getColumnNames(self):
        return self.TableHeaders
    # 
    def getColumn(self, ColNameOrNumb):
        if type(ColNameOrNumb) is str or type(ColNameOrNumb) is numpy.string_:
            if ColNameOrNumb in self.TableHeaders:
                return self.TableData.field(ColNameOrNumb)
            else:
                print("Error! Column name \"%s\" was not found in the data table!"%(ColNameOrNumb))
                return []
        else:
            if ColNameOrNumb >= 1 and ColNameOrNumb <= len(self.TableHeaders):
                #<BUGGY><FIXED><20170210># return self.TableData[int(ColNameOrNumb)]
                #<BUGGY><FIXED><20170226># [int(ColNameOrNumb)] --> [int(ColNameOrNumb)-1]
                return self.TableData.field(self.TableHeaders[int(ColNameOrNumb)-1])
            else:
                print("Error! Column number %d is out of allowed range (1 - %d)!"%(int(ColNameOrNumb),len(self.TableHeaders)))
                return []
    # 
    def setColumn(self, ColNameOrNumb, DataArray):
        if type(ColNameOrNumb) is str or type(ColNameOrNumb) is numpy.string_:
            if ColNameOrNumb in self.TableHeaders:
                self.TableData[ColNameOrNumb] = DataArray
            else:
                print("Error! Column name \"%s\" was not found in the data table!"%(ColNameOrNumb))
                return
        else:
            if ColNameOrNumb >= 1 and ColNameOrNumb <= len(self.TableHeaders):
                #<BUGGY><FIXED><20170210># self.TableData[int(ColNameOrNumb)] = DataArray
                #<BUGGY><FIXED><20170226># [int(ColNameOrNumb)] --> [int(ColNameOrNumb)-1]
                self.TableData[self.TableHeaders[int(ColNameOrNumb)-1]] = DataArray
            else:
                print("Error! Column number %d is out of allowed range (1 - %d)!"%(int(ColNameOrNumb),len(self.TableHeaders)))
                return
    # 
    def saveAs(self, OutputFilePath, OverWrite = False):
        if os.path.isfile(OutputFilePath):
            if OverWrite == True:
                os.system("mv %s %s"%(OutputFilePath, OutputFilePath+'.backup'))
                self.FitsStruct.writeto(OutputFilePath)
                print("Output to %s! (A backup has been created as %s)"%(OutputFilePath, OutputFilePath+'.backup'))
            else:
                print("We will not overwrite unless you specify saveAs(OverWrite=True)!")
        else:
            self.FitsStruct.writeto(OutputFilePath)
            print("Output to %s!"%(OutputFilePath))
















# 
class CrabFitsImage(object):
    # 
    def __init__(self, FitsImageFile, FitsImageExtension=0):
        self.FitsImageFile = FitsImageFile
        print "Reading Fits Image: %s"%(self.FitsImageFile)
        self.FitsStruct = fits.open(self.FitsImageFile)
        self.Image = []
        self.Header = []
        self.Dimension = []
        self.WCS = []
        self.PixScale = [numpy.nan, numpy.nan]
        self.World = {}
        #print FitsImagePointer.info()
        # 
        ImageCount = 0
        for ImageId in range(len(self.FitsStruct)):
            if type(self.FitsStruct[ImageId]) is astropy.io.fits.hdu.image.PrimaryHDU:
                if ImageCount == FitsImageExtension:
                    # 
                    # read fits image and header
                    self.Image = self.FitsStruct[ImageId].data
                    self.Header = self.FitsStruct[ImageId].header
                    # 
                    # fix NAXIS to 2 if NAXIS>2, this is useful for VLA images
                    if(self.Header['NAXIS']>2):
                        while(self.Header['NAXIS']>2):
                            self.Image = self.Image[0]
                            for TempStr in ('NAXIS','CTYPE','CRVAL','CRPIX','CDELT','CUNIT','CROTA'):
                                TempKey = '%s%d'%(TempStr,self.Header['NAXIS'])
                                if TempKey in self.Header:
                                    del self.Header[TempKey]
                                    #print("del %s"%(TempKey))
                            for TempInt in range(long(self.Header['NAXIS'])):
                                TempKey = 'PC%02d_%02d'%(TempInt+1,self.Header['NAXIS'])
                                if TempKey in self.Header:
                                    del self.Header[TempKey]
                                    #print("del %s"%(TempKey))
                                TempKey = 'PC%02d_%02d'%(self.Header['NAXIS'],TempInt+1)
                                if TempKey in self.Header:
                                    del self.Header[TempKey]
                                    #print("del %s"%(TempKey))
                            self.Header['NAXIS'] = self.Header['NAXIS']-1
                        for TempStr in ('NAXIS','CTYPE','CRVAL','CRPIX','CDELT','CUNIT','CROTA'):
                            for TempInt in (3,4):
                                TempKey = '%s%d'%(TempStr,TempInt)
                                if TempKey in self.Header:
                                    del self.Header[TempKey]
                    # 
                    self.Dimension = [ numpy.long(self.Header['NAXIS1']), numpy.long(self.Header['NAXIS2']) ]
                    self.WCS = WCS(self.Header)
                    self.PixScale = astropy.wcs.utils.proj_plane_pixel_scales(self.WCS) * 3600.0 # arcsec
                    # 
                    ImageCount = ImageCount + 1
                    break
                else:
                    ImageCount = ImageCount + 1
                # 
        if(ImageCount==0):
            print "Error! The input FitsImageFile does not contain any data image!"
        # 
    # 
    def image(self):
        return self.Image
    # 
    def getImage(self):
        return self.Image
    # 
    def dimension(self):
        return self.Dimension
    # 
    def getDimension(self):
        return self.Dimension
    # 
    def wcs(self):
        return self.WCS
    # 
    def getWCS(self):
        return self.WCS
    # 
    def pixscale(self):
        return self.PixScale
    # 
    def getPixScale(self):
        return self.PixScale
















# 
class Highz_Galaxy(object):
    # 
    def __init__(self, ID=-1L, SubID=-1L, Name="", Field="", Names={}, RA=-1E0, Dec=-1E0, Epoch="J2000", z=0.0, Morphology={}, Photometry={}, Redshifts={}):
        self.ID = long(ID)
        self.RA = float(RA)
        self.Dec = float(Dec)
        self.Epoch = str(Epoch)
        self.Name = str(Name)
        self.Field = str(Field)
        self.SubID = long(SubID)
        self.Names = Names
        # 
        self.Morphology = Morphology
        self.Photometry = Photometry
        self.Redshifts = Redshifts
        self.z = z
        # 
        # check Pos Angle
        if 'Pos Angle' in self.Morphology:
            if self.Morphology['Pos Angle'] < -180.0: 
                self.Morphology['Pos Angle'] = self.Morphology['Pos Angle'] + 360.0
            elif self.Morphology['Pos Angle'] > 180.0:
                self.Morphology['Pos Angle'] = self.Morphology['Pos Angle'] - 360.0
                # http://stackoverflow.com/questions/35749246/python-atan-or-atan2-what-sould-i-use
        # 
        self.SED = {}
        self.LED = {}
        # 
        self.World = {}
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
        # for tmp_name, tmp_value in globals().items():
        #     print tmp_name, "*************", tmp_value, "*************", self, "*************", (tmp_value is self)
        #     #print tmp_name, "*************", tmp_value, "*************", self, "*************", isinstance(tmp_value, self.__class__)
        #     #print tmp_name, "*************", tmp_value, "*************", type(self), "*************", (tmp_value is type(self))
        #     #print tmp_name, "*************", tmp_value, "*************", self.__class__, "*************", (tmp_value is self.__class__) # same  as type(self)
        #     if tmp_value is self:
        #         self.World['My Name'] = tmp_name
        #         break
        # 
        # print galaxy info
        tmp_str_max_length = 0
        if tmp_str_max_length < len(self.World['My Name']+' '):
            tmp_str_max_length = len(self.World['My Name']+' ')
        if tmp_str_max_length < len(self.Field):
            tmp_str_max_length = len(self.Field)
        if tmp_str_max_length < len( str(self.ID) ):
            tmp_str_max_length = len( str(self.ID) )
        if tmp_str_max_length < len( str(self.SubID) ):
            tmp_str_max_length = len( str(self.SubID) )
        if tmp_str_max_length < len(self.Name):
            tmp_str_max_length = len(self.Name)
        if tmp_str_max_length < len( ', '.join(self.Names.values()) ):
            tmp_str_max_length = len( ', '.join(self.Names.values()) )
        tmp_str_format_fixedwidth = '{0:<%d}'%(tmp_str_max_length)
        tmp_str_format_filleddash = '{0:-<%d}'%(tmp_str_max_length)
        print("")
        print(' |-------- %s-|'%( tmp_str_format_filleddash.format(self.World['My Name']+' ')       ))
        print(' | Field | %s |'%( tmp_str_format_fixedwidth.format(self.Field)                      ))
        print(' |    ID | %s |'%( tmp_str_format_fixedwidth.format(self.ID)                         ))
        print(' | SubID | %s |'%( tmp_str_format_fixedwidth.format(self.SubID)                      ))
        print(' |  Name | %s |'%( tmp_str_format_fixedwidth.format(self.Name)                       ))
        print(' | Names | %s |'%( tmp_str_format_fixedwidth.format(', '.join(self.Names.values()))  ))
        print(' |---------%s-|'%( tmp_str_format_filleddash.format('-')                             ))
        print("")
















# 
class Highz_Catalogue(object):
    # 
    def __init__(self, FitsTableFile):
        self.FitsTableFile = FitsTableFile
        self.FitsTablePointer = CrabFitsTable(FitsTableFile)
        self.World = {}
        if self.FitsTablePointer:
            self.TableData = self.FitsTablePointer.getData()
            self.TableHeaders = self.FitsTablePointer.getColumnNames()
            self.World['Is Valid'] = True
            self.RA = self.ra()
            self.Dec = self.dec()
            self.KDTree = None
        else:
            self.TableData = []
            self.TableHeaders = []
            self.World['Is Valid'] = False
            self.RA = None
            self.Dec = None
            self.KDTree = None
    # 
    # get column by a given list of possible column names, 
    # can also input column number selection and row index selection. 
    def col(self, ColName=[], ColSelect=[1], RowSelect=[], CheckExistence=False):
        # ColName is a list of column names, but in default only the first found column data will be returned. 
        # ColSelect is a list of column index (starting from 1), default is [1], i.e. return the first found column. 
        if type(ColName) is not list:
            ColName = [ColName]
        if type(ColSelect) is not list:
            ColSelect = [ColSelect] # number starting from 1
            ColSingle = 0 # whether the input is a single scalar or a list
        else:
            ColSingle = len(ColSelect)
        if type(RowSelect) is not list:
            RowSelect = [RowSelect] # index starting from 0
            RowSingle = 0 # whether the input is a single scalar or a list
        else:
            RowSingle = len(RowSelect)
        # use numpy array
        ColName = numpy.array(ColName)
        ColSelect = numpy.array(ColSelect)
        RowSelect = numpy.array(RowSelect)
        # prepare output array and count
        ColOutput = []
        ColNumber = 0
        ColCount = 0
        # loop
        for ColHead in ColName:
            #print(ColHead, ColHead in self.TableHeaders)
            if ColHead in self.TableHeaders:
                ColNumber = ColNumber + 1
                #print(ColNumber, ColSelect)
                if ColNumber <= numpy.max(ColSelect):
                    #print('Reading column "%s"'%(ColHead))
                    ColData = self.FitsTablePointer.getColumn(ColHead)
                    ColCount = ColCount + 1
                    if ColCount == 1:
                        # if ColSelect is a list with more than 1 element, then return a 2D numpy array
                        ColOutput = numpy.column_stack((ColData,))
                        #print(ColOutput.shape)
                    elif ColCount == 2:
                        # ColSelect is a list with more than 1 element, then return a 2D numpy array
                        ColOutput = numpy.column_stack((ColOutput,ColData))
                        #print(ColOutput.shape)
                    else:
                        # ColSelect is a list with more than 1 element, then return a 2D numpy array
                        ColOutput = numpy.column_stack((ColOutput,ColData))
                        #print(ColOutput.shape)
                else:
                    break
            else:
                if CheckExistence:
                    print('Error! Column "%s" was not found in table "%s"!'%(ColHead, self.FitsTableFile))
                    return None
        # if RowSelect is input
        if len(RowSelect) > 0:
            if ColCount > 0:
                if RowSingle > 0:
                    if ColSingle > 0:
                        return ColOutput[RowSelect[:,None],ColSelect-1]
                    else:
                        return ColOutput[RowSelect[:],ColSelect[0]-1]
                else:
                    if ColSingle > 0:
                        return ColOutput[RowSelect[0,None],ColSelect-1]
                    else:
                        return ColOutput[RowSelect[0],ColSelect[0]-1]
            else:
                return numpy.nan
        # return
        return ColOutput
    # 
    def object(self, InputIndex=[]):
        ColList = ['OBJECT','Object','object','NAME','SOURCE','Name','Source','name','source']
        return self.col(ColName=ColList, ColSelect=1, RowSelect=InputIndex)
    # 
    def id(self, InputIndex=[]):
        ColList = ['ID','INDEX','id','_id','index','NUMBER','ID_1','id_1','ID_2','id_2']
        return self.col(ColName=ColList, ColSelect=1, RowSelect=InputIndex)
    # 
    def id_2(self, InputIndex=[]):
        ColList = ['ID','INDEX','id','_id','index','NUMBER','ID_1','id_1','ID_2','id_2']
        return self.col(ColName=ColList, ColSelect=2, RowSelect=InputIndex)
    # 
    def ra(self, InputIndex=[]):
        ColList = ['RA','ra','ALPHA_J2000','_ra','RA_1','ra_1','RA_2','ra_2']
        return self.col(ColName=ColList, ColSelect=1, RowSelect=InputIndex)
    # 
    # read a second RA/Dec column in the catalog
    def ra_2(self, InputIndex=[]):
        ColList = ['RA','ra','ALPHA_J2000','_ra','RA_1','ra_1','RA_2','ra_2']
        return self.col(ColName=ColList, ColSelect=2, RowSelect=InputIndex)
    # 
    def dec(self, InputIndex=[]):
        ColList = ['DEC','Dec','dec','DELTA_J2000','_dec','DEC_1','Dec_1','dec_1','DEC_2','Dec_2','dec_2']
        return self.col(ColName=ColList, ColSelect=1, RowSelect=InputIndex)
    # 
    # read a second RA/Dec column in the catalog
    def dec_2(self, InputIndex=[]):
        ColList = ['DEC','Dec','dec','DELTA_J2000','_dec','DEC_1','Dec_1','dec_1','DEC_2','Dec_2','dec_2']
        return self.col(ColName=ColList, ColSelect=2, RowSelect=InputIndex)
    # 
    def zphot(self, InputIndex=[]):
        ColList = ['PHOTOZ','zphot','photo-z','z_phot','zPDF','ZPDF','ZML','z']
        return self.col(ColName=ColList, ColSelect=1, RowSelect=InputIndex)
    # 
    def zspec(self, InputIndex=[]):
        ColList = ['SPECZ','zspec','spec-z','z_spec']
        return self.col(ColName=ColList, ColSelect=1, RowSelect=InputIndex)
    # 
    def recognize(self, InputFileName=''):
        if InputFileName == '':
            InputFileName = self.FitsTableFile
        FileDirName = os.path.dirname(InputFileName)
        FileBaseName = os.path.basename(InputFileName)
        RecognizedInfo = None
        for RecognizingStr in [FileBaseName, FileDirName]:
            if RecognizingStr.find('Laigle')>=0 or \
               RecognizingStr.find('Match_cycle2_new_detections_1.5arcsec.fits')>=0:
                RecognizedInfo = {'Name': 'Laigle+2016', 'BibCode': '2016ApJS..224...24L', 'Selection': 'UltraVISTA YJHKs chi2'}
                return RecognizedInfo
            if RecognizingStr.find('Davidzon')>=0 and RecognizingStr.find('IRAC')>=0 and RecognizingStr.find('SPLASH')>=0:
                RecognizedInfo = {'Name': 'Davidzon+2017', 'BibCode': 'Priv. Comm.', 'Selection': 'IRAC SPLASH Residual SExtractor'}
                return RecognizedInfo
        return RecognizedInfo
    # 
    def catalog_name(self):
        RecognizedInfo = self.recognize()
        if RecognizedInfo:
            return RecognizedInfo['Name']
        return ''
    # 
    def catalog_bibcode(self):
        RecognizedInfo = self.recognize()
        if RecognizedInfo:
            return RecognizedInfo['BibCode']
        return ''
    # 
    def catalog_selection_method(self):
        RecognizedInfo = self.recognize()
        if RecognizedInfo:
            return RecognizedInfo['Selection']
        return ''
    # 
    def calc_crowdedness(self, input_ra, input_dec, input_fwhm, verbose=False):
        if self.RA is not None and self.Dec is not None:
            sep_dec = (numpy.array(self.Dec) - input_dec) * 3600.0 # arcsec
            sep_ra = (numpy.array(self.RA) - input_ra) * 3600.0 * numpy.cos(input_dec / 180.0 * numpy.pi)
            Crowdedness = numpy.sum(numpy.exp(-(sep_ra**2 + sep_dec**2)/(input_fwhm**2)))
            if verbose:
                print('Highz_catalogue::calc_crowdedness() len(self.RA) = %d'%(len(self.RA)))
                print('Highz_catalogue::calc_crowdedness() Crowdedness = %g'%(Crowdedness))
            return Crowdedness
        return numpy.nan
    # 
    def calc_clean_index(self, input_ra, input_dec, input_radius):
        if self.RA is not None and self.Dec is not None:
            sep_dec = (numpy.array(self.Dec) - input_dec) * 3600.0 # arcsec
            sep_ra = (numpy.array(self.RA) - input_ra) * 3600.0 * numpy.cos(input_dec / 180.0 * numpy.pi)
            Clean_Index = numpy.sum((sep_ra**2 + sep_dec**2) <= (input_radius**2))
            return Clean_Index
        return numpy.nan
    # 
    def about(self):
        # 
        # get my name 
        self.World['My Name'] = ""
        for tmp_name, tmp_value in globals().items():
            if tmp_value is self:
                self.World['My Name'] = tmp_name
                break
    # 
    def __exit__(self, exc_type, exc_value, traceback):
        if(FitsTableStruct):
            self.FitsTableStruct.close()
















# 
class Highz_Image(object):
    """Highz_Image"""
    # 
    def __init__(self, FitsImageFile):
        # 
        if type(FitsImageFile) is list:
            if len(FitsImageFile)>0:
                self.FitsImageFile = FitsImageFile[0]
            else:
                print("Error! The input FitsImageFile is an empty list!")
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
        # check FitsImageFile
        if not os.path.isfile(self.FitsImageFile):
            print("Error! The input FitsImageFile \"%s\" was not found!\n"%(self.FitsImageFile))
            sys.exit()
        # 
        # read FitsImageFile with dzliu python class 'CrabFitsImage'
        self.FitsImagePointer = CrabFitsImage(self.FitsImageFile)
        self.Image = self.FitsImagePointer.getImage()
        self.Dimension = self.FitsImagePointer.getDimension()
        self.WCS = self.FitsImagePointer.getWCS()
        self.PixScale = self.FitsImagePointer.getPixScale()
        # 
        # prepare image background statistics
        self.Background_mu = numpy.nan
        self.Background_sigma = numpy.nan
        self.Background_method = 'N/A'
        # 
        # prepare source aper phot
        self.Apertures = []
        # 
        # plot
        self.PlotDevice = None
        self.PlotPanel = None
        self.PlotImage = None
        self.PlotTexts = None
        self.ZoomScale = None
        self.ZoomImage = None
        self.ZoomSize = None
        self.ZoomRect = None
        self.ZoomWCS = None
        # 
        # world
        self.World = {}
        self.World['Is Valid'] = (self.FitsImagePointer is not None)
    # 
    def isValid(self):
        return self.World['Is Valid']
    # 
    def sky2xy(self, input_ra, input_dec):
        if self.ZoomWCS is not None:
            internal_wcs = self.ZoomWCS
        else:
            internal_wcs = self.WCS
        output_x, output_y = internal_wcs.wcs_world2pix(input_ra, input_dec, 1) # 3rd arg: origin is the coordinate in the upper left corner of the image. In FITS and Fortran standards, this is 1. In Numpy and C standards this is 0.
        if type(input_ra) is not list and type(input_ra) is not numpy.ndarray and \
           type(input_dec) is not list and type(input_dec) is not numpy.ndarray :
            return output_x.flatten().tolist()[0], output_y.flatten().tolist()[0] # return a tuple
        else:
            return numpy.column_stack((output_x, output_y)) # return a numpy.ndarray
    # 
    def xy2sky(self, input_x, input_y):
        if self.ZoomWCS is not None:
            internal_wcs = self.ZoomWCS
        else:
            internal_wcs = self.WCS
        output_ra, output_dec = internal_wcs.wcs_pix2world(input_x, input_y, 1) # 3rd arg: origin is the coordinate in the upper left corner of the image. In FITS and Fortran standards, this is 1. In Numpy and C standards this is 0.
        if type(input_x) is not list and type(input_x) is not numpy.ndarray and \
           type(input_y) is not list and type(input_y) is not numpy.ndarray :
            return output_ra.flatten().tolist()[0], output_dec.flatten().tolist()[0] # return a tuple
        else:
            return numpy.column_stack((output_ra, output_dec)) # return a numpy.ndarray
    # 
    def plot(self, zoom_rect=[], zoom_center=[], zoom_size=[]):
        # zoom the plot according to the zoom_rect
        if type(zoom_rect) is tuple:
            zoom_rect = list(zoom_rect)
        if type(zoom_center) is tuple:
            zoom_center = list(zoom_center)
        if type(zoom_size) is tuple:
            zoom_size = list(zoom_size)
        if type(zoom_rect) is numpy.ndarray:
            zoom_rect = zoom_rect.flatten().tolist()
        if type(zoom_center) is numpy.ndarray:
            zoom_center = zoom_center.flatten().tolist()
        if type(zoom_size) is numpy.ndarray:
            zoom_size = zoom_size.flatten().tolist()
        if type(zoom_rect) is not list:
            zoom_rect = [zoom_rect]
        if type(zoom_center) is not list:
            zoom_center = [zoom_center]
        if type(zoom_size) is not list:
            zoom_size = [zoom_size]
        if len(zoom_rect) != 4 and len(zoom_center) == 2 and len(zoom_size) >= 1:
            if len(zoom_size) == 1: zoom_size = [zoom_size[0], zoom_size[0]]
            zoom_rect = [ numpy.round(zoom_center[0]-(zoom_size[0]/2.0)).astype(long), 
                          numpy.round(zoom_center[0]+(zoom_size[0]/2.0)).astype(long), 
                          numpy.round(zoom_center[1]-(zoom_size[1]/2.0)).astype(long), 
                          numpy.round(zoom_center[1]+(zoom_size[1]/2.0)).astype(long) ]
        #print(zoom_center, type(zoom_center), len(zoom_center))
        #print(zoom_size, type(zoom_size), len(zoom_size))
        #print(zoom_rect, type(zoom_rect), len(zoom_rect))
        if len(zoom_rect) == 4:
            zoom_size = [ numpy.round((zoom_rect[1]-zoom_rect[0]+1)), 
                          numpy.round((zoom_rect[3]-zoom_rect[2]+1)) ]
            zoom_center = [ numpy.round((zoom_rect[1]+zoom_rect[0])/2.0), 
                            numpy.round((zoom_rect[3]+zoom_rect[2])/2.0) ]
            self.ZoomSize = zoom_size
            self.ZoomRect = zoom_rect
            self.ZoomImage, self.ZoomWCS = crop(self.Image, self.ZoomRect, imagewcs = self.WCS) # rect is x1 x2 y1 y2
            self.ZoomScale = numpy.divide(numpy.array(self.ZoomImage.shape,dtype=float), numpy.array(self.Image.shape,dtype=float))
            print("Plotting fits image \"%s\" with FoV %.3f %.3f arcsec (size %ld %ld) around Center %.3f %.3f with Rect %s"%(self.FitsImageFile, zoom_size[0] * self.PixScale[0], zoom_size[1] * self.PixScale[1], zoom_size[0], zoom_size[1], zoom_center[0], zoom_center[1], zoom_rect))
        else:
            self.ZoomSize = []
            self.ZoomRect = []
            self.ZoomImage = self.Image
            self.ZoomWCS = self.WCS
            self.ZoomScale = numpy.array([1.0, 1.0])
            print("Plotting fits image \"%s\" with FoV %.3f %.3f arcsec (size %ld %ld)"%(self.FitsImageFile, self.Dimension[0] * self.PixScale[0], self.Dimension[1] * self.PixScale[1], self.Dimension[0], self.Dimension[1]))
        # 
        # plot frame
        self.PlotDevice = pyplot.figure(figsize=(9.0,8.0), dpi=90) # set figure size 9.0 x 8.0 inches, 90 pixels per inch. 
        self.PlotPanel = self.PlotDevice.add_axes([0.10, 0.10, 0.85, 0.85], projection = self.ZoomWCS) # plot RA Dec axes #  PlotPanel = PlotDevice.add_subplot(1,1,1)
        self.PlotPanel.set_xlabel('RA')
        self.PlotPanel.set_ylabel('Dec')
        self.PlotPanel.set_aspect('equal')
        self.PlotPanel.coords[0].set_ticks(size=8, width=1.35, exclude_overlapping=True)
        self.PlotPanel.coords[1].set_ticks(size=8, width=1.35, exclude_overlapping=True)
        self.PlotPanel.coords[0].set_major_formatter('hh:mm:ss.ss') # https://wcsaxes.readthedocs.io/en/latest/ticks_labels_grid.html
        self.PlotPanel.coords[1].set_major_formatter('dd:mm:ss.s') # https://wcsaxes.readthedocs.io/en/latest/ticks_labels_grid.html
        self.PlotPanel.coords[0].ticks.display_minor_ticks(True) # http://docs.astropy.org/en/latest/_modules/astropy/visualization/wcsaxes/coordinate_helpers.html?highlight=zip
        self.PlotPanel.coords[1].ticks.display_minor_ticks(True) # http://docs.astropy.org/en/latest/_modules/astropy/visualization/wcsaxes/coordinate_helpers.html?highlight=zip
        self.PlotPanel.coords[0].set_separator(':')
        self.PlotPanel.coords[1].set_separator(':')
        self.PlotPanel.coords[0].set_minor_frequency(10) # http://docs.astropy.org/en/stable/api/astropy.visualization.wcsaxes.CoordinateHelper.html
        self.PlotPanel.coords[1].set_minor_frequency(10) # http://docs.astropy.org/en/stable/api/astropy.visualization.wcsaxes.CoordinateHelper.html
        # 
        # calc image mean and stddev
        # check FitsImageFile+'.pixel.statistics.txt'
        background_mu = numpy.nan
        background_sigma = numpy.nan
        background_method = 'N/A'
        if not os.path.isfile(self.FitsImageFile+'.pixel.statistics.txt'):
            os.system('%s "%s"'%('caap_analyze_fits_image_pixel_histogram.py', self.FitsImageFile))
        with open(self.FitsImageFile+'.pixel.statistics.txt', 'r') as fp:
            for lp in fp:
                if lp.startswith('Gaussian_mu'):
                    background_mu = float((lp.split('=')[1]).split('#')[0].replace(' ',''))
                elif lp.startswith('Gaussian_sigma'):
                    background_sigma = float((lp.split('=')[1]).split('#')[0].replace(' ',''))
                    background_method = 'Gaussian_sigma'
        # 
        # <20170224> added a check step to make sure we measure the FitGauss
        if background_sigma is numpy.nan or background_sigma < 0:
            os.system('%s "%s"'%('caap_analyze_fits_image_pixel_histogram.py', self.FitsImageFile))
            with open(self.FitsImageFile+'.pixel.statistics.txt', 'r') as fp:
                for lp in fp:
                    if lp.startswith('Gaussian_mu'):
                        background_mu = float((lp.split('=')[1]).split('#')[0].replace(' ',''))
                    elif lp.startswith('Gaussian_sigma'):
                        background_sigma = float((lp.split('=')[1]).split('#')[0].replace(' ',''))
                        background_method = 'Gaussian_sigma'
        # 
        # <20170427> fall back to Inner_sigma
        if background_sigma is numpy.nan or background_sigma < 0:
            #os.system('%s "%s"'%('caap_analyze_fits_image_pixel_histogram.py', self.FitsImageFile))
            with open(self.FitsImageFile+'.pixel.statistics.txt', 'r') as fp:
                for lp in fp:
                    if lp.startswith('Inner_mu'):
                        background_mu = float((lp.split('=')[1]).split('#')[0].replace(' ',''))
                    elif lp.startswith('Inner_sigma'):
                        background_sigma = float((lp.split('=')[1]).split('#')[0].replace(' ',''))
                        background_method = 'Inner_sigma'
        # 
        self.Background_mu = background_mu
        self.Background_sigma = background_sigma
        self.Background_method = background_method
        # 
        # 
        # plot image
        self.PlotImage = self.PlotPanel.imshow(self.ZoomImage, origin = 'lower', cmap = 'binary', aspect = 'equal', 
                norm = ImageNormalize(self.ZoomImage, vmin=self.Background_mu-0.5*self.Background_sigma, vmax=self.Background_mu+3.0*self.Background_sigma)
            )
        #PlotDevice.colorbar(PlotImage)
        # 
        # show
        self.PlotDevice.show()
        #self.PlotDevice.waitforbuttonpress()
    # 
    def aper(self, label='no name', radec=[], position=[], major=numpy.nan, minor=numpy.nan, angle=numpy.nan, 
             color='green', edgecolor='', facecolor='', linewidth=2, 
             alpha=1.0, edgealpha=numpy.nan, facealpha=0.0, zorder=10, 
             draw_ellipse = True, draw_cross = False):
        # 
        # parse input arguments as list
        if type(position) is numpy.ndarray:
            position = position.tolist()
        if type(radec) is numpy.ndarray:
            radec = radec.tolist()
        if len(radec) == 2:
            position = self.sky2xy(radec[0],radec[1])
        elif len(position) == 2:
            radec = self.xy2sky(position[0], position[1])
        # 
        # solve color arguments
        if edgecolor == '':
            edgecolor = color
        if facecolor == '':
            facecolor = color
        if edgecolor == 'none' and facecolor == 'none':
            draw_ellipse = False
        if color == 'none':
            draw_cross = False
        # 
        # solve alpha arguments
        if numpy.isnan(edgealpha) and not numpy.isnan(alpha):
            edgealpha = alpha
        # 
        # do aperture photometry if self.PixScale is valid
        if numpy.isnan(self.PixScale[0]) == False and numpy.isnan(self.PixScale[1]) == False:
            # 
            # convert major minor from arcsec to pix unit
            pix_major = major * numpy.sqrt( (numpy.cos(angle/180.0*numpy.pi)/self.PixScale[0])**2 + (numpy.sin(angle/180.0*numpy.pi)/self.PixScale[1])**2 )
            pix_minor = minor * numpy.sqrt( (numpy.sin(angle/180.0*numpy.pi)/self.PixScale[0])**2 + (numpy.cos(angle/180.0*numpy.pi)/self.PixScale[1])**2 )
            pix_angle = angle
            pix_posxy = position
            pix_area = numpy.pi * pix_major/2.0 * pix_minor/2.0
            area = numpy.pi * major/2.0 * minor/2.0 # pix_major * pix_minor * self.PixScale[0] * self.PixScale[1]
            # 
            # print aperture info
            print('Plotting aperture "%s" at position %0.3f %0.3f (RA Dec %0.10f %0.10f) with major minor %0.3f %0.3f pix (%0.3f %0.3f arcsec) angle %0.3f deg'%(label, position[0], position[1], radec[0], radec[1], pix_major, pix_minor, major, minor, angle))
            # 
            # draw Ellipse (with transparancy according to the input alpha arguments)
            if facealpha > 0.0:
                # draw a filled ellipse with transparancy
                pix_ellipse2 = Ellipse(xy=pix_posxy, width=pix_major, height=pix_minor, angle=pix_angle, edgecolor='none', facecolor=facecolor, linewidth=linewidth, alpha=facealpha, zorder=zorder)
                pix_ellipse = Ellipse(xy=pix_posxy, width=pix_major, height=pix_minor, angle=pix_angle, edgecolor=edgecolor, facecolor='none', linewidth=linewidth, alpha=edgealpha, zorder=zorder)
                if draw_ellipse:
                    self.PlotPanel.add_artist(pix_ellipse2)
                    self.PlotPanel.add_artist(pix_ellipse)
                    self.PlotDevice.canvas.draw()
            else:
                # draw a open ellipse
                pix_ellipse = Ellipse(xy=pix_posxy, width=pix_major, height=pix_minor, angle=pix_angle, edgecolor=edgecolor, facecolor='none', linewidth=linewidth, alpha=edgealpha, zorder=zorder)
                if draw_ellipse:
                    self.PlotPanel.add_artist(pix_ellipse)
                    self.PlotDevice.canvas.draw()
            # 
            # draw Cross
            if draw_cross:
                pix_line_x1 = matplotlib.lines.Line2D([pix_posxy[0]+0.25/self.PixScale[0],pix_posxy[0]+1.00/self.PixScale[0]], 
                                                      [pix_posxy[1]+0.00/self.PixScale[1],pix_posxy[1]+0.00/self.PixScale[1]], color=color, linewidth=linewidth, alpha=alpha, zorder=zorder)
                pix_line_x2 = matplotlib.lines.Line2D([pix_posxy[0]-0.25/self.PixScale[0],pix_posxy[0]-1.00/self.PixScale[0]], 
                                                      [pix_posxy[1]+0.00/self.PixScale[1],pix_posxy[1]+0.00/self.PixScale[1]], color=color, linewidth=linewidth, alpha=alpha, zorder=zorder)
                pix_line_y1 = matplotlib.lines.Line2D([pix_posxy[0]+0.00/self.PixScale[0],pix_posxy[0]+0.00/self.PixScale[0]], 
                                                      [pix_posxy[1]+0.25/self.PixScale[1],pix_posxy[1]+1.00/self.PixScale[1]], color=color, linewidth=linewidth, alpha=alpha, zorder=zorder)
                pix_line_y2 = matplotlib.lines.Line2D([pix_posxy[0]+0.00/self.PixScale[0],pix_posxy[0]+0.00/self.PixScale[0]], 
                                                      [pix_posxy[1]-0.25/self.PixScale[1],pix_posxy[1]-1.00/self.PixScale[1]], color=color, linewidth=linewidth, alpha=alpha, zorder=zorder)
                #pix_cross = self.PlotPanel.plot([pix_posxy[0]], [pix_posxy[1]], marker='+', markeredgewidth=1.85, markersize=numpy.mean(3.0/self.PixScale), color=color, zorder=zorder)
                #markersize=numpy.mean(0.06*self.PlotDevice.get_size_inches()*self.PlotDevice.dpi/self.PixScale)
                self.PlotPanel.add_line(pix_line_x1)
                self.PlotPanel.add_line(pix_line_x2)
                self.PlotPanel.add_line(pix_line_y1)
                self.PlotPanel.add_line(pix_line_y2)
                self.PlotDevice.canvas.draw()
            # 
            # do aperture photometry
            verbose = True
            if self.ZoomImage is not None:
                flux, pix_number, pix_centroid = elliptical_Photometry(self.ZoomImage, pix_ellipse, imagewcs=self.ZoomWCS, verbose=verbose)
            else:
                flux, pix_number, pix_centroid = elliptical_Photometry(self.Image, pix_ellipse, imagewcs=self.WCS, verbose=verbose)
            # 
            # calculate flux-weighted centroid (RA Dec)
            centroid = self.xy2sky(pix_centroid[0], pix_centroid[1])
            # 
            self.Apertures.append(
                    { 
                        'Ellipse': pix_ellipse, 
                        'X': pix_posxy[0], 
                        'Y': pix_posxy[1], 
                        'RA': radec[0], 
                        'Dec': radec[1], 
                        'Major': major, 
                        'Minor': minor, 
                        'Angle': angle, 
                        'Area': area, 
                        'Pixel Area': pix_area, 
                        'Pixel Number': pix_number, 
                        'Pixel Centroid': pix_centroid, 
                        'Centroid': centroid, 
                        'Flux': flux, 
                        'Noise': self.Background_sigma * numpy.sqrt(float(pix_number)), 
                        'Background': self.Background_mu * float(pix_number), 
                        'Label': label
                    }
                )
            # 
        # 
        # show
        self.PlotDevice.show()
        #self.PlotDevice.waitforbuttonpress()
    # 
    def get_aperture_by_label(self, label):
        for one_aperture in self.Apertures:
            if label.find('*')>=0:
                if re.match(label, one_aperture['Label']):
                    return one_aperture
            else:
                if one_aperture['Label'].find(label) >= 0:
                    return one_aperture
        return None
    # 
    def text(self, input_text, align_xy = [], align_top_right = True, align_top_left = False, 
                   text_box_alpha = 0.8, text_box_color = hex2color('#FFFFFF'), 
                   line_spacing = 0.042, fontsize = 14, color = hex2color('#00CC00'), 
                   horizontalalignment = 'left', verticalalignment = 'center'):
        if self.PlotPanel:
            # parse the input align_xy as a list
            if type(align_xy) is numpy.ndarray:
                align_xy = align_xy.flatten().tolist()
            if type(align_xy) is not list:
                align_xy = [align_xy]
            # solve conflicting input arguments
            if align_top_right and align_top_left:
                align_top_right = False
                align_top_left = True
            # make sure align_xy has a dimension of 2
            if len(align_xy) < 2:
                if align_top_right:
                    align_xy = [0.97, 0.95]
                elif align_top_left:
                    align_xy = [0.03, 0.95]
            if len(align_xy) > 2:
                align_xy = align_xy[0:1]
            if len(align_xy) == 2:
                # skip existing text lines by line_spacing
                if self.PlotTexts:
                    for plot_text in self.PlotTexts:
                        if align_top_right and plot_text['align_top_right']:
                            align_xy[1] = align_xy[1] - float(line_spacing)
                        elif align_top_left and plot_text['align_top_left']:
                            align_xy[1] = align_xy[1] - float(line_spacing)
                # draw annotate
                self.PlotPanel.annotate(
                    input_text, 
                    xy = align_xy, xycoords = 'axes fraction', 
                    fontsize = fontsize, color = color, 
                    bbox = dict(boxstyle="round,pad=0.2", alpha=text_box_alpha, facecolor=text_box_color, edgecolor=text_box_color, linewidth=1), 
                    horizontalalignment = horizontalalignment, verticalalignment = verticalalignment
                )
                if self.PlotTexts:
                    self.PlotTexts.append( {'Text': input_text, 'align_xy': align_xy, 'align_top_right': align_top_right, 'align_top_left': align_top_left} )
                else:
                    self.PlotTexts = [ {'Text': input_text, 'align_xy': align_xy, 'align_top_right': align_top_right, 'align_top_left': align_top_left} ]
        # 





























