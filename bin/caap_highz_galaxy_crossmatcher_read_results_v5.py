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


for band in ['HST--ACS', 'Spitzer--IRAC-ch1', 'Spitzer--IRAC-ch2', 'Spitzer--IRAC-ch3', 'Spitzer--IRAC-ch4', 'UltraVISTA--J', 'UltraVISTA--H', 'UltraVISTA--Ks']: 
    
    list_Score_Total = []
    list_Score_Morph = []
    list_Score_Photo = []
    list_Score_Exten = []
    
    for i in range(len(list_Obj)):
        # fix list_Obj empty
        if list_Obj[i] == '':
            list_Obj[i] = '__'
        # read result file
        temp_Score_Total = numpy.nan
        temp_Score_Morph = numpy.nan
        temp_Score_Photo = numpy.nan
        temp_Score_Exten = numpy.nan
        temp_Score_File = 'results/%d--%s.txt'%(i, band)
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
                fp.close()
        else:
            print("Warning! \"%s\" was not found for source \"%s\"!"%(temp_Score_File, list_Obj[i]))
        list_Score_Total.append(temp_Score_Total)
        list_Score_Morph.append(temp_Score_Morph)
        list_Score_Photo.append(temp_Score_Photo)
        list_Score_Exten.append(temp_Score_Exten)
        
    
    
    # compute the header object column string max length
    strlen_Obj = 0
    for i in range(len(list_Obj)):
        if strlen_Obj < len(list_Obj[i]):
            strlen_Obj = len(list_Obj[i])
    
    output_Txt = crossmatch_TableFile.replace('.fits','_crossmatched_scores_'+band.replace('--','_')+'.txt')
    with open(output_Txt, 'w') as fp:
        # print header
        fmt = '# {:<10s} {:<%ds} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s}\n'%(strlen_Obj)
        fp.write( fmt.format("INDEX", "OBJECT", "SUBID_TILE", "SNR_FIT", "Separation", "PHOTOZ", "Score_Total", "Score_Morph", "Score_Photo", "Score_Exten") )
        fp.write( "# \n" )
        # loop each source
        for i in range(len(list_Obj)):
            fmt = '  {:<10d} {:<%ds} {:12d} {:12.3f} {:12.3f} {:12.4f} {:12g} {:12g} {:12g} {:12g}\n'%(strlen_Obj)
            fp.write( fmt.format(i, list_Obj[i], list_Sid[i], list_SNR[i], list_Sep[i], list_z[i], \
                        float(list_Score_Total[i]), float(list_Score_Morph[i]), float(list_Score_Photo[i]), float(list_Score_Exten[i])) )
        fp.close()
    
    print("Output to \"%s\"!"%(output_Txt))


