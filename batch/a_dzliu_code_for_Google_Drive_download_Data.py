#!/usr/bin/env python2.7
# 

import os, sys

caap_bin_dir = os.path.expanduser('~')+'/Cloud/Github/Crab.Toolkit.CAAP/bin'
if not os.path.isdir(caap_bin_dir):
    print('Error! Software dependency missing! "%s" was not found!'%(caap_bin_dir))
    print('Please clone "https://github.com/1054/Crab.Toolkit.CAAP" into "~/Cloud/Github/" then run this code again!')
    sys.exit()

sys.path.append(os.path.expanduser('~')+'/Cloud/Github/Crab.Toolkit.CAAP/bin')

from caap_google_drive_operator import CAAP_Google_Drive_Operator



# 
# Main Code
# 
if len(sys.argv)>1:
    gdo = CAAP_Google_Drive_Operator()
    for i in range(len(sys.argv)-1):
        j=i+1
        #files = gdo.get_file_by_name('Photometry/ALMA_full_archive/Blind_Extraction_by_Benjamin/20170930/Output_Residual_Images/%s.cont.I.residual.fits'%(sys.argv[j]), verbose = False)
        files = gdo.get_file_by_name(sys.argv[j], verbose = False)
        #files = gdo.get_file_by_name('A-COSMOS_blind_2017-07-12_temporary.fits')
        if len(files)>0:
            #print(files)
            gdo.download_files(files)
        else:
            print('***************************')
            print('Warning! Nothing was found for the input name "%s"!'%(sys.argv[j]))
            print('***************************')
            print('')
else:
    print('Usage: ')
    print('       ./a_dzliu_code_for_Google_Drive_download_Data.py 2012.1.00076.S_SB5_GB1_MB1_ID247_sci.spw0_1_2_3')






