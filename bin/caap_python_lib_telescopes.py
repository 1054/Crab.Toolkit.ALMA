#!/usr/bin/env python2.7
# 

##################################################################################
# 
# class recognize_Instrument(str) -- return rec_Instrument, rec_Telescope
# 
##################################################################################

import os, sys





# 
def recognize_Instrument(FitsFileName):
    rec_Telescope = ""
    rec_Instrument = ""
    if type(FitsFileName) is str:
        if FitsFileName.lower().find('_acs_')>=0:
            rec_Telescope = "HST"
            rec_Instrument = "ACS"
        elif FitsFileName.lower().find('_irac_ch1')>=0:
            rec_Telescope = "Spitzer"
            rec_Instrument = "IRAC ch1"
        elif FitsFileName.lower().find('_irac_ch2')>=0:
            rec_Telescope = "Spitzer"
            rec_Instrument = "IRAC ch2"
        elif FitsFileName.lower().find('_irac_ch3')>=0:
            rec_Telescope = "Spitzer"
            rec_Instrument = "IRAC ch3"
        elif FitsFileName.lower().find('_irac_ch4')>=0:
            rec_Telescope = "Spitzer"
            rec_Instrument = "IRAC ch4"
        elif FitsFileName.lower().find('_mips_160_')>=0:
            rec_Telescope = "Spitzer"
            rec_Instrument = "MIPS 160um"
        elif FitsFileName.lower().find('_mips_70_')>=0:
            rec_Telescope = "Spitzer"
            rec_Instrument = "MIPS 70um"
        elif FitsFileName.lower().find('_mips_24_')>=0:
            rec_Telescope = "Spitzer"
            rec_Instrument = "MIPS 24um"
        elif FitsFileName.lower().find(('.J.original').lower())>=0:
            rec_Telescope = "UltraVISTA"
            rec_Instrument = "J"
        elif FitsFileName.lower().find(('.H.original').lower())>=0:
            rec_Telescope = "UltraVISTA"
            rec_Instrument = "H"
        elif FitsFileName.lower().find(('.Ks.original').lower())>=0:
            rec_Telescope = "UltraVISTA"
            rec_Instrument = "Ks"
        elif FitsFileName.lower().find(('.Ks.matched').lower())>=0:
            rec_Telescope = "UltraVISTA"
            rec_Instrument = "Ks"
        elif FitsFileName.lower().find(('_image_250_SMAP_').lower())>=0:
            rec_Telescope = "Herschel"
            rec_Instrument = "SPIRE 250um"
        elif FitsFileName.lower().find(('_image_350_SMAP_').lower())>=0:
            rec_Telescope = "Herschel"
            rec_Instrument = "SPIRE 350um"
        elif FitsFileName.lower().find(('_image_500_SMAP_').lower())>=0:
            rec_Telescope = "Herschel"
            rec_Instrument = "SPIRE 500um"
        elif FitsFileName.lower().find(('_pep_COSMOS_red_Map').lower())>=0:
            rec_Telescope = "Herschel"
            rec_Instrument = "PACS 160um"
        elif FitsFileName.lower().find(('_pep_COSMOS_green_Map').lower())>=0:
            rec_Telescope = "Herschel"
            rec_Instrument = "PACS 100um"
        elif FitsFileName.lower().find(('_pep_COSMOS_blue_Map').lower())>=0:
            rec_Telescope = "Herschel"
            rec_Instrument = "PACS 70um"
        elif FitsFileName.lower().find(('_cosmos08_gw_18Aug10_v6_').lower())>=0:
            rec_Telescope = ""
            rec_Instrument = ""
        elif FitsFileName.lower().find(('_MAMBO_image_').lower())>=0:
            rec_Telescope = "IRAM 30m"
            rec_Instrument = "MAMBO 1.2mm"
        elif FitsFileName.lower().find(('_vla_20cm').lower())>=0:
            rec_Telescope = "VLA"
            rec_Instrument = "20cm"
        elif FitsFileName.lower().find(('_vla_90cm').lower())>=0:
            rec_Telescope = "VLA"
            rec_Instrument = "90cm"
        elif FitsFileName.lower().find(('_vla_3ghz').lower())>=0:
            rec_Telescope = "VLA"
            rec_Instrument = "3GHz"
    # 
    return rec_Instrument, rec_Telescope




























