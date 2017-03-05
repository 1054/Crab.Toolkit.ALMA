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

import os
import sys
import glob
import inspect
import math
import numpy
import astropy
from astropy import units
from astropy.io import fits












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
        if type(ColNameOrNumb) is str:
            if ColNameOrNumb in self.TableHeaders:
                return self.TableData.field(ColNameOrNumb)
            else:
                print("Error! Column name \"%s\" was not found in the data table!"%(ColNameOrNumb))
                return []
        else:
            if ColNameOrNumb >= 0 and ColNameOrNumb < len(self.TableHeaders):
                #<BUGGY><FIXED><20170210># return self.TableData[int(ColNameOrNumb)]
                return self.TableData.field(self.TableHeaders[int(ColNameOrNumb)])
            else:
                print("Error! Column number %d is out of allowed range (0 - %d)!"%(int(ColNameOrNumb),len(self.TableHeaders)-1))
                return []
    # 
    def setColumn(self, ColNameOrNumb, DataArray):
        if type(ColNameOrNumb) is str:
            if ColNameOrNumb in self.TableHeaders:
                self.TableData[ColNameOrNumb] = DataArray
            else:
                print("Error! Column name \"%s\" was not found in the data table!"%(ColNameOrNumb))
                return
        else:
            if ColNameOrNumb >= 0 and ColNameOrNumb < len(self.TableHeaders):
                #<BUGGY><FIXED><20170210># self.TableData[int(ColNameOrNumb)] = DataArray
                self.TableData[self.TableHeaders[int(ColNameOrNumb)]] = DataArray
            else:
                print("Error! Column number %d is out of allowed range (0 - %d)!"%(int(ColNameOrNumb),len(self.TableHeaders)-1))
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
        self.FitsTableCrab = CrabFitsTable(FitsTableFile)
        self.World = {}
        if self.FitsTableCrab:
            self.TableData = self.FitsTableCrab.getData()
            self.TableHeaders = self.FitsTableCrab.getColumnNames()
            self.World['Is Valid'] = True
        else:
            self.TableData = []
            self.TableHeaders = []
            self.World['Is Valid'] = False
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

































