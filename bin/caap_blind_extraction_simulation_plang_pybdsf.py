#!/usr/bin/env python2.7
# 

import os, sys, re
import numpy
import astropy
from astropy.io import fits

# pip-2.7 install --user pidly pexpect # see -- http://www.bdnyc.org/2013/10/using-idl-within-python/
import pidly
idl = pidly.IDL('/Applications/exelis/idl/bin/idl')


# 
# Prepare simulated and recovered dir
# The simulated_dir should contain those simulation files from Philipp
# And the recovered_dir should contain those recovered files with PyBDSM
# 
simulated_dir = 'input_fits_files/2015.1.01495.S_SB1_GB1_MB1_COSMOS-16199'
recovered_dir = 'caap_blind_extraction_photometry_pybdsf'
recovered_list_of_catalog = recovered_dir + os.sep + 'output_list_of_catalog.txt'
if not os.path.isdir(simulated_dir):
    print('Error! The simulated directory "%s" was not found!'%(simulated_dir))
    sys.exit()
if not os.path.isdir(recovered_dir):
    print('Error! The recovered directory "%s" was not found!'%(recovered_dir))
    sys.exit()
if not os.path.isfile(recovered_list_of_catalog):
    print('Error! The recovered list of catalog "%s" was not found!'%(recovered_list_of_catalog))
    sys.exit()

input_fits_file = []
has_print_header = False
has_print_lines = 0
output_data_table = 'output_sim_data_table.txt'
ofs = open(output_data_table, 'w')
with open(recovered_list_of_catalog) as fp:
    input_list_files = fp.readlines()
    #<DEBUG># input_list_files = input_list_files[214:216]
    for lp in input_list_files:
        input_fits_file = lp.strip()
        input_fits_name = os.path.basename(os.path.dirname(input_fits_file))
        input_fits_base = input_fits_name.replace('.fits.gz','').replace('.fits','')
        sim_param_file = simulated_dir + os.sep + input_fits_base.replace('_model','_info.save')
        rec_catalog_file = recovered_dir + os.sep + input_fits_base + os.sep + 'pybdsm_cat.fits'
        # 
        # read simulated parameter file
        if not os.path.isfile(sim_param_file):
            print('Error! The simulation parameter file "%s" was not found!'%(sim_param_file))
            sys.exit()
        idl('restore, "%s", verbose = false'%(sim_param_file))
        sim_x = idl.CENX
        sim_y = idl.CENY
        sim_pixsc = idl.PIXSCL * 3600.0 # arcsec
        sim_Maj = idl.SOURCE_SIZE * idl.BEAMSIZE_PIX * sim_pixsc # arcsec
        sim_Min = sim_Maj * idl.AR # arcsec
        sim_PA = idl.PA # degree
        sim_fpeak = idl.PEAK_FLUX # Jy/beam
        sim_f = idl.TOTAL_FLUX # Jy
        sim_beam_maj = idl.BEAMSIZE_PIX * sim_pixsc # arcsec
        sim_beam_min = idl.BEAMSIZE_MINOR_PIX * sim_pixsc # arcsec
        sim_beam_pa = idl.BEAMPA # degree
        sim_str_split = re.findall('Size([0-9.]+)_SN([0-9.]+)_number([0-9]+)_.*', input_fits_base)
        sim_image_name = input_fits_base
        sim_image_dir = os.path.basename(simulated_dir)
        if sim_str_split:
            if len(sim_str_split[0]) >= 3:
                sim_Size = float(sim_str_split[0][0])
                sim_SNR_peak = float(sim_str_split[0][1])
                sim_id = long(sim_str_split[0][2])
                sim_rms = sim_fpeak / sim_SNR_peak
            else:
                print('Error! Failed to run \"re.findall(\'Size([0-9.]+)_SN([0-9.]+)_number([0-9]+)_.*\', input_fits_base)\"!')
                sys.exit()
        else:
            print('Error! Failed to run \"re.findall(\'Size([0-9.]+)_SN([0-9.]+)_number([0-9]+)_.*\', input_fits_base)\"!')
            sys.exit()
        # 
        # read recovered catalog file
        if not os.path.isfile(rec_catalog_file):
            #print('Warning! The recovered catalog file "%s" was not found! Meaning that this simulated source is not recovered!'%(input_fits_file))
            rec_x = -99
            rec_y = -99
            rec_f = -99
            rec_df = -99
            rec_fpeak = -99
            rec_dfpeak = -99
            rec_Maj = -99
            rec_Min = -99
            rec_PA = -99
            rec_S_Code = -99
        else:
            #print(rec_catalog_file)
            recovered_catalog_fits = fits.open(rec_catalog_file)
            #print(recovered_catalog_fits[0].header)
            recovered_catalog_header = recovered_catalog_fits[1].columns
            recovered_catalog_table = recovered_catalog_fits[1].data
            #print(recovered_catalog_header)
            #print(recovered_catalog_table)
            rec_x = recovered_catalog_table['Xposn']
            rec_y = recovered_catalog_table['Yposn']
            rec_dx = recovered_catalog_table['E_Xposn']
            rec_dy = recovered_catalog_table['E_Yposn']
            rec_f = recovered_catalog_table['Total_flux'] # Jy
            rec_df = recovered_catalog_table['E_Total_flux'] # Jy
            rec_fpeak = recovered_catalog_table['Peak_flux'] # Jy/beam
            rec_dfpeak = recovered_catalog_table['E_Peak_flux'] # Jy/beam
            rec_Maj = recovered_catalog_table['Maj'] * 3600.0 # arcsec
            rec_dMaj = recovered_catalog_table['E_Maj'] * 3600.0 # arcsec
            rec_Min = recovered_catalog_table['Min'] * 3600.0 # arcsec
            rec_dMin = recovered_catalog_table['E_Min'] * 3600.0 # arcsec
            rec_PA = recovered_catalog_table['PA']
            rec_dPA = recovered_catalog_table['E_PA']
            rec_S_Code = recovered_catalog_table['S_Code']
            rec_xydis = numpy.sqrt((rec_x - sim_x)**2 + (rec_y - sim_y)**2)
            lim_arcsec = 2.0 # arcsec #<TODO># 
            lim_xydis = numpy.sqrt(rec_dx**2+rec_dy**2+(lim_arcsec/sim_pixsc)**2)
            #<DEBUG># for iii in range(len(lim_xydis)):
            #<DEBUG>#     print('rec_xy = %g %g, sim_x = %g %g'%(rec_x[iii], rec_y[iii], sim_x, sim_y))
            #<DEBUG>#     print('rec_xydis = %g, lim_xydis = %g'%(rec_xydis[iii], lim_xydis[iii]))
            rec_index = numpy.argwhere(rec_xydis<lim_xydis) # select the brightest recovered source that are within 2.0 arcsec radius of the simulated source as the right counterparat!
            #
            recovered_catalog_fits.close()
            #print(sim_pixsc)
            #print(rec_index)
            if len(rec_index) <= 0:
                # no reasonably recovered source
                #print('Warning! No recovered source was found within %.2f arcsec or %.3f pixel of the simulated source!'%(lim_arcsec, lim_xydis))
                rec_x = -99
                rec_y = -99
                rec_f = -99
                rec_df = -99
                rec_fpeak = -99
                rec_dfpeak = -99
                rec_Maj = -99
                rec_Min = -99
                rec_PA = -99
                rec_S_Code = -99
            else:
                rec_x = rec_x[rec_index[0]]
                rec_y = rec_y[rec_index[0]]
                rec_f = rec_f[rec_index[0]]
                rec_df = rec_df[rec_index[0]]
                rec_fpeak = rec_fpeak[rec_index[0]]
                rec_dfpeak = rec_dfpeak[rec_index[0]]
                rec_Maj = rec_Maj[rec_index[0]]
                rec_Min = rec_Min[rec_index[0]]
                rec_PA = rec_PA[rec_index[0]]
                rec_S_Code = rec_S_Code[rec_index[0]]
            #break
        # 
        # print
        if not has_print_header:
            #print('%15s %15s %15s %15s %15s %15s %15s %15s %15s %15s %15s %15s'%('sim_id', 'sim_Size', 'sim_SNR_peak', 'sim_rms', 'sim_pixsc', 'sim_f', 'sim_fpeak', 'sim_Maj', 'sim_Min', 'sim_beam_maj', 'sim_beam_min', 'sim_beam_pa'))
            print('# %10s %13s %13s %13s %13s %13s %13s %13s %13s %13s %13s %13s %13s'%('sim_id', 'sim_Size', 'sim_SNR_peak', 'sim_rms', 'sim_pixsc', 'sim_f', 'sim_fpeak', 'sim_Maj', 'sim_Min', 'rec_f', 'rec_df', 'rec_fpeak', 'rec_dfpeak'))
            ofs.write('# %10s %13s %13s %13s %13s %13s %13s %13s %13s %13s %13s %13s %13s %13s %13s %33s %50s %13s %13s %13s %13s %13s %13s %13s %13s %13s %13s\n'%('sim_id', 'sim_Size', 'sim_SNR_peak', 'sim_rms', 'sim_pixsc', 'sim_beam_maj', 'sim_beam_min', 'sim_beam_pa', 'sim_x', 'sim_y', 'sim_f', 'sim_fpeak', 'sim_Maj', 'sim_Min', 'sim_PA', 'sim_image_name', 'sim_image_dir', 'rec_x', 'rec_y', 'rec_f', 'rec_df', 'rec_fpeak', 'rec_dfpeak', 'rec_Maj', 'rec_Min', 'rec_PA', 'rec_S_Code'))
            has_print_header = True
        if has_print_header:
            #print('%15d %15g %15g %15g %15g %15g %15g %15g %15g %15g %15g %15g'%(sim_id, sim_Size, sim_SNR_peak, sim_rms, sim_pixsc, sim_f, sim_fpeak, sim_Maj, sim_Min, sim_beam_maj, sim_beam_min, sim_beam_pa))
            print('%12d %13g %13g %13g %13g %13g %13g %13g %13g %13g %13g %13g %13g'%(sim_id, sim_Size, sim_SNR_peak, sim_rms, sim_pixsc, sim_f, sim_fpeak, sim_Maj, sim_Min, rec_f, rec_df, rec_fpeak, rec_dfpeak))
            ofs.write('%12d %13g %13g %13g %13g %13g %13g %13g %13g %13g %13g %13g %13g %13g %13g %33s %50s %13g %13g %13g %13g %13g %13g %13g %13g %13g %13s\n'%(sim_id, sim_Size, sim_SNR_peak, sim_rms, sim_pixsc, sim_beam_maj, sim_beam_min, sim_beam_pa, sim_x, sim_y, sim_f, sim_fpeak, sim_Maj, sim_Min, sim_PA, sim_image_name, sim_image_dir, rec_x, rec_y, rec_f, rec_df, rec_fpeak, rec_dfpeak, rec_Maj, rec_Min, rec_PA, rec_S_Code))
            has_print_lines = has_print_lines + 1
        # 
        # 
        #if has_print_lines > 100:
        #    break




