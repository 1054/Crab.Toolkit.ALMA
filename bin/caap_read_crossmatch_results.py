#!/usr/bin/env python
# 

import os, sys
import numpy
import astropy
import astropy.io.ascii as asciitable

from a_dzliu_python_lib_highz import *

crossmatch_TableFile = 'Match_cycle2_new_detections_1.5arcsec.fits'

crossmatch_TableData = CrabFitsTable(crossmatch_TableFile)

list_Obj = crossmatch_TableData.getColumn('OBJECT')
list_Sid = crossmatch_TableData.getColumn('SUBID_TILE')
list_SNR = crossmatch_TableData.getColumn('SNR_FIT')
list_Sep = crossmatch_TableData.getColumn('Separation')
list_z = crossmatch_TableData.getColumn('PHOTOZ')
list_Score_Total = []
list_Score_Morph = []
list_Score_Photo = []
list_Score_Exten = []

for i in range(len(list_Obj)):
    temp_Score_Total = numpy.nan
    temp_Score_Morph = numpy.nan
    temp_Score_Photo = numpy.nan
    temp_Score_Exten = numpy.nan
    temp_Score_File = 'results/COSMOS--%s--%s--HST--ACS.txt'%(list_Obj[i], list_Sid[i])
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
    

# result_data_table_array = numpy.rec.fromarrays( (list_Obj, list_Sid, list_SNR, list_Sep, list_z), 
#                                                 dtype = [("OBJECT", 'S'), ("SUBID_TILE", 'i8'), ("SNR_FIT", 'f8'), ("Separation", 'f8'), ("PHOTOZ", 'f8')], 
#                                               )
# 
# 
# result_data_table_array = numpy.lib.recfunctions.append_fields( result_data_table_array, \
#                                                                 ["Score_Total", "Score_Morph", "Score_Photo", "Score_Exten"], 
#                                                                 (list_Score_Total, list_Score_Morph, list_Score_Photo, list_Score_Exten), 
#                                                                 usemask = False, 
#                                                               )
# 

# result_data_table_array = numpy.rec.fromarrays( (list_Obj, list_Sid, list_SNR, list_Sep, list_z, list_Score_Total, list_Score_Morph, list_Score_Photo, list_Score_Exten), 
#                                                 dtype = [ ("OBJECT", object), ("SUBID_TILE", 'i8'), ("SNR_FIT", 'f8'), ("Separation", 'f8'), ("PHOTOZ", 'f8'), 
#                                                           ("Score_Total", 'f8'), ("Score_Morph", 'f8'), ("Score_Photo", 'f8'), ("Score_Exten", 'f8') ], 
#                                               )


# asciitable.write( result_data_table_array, 
#                     sys.stdout, Writer=asciitable.FixedWidthTwoLine )


# compute the header object column string max length
strlen_Obj = 0
for i in range(len(list_Obj)):
    if strlen_Obj < len(list_Obj[i]):
        strlen_Obj = len(list_Obj[i])

output_Txt = crossmatch_TableFile.replace('.fits','_crossmatched_scores.txt')
with open(output_Txt, 'w') as fp:
    # print header
    fmt = '# {:<%ds} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s}\n'%(strlen_Obj)
    fp.write( fmt.format("OBJECT", "SUBID_TILE", "SNR_FIT", "Separation", "PHOTOZ", "Score_Total", "Score_Morph", "Score_Photo", "Score_Exten") )
    fp.write( "# \n" )
    # loop each source
    for i in range(len(list_Obj)):
        fmt = '  {:<%ds} {:12d} {:12.3f} {:12.3f} {:12.4f} {:12g} {:12g} {:12g} {:12g}\n'%(strlen_Obj)
        fp.write( fmt.format(list_Obj[i], list_Sid[i], list_SNR[i], list_Sep[i], list_z[i], \
                    float(list_Score_Total[i]), float(list_Score_Morph[i]), float(list_Score_Photo[i]), float(list_Score_Exten[i])) )
    fp.close()

print("Output to \"%s\"!"%(output_Txt))


