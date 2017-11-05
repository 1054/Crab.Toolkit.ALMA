#!/usr/bin/env python2.7
# 

import os, sys

sys.path.insert(1,os.path.abspath(os.path.dirname(sys.argv[0]))+os.sep+'3rd_party'+os.sep+'python_packages'+os.sep+'lib'+os.sep+'python2.7'+os.sep+'site-packages'+os.sep+'bdsf-1.8.12-py2.7-macosx-10.12-x86_64.egg')
sys.path.insert(1,os.path.abspath(os.path.dirname(sys.argv[0]))+os.sep+'3rd_party'+os.sep+'python_packages'+os.sep+'lib'+os.sep+'python2.7'+os.sep+'site-packages')
#print sys.path

import numpy
import scipy
import bdsf

input_fits_files = []
input_list_files = []
input_loop_start = -1
input_loop_end = -1

for i in range(1,len(sys.argv)):
    if sys.argv[i].endswith('.fits') or sys.argv[i].endswith('.FITS'):
        if os.path.isfile(sys.argv[i]):
            input_fits_files.append(sys.argv[i])
        else:
            print('%s'%('*'*80))
            print('Warning! "%s" was not found!'%(sys.argv[i]))
            print('')
    elif sys.argv[i].startswith('-'):
        if sys.argv[i] == '-start':
            if i+1 <= len(sys.argv)-1:
                input_loop_start = long(sys.argv[i+1])
        elif sys.argv[i] == '-end':
            if i+1 <= len(sys.argv)-1:
                input_loop_end = long(sys.argv[i+1])
    else:
        if os.path.isfile(sys.argv[i]):
            with open(sys.argv[i]) as fp:
                input_list_files = fp.readlines()
                for lp in input_list_files:
                    input_fits_file = lp.strip()
                    if input_fits_file.endswith('.fits') or input_fits_file.endswith('.FITS'):
                        if lp.find('/')==0 or lp.find('~')==0 or lp.find('$')==0:
                            input_fits_file = input_fits_file
                        else:
                            input_fits_file = os.path.abspath(os.path.dirname(sys.argv[i])) + os.sep + input_fits_file
                        input_fits_files.append(input_fits_file)
                    else:
                        print('%s'%('*'*80))
                        print('Warning! "%s" is not a FITS file!'%(input_fits_file))
                        print('')
        else:
            print('%s'%('*'*80))
            print('Warning! "%s" was not found!'%(sys.argv[i]))
            print('')


for i in range(len(input_fits_files)):
    # 
    # loop control
    if input_loop_start >=0:
        if i < input_loop_start:
            continue
    if input_loop_end >=0:
        if i > input_loop_end:
            break
    # 
    # process fits file
    input_fits_file = input_fits_files[i]
    print('%s'%('*'*80))
    print('Processing "%s"'%(input_fits_file))
    fit_result = bdsf.process_image(input_fits_file, thresh_isl = 2.0, thresh_pix = 3.5) # rms_map=False, rms_value=1e-5, 
    fit_result.write_catalog(outfile = 'pybdsm_cat.fits', clobber = True) # clobber = True means overwrite existing file. 
    fit_result.write_catalog(outfile = 'pybdsm_cat.ds9.reg', format = 'ds9', clobber = True)
    fit_result.export_image(outfile = 'pybdsm_img_gaus_resid.fits',        img_type = 'gaus_resid',       clobber = True) # Gaussian model residual image
    fit_result.export_image(outfile = 'pybdsm_img_rms.fits',               img_type = 'rms',              clobber = True)
    fit_result.export_image(outfile = 'pybdsm_img_mean.fits',              img_type = 'mean',             clobber = True)
    fit_result.export_image(outfile = 'pybdsm_img_gaus_model.fits',        img_type = 'gaus_model',       clobber = True) # Gaussian model image
    fit_result.export_image(outfile = 'pybdsm_img_island_mask.fits',       img_type = 'island_mask',      clobber = True) # Island mask image (0 = outside island, 1 = inside island)
    fit_result.export_image(outfile = 'pybdsm_img_ch0.fits',               img_type = 'ch0',              clobber = True) # image used for source detection

    print('\n')






