#!/usr/bin/env python
# 

import os, sys

if len(sys.argv) <= 1:
    print("Usage: caap_read_crossmatch_results.py \"topcat_crossmatched_catalog.fits\"")
    sys.exit()



import numpy
import astropy
import astropy.io.ascii as asciitable

from caap_python_lib_highz import *

crossmatch_TableFile = sys.argv[1] # 'Match_cycle2_new_detections_1.5arcsec.fits'

crossmatch_TableData = CrabFitsTable(crossmatch_TableFile)

list_Obj = crossmatch_TableData.getColumn('OBJECT')
list_Sid = crossmatch_TableData.getColumn('SUBID_TILE')
list_SNR = crossmatch_TableData.getColumn('SNR_FIT')
list_Sep = crossmatch_TableData.getColumn('Separation')
if 'ZPDF' in crossmatch_TableData.getColumnNames():
    list_z = crossmatch_TableData.getColumn('ZPDF')
else:
    list_z = list_SNR*0.0 -99.0


list_band = ['HST--ACS', 'Spitzer--IRAC-ch1', 'Spitzer--IRAC-ch2', 'Spitzer--IRAC-ch3', 'Spitzer--IRAC-ch4', 'UltraVISTA--J', 'UltraVISTA--H', 'UltraVISTA--Ks']
#list_band = ['HST--ACS', 'UltraVISTA--J', 'UltraVISTA--H', 'UltraVISTA--Ks']

for band in list_band: 
    
    list_Score_Total = []
    list_Score_Morph = []
    list_Score_Photo = []
    list_Score_Exten = []
    list_Crowdedness = []
    list_Clean_Index = []
    list_Sep_Counterpart = []
    list_Ang_Counterpart = []
    list_Sep_Centroid = []
    list_Ang_Centroid = []
    
    for i in range(len(list_Obj)):
        # fix list_Obj empty
        if list_Obj[i] == '':
            list_Obj[i] = '__'
        # fix list_Obj white space
        if list_Obj[i].find(' ')>=0:
            list_Obj[i] = list_Obj[i].replace(' ','_')
        # read result file
        temp_Score_Total = numpy.nan
        temp_Score_Morph = numpy.nan
        temp_Score_Photo = numpy.nan
        temp_Score_Exten = numpy.nan
        temp_Crowdedness = numpy.nan
        temp_Clean_Index = numpy.nan
        temp_Sep_Counterpart = numpy.nan
        temp_Ang_Counterpart = numpy.nan
        temp_Sep_Centroid = numpy.nan
        temp_Ang_Centroid = numpy.nan
        temp_Position = []
        temp_Centroid = []
        temp_Score_File = 'results/%d--%s.txt'%(i, band) # file name starts with index i, i starts from 0. 
        if os.path.isfile(temp_Score_File):
            with open(temp_Score_File, 'r') as fp:
                for lp in fp:
                    if lp.startswith('Match.Score'):
                        temp_Score_Total = (lp.split('=')[1]).split('#')[0]
                    elif lp.startswith('Match.Morphology.Score'):
                        temp_Score_Morph = (lp.split('=')[1]).split('#')[0]
                    elif lp.startswith('Match.Photometry.Score'):
                        temp_Score_Photo = (lp.split('=')[1]).split('#')[0]
                    elif lp.startswith('Match.Morphology.Extended'):
                        temp_Score_Exten = (lp.split('=')[1]).split('#')[0]
                    elif lp.startswith('Crowdedness'):
                        temp_Crowdedness = (lp.split('=')[1]).split('#')[0]
                    elif lp.startswith('Clean_Index'):
                        temp_Clean_Index = (lp.split('=')[1]).split('#')[0]
                    elif lp.startswith('Match.Morphology.SepDist'):
                        temp_Sep_Counterpart = (lp.split('=')[1]).split('#')[0]
                    elif lp.startswith('Match.Morphology.SepAngle'):
                        temp_Ang_Counterpart = (lp.split('=')[1]).split('#')[0]
                    elif lp.startswith('Match.Photometry.Position'):
                        temp_String = (lp.split('=')[1]).split('#')[0]
                        if temp_String.find('nan') < 0:
                            temp_Position = eval(temp_String) # should be the ALMA position
                        else:
                            print('Found nan in "%s"!'%(temp_Score_File))
                    elif lp.startswith('Match.Photometry.Centroid'):
                        temp_String = (lp.split('=')[1]).split('#')[0]
                        if temp_String.find('nan') < 0:
                            temp_Centroid = eval(temp_String) # the light-weighted centroid of the image
                        else:
                            print('Found nan in "%s"!'%(temp_Score_File))
                fp.close()
        else:
            print("Warning! \"%s\" was not found for source \"%s\"!"%(temp_Score_File, list_Obj[i]))
        list_Score_Total.append(temp_Score_Total)
        list_Score_Morph.append(temp_Score_Morph)
        list_Score_Photo.append(temp_Score_Photo)
        list_Score_Exten.append(temp_Score_Exten)
        list_Crowdedness.append(temp_Crowdedness)
        list_Clean_Index.append(temp_Clean_Index)
        if len(temp_Position) > 0 and len(temp_Centroid) > 0:
            temp_Sep_X = (temp_Centroid[0] - temp_Position[0]) * numpy.cos(temp_Position[1]/180.0*numpy.pi) * 3600.0
            temp_Sep_Y = (temp_Centroid[1] - temp_Position[1]) * 3600.0
            temp_Ang_Centroid = numpy.arctan2(temp_Sep_Y, temp_Sep_X) / numpy.pi * 180.0
            temp_Sep_Centroid = numpy.sqrt( (temp_Sep_X)**2 + (temp_Sep_Y)**2 )
        list_Sep_Counterpart.append(temp_Sep_Counterpart)
        list_Ang_Counterpart.append(temp_Ang_Counterpart)
        list_Sep_Centroid.append(temp_Sep_Centroid)
        list_Ang_Centroid.append(temp_Ang_Centroid)
        
    
    
    # compute the header object column string max length
    strlen_Obj = 0
    for i in range(len(list_Obj)):
        if strlen_Obj < len(list_Obj[i]):
            strlen_Obj = len(list_Obj[i])
    
    output_Txt = crossmatch_TableFile.replace('.fits','_crossmatched_scores_'+band.replace('--','_')+'.txt')
    with open(output_Txt, 'w') as fp:
        # print header
        fmt = '# {:<10s} {:<%ds} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s}\n'%(strlen_Obj)
        fp.write( fmt.format("INDEX", "OBJECT", "SUBID_TILE", "SNR_FIT", "Separation", "PHOTOZ", "Score_Total", "Score_Morph", "Score_Photo", "Score_Exten", "Crowdedness", "Clean_Index") )
        fp.write( "# \n" )
        # loop each source
        for i in range(len(list_Obj)):
            fmt = '  {:<10d} {:<%ds} {:12d} {:12.3f} {:12.3f} {:12.4f} {:12g} {:12g} {:12g} {:12g} {:12g} {:12g}\n'%(strlen_Obj)
            fp.write( fmt.format( i, list_Obj[i], list_Sid[i], list_SNR[i], list_Sep[i], list_z[i], \
                                  float(list_Score_Total[i]), float(list_Score_Morph[i]), float(list_Score_Photo[i]), float(list_Score_Exten[i]) , \
                                  float(list_Crowdedness[i]), float(list_Clean_Index[i])
                                )
                    )
        fp.close()
    
    print("Output to \"%s\"!"%(output_Txt))


