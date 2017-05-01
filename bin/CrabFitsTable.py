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
#   Last update: 
#            20170226 02h30m -- Fixed getColumn(number), number starts from 1. 
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






























