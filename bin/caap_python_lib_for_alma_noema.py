#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# 
# 


import numpy

from datetime import datetime


def calc_BeamSize(Frequency_GHz, Diameter_m):
    # ALMA_Cycle4_Technical_Handbook_08Sep2016.pdf -- Equation(3.4)
    return 1.02 * (2.99792458e-1/Frequency_GHz) / Diameter_m / numpy.pi * 180.0 * 3600.0 # arcsec


def calc_SolidAngle(BeamSize_arcsec):
    # 
    return (numpy.pi * (BeamSize_arcsec/3600.0/180.0*numpy.pi)**2) / (4.0 * numpy.log(2.0))


def calc_JanskyPerKelvin(Aeff_m2, Frequency_GHz, Diameter_m):
    # 
    # 1 / Aeff * Omega / lambda**2 [Jy/K]
    # [W s K^-1 m^-2] -> [W m^-2 Hz-1 K^-1] -> 1e26 [Jy K^-1]
    #return (1.0 / Aeff_m2) / (2.99792458e8/(Frequency_GHz*1e9))**2 * calc_SolidAngle(calc_BeamSize(Frequency_GHz, Diameter_m))
    # 
    # 2 * k_B * Omega / lambda**2 [Jy/K]
    # [W s K^-1 m^-2] -> [W m^-2 Hz-1 K^-1] -> 1e26 [Jy K^-1]
    #return (2.0 * 1.38e-23 * calc_SolidAngle(calc_BeamSize(Frequency_GHz, Diameter_m))) / ((2.99792458e8/(Frequency_GHz*1e9))**2) / 1e-26
    # 
    # 2 * k_B / Aeff
    # [W s K^-1 m^-2] -> [W m^-2 Hz-1 K^-1] -> 1e26 [Jy K^-1]
    return (2.0 * 1.38e-23 / Aeff_m2 * 1e26) # this is better because "Aeff_m2" considers "eta_ap".


def calc_Sensitivity(Tint=[], Tsys=[], Nant=0, Npol=2, Bandwidth=0.0, bw=0.0, Velowidth=0.0, dv=0.0, 
                     Frequency=0.0, freq=0.0, Telescope='NOEMA', Weather='summer', eta_ap=numpy.nan, 
                     Verbose=True):
    # 
    # NOEMACapabilities.pdf 
    # 
    # The rms noise can be computed from
    #     {\sigma} = \frac{ JpK * Tsys }{ \eta * \sqrt{Nant*(Nant-1)*Tint*Bandwidth*Npol} }
    # where
    #     JpK is the conversion factor from Kelvin to Jansky, 
    #         JpK = (1.0/Aeff) * lambda^2 / Omega, 
    #               Aeff = eta_ap * Area, 
    #                      eta_ap = 0.72 * exp(-16*pi^2*sigma^2/lambda^2), 
    #                               sigma is the rms surface accuracy of the antenna.
    #               Omega = (pi * theta^2) / (4.0*ln(2))
    #         e.g. ALMA 12m, band 3, eta_ap = 0.71, Area = 113.1 m^2, so JpK = 0.71 * 1.38e-16 erg/K / 113.1 m^2 = 0.71 * 1.38e-16 * 1e23 / 113.1e4 [Jy/K * s cm^2 Hz cm^2] = 8.663129973 [Jy/K]
    #         e.g. ALMA 7m, band 3, eta_ap = 0.71, Area = 38.5 m^2, so JpK = 0.71 * 1380 / 38.5 = 25.44935065 [Jy/K]
    #     \eta is an additional efficiency factor due to atmospheric phase noise
    #     Bandwidth in GHz (or Velowidth in km/s)
    #     Frequency in GHz
    # 
    # If input Frequency by argument freq
    if Frequency <= 0.0 and freq > 0.0:
        Frequency = freq
    if type(Frequency) is str:
        Frequency = float(Frequency)
    # 
    # If input velocity width by argument dv
    if Velowidth <= 0.0 and dv > 0.0:
        Velowidth = dv
    # 
    # If input band width by argument bw
    if Bandwidth <= 0.0 and bw > 0.0:
        Bandwidth = bw
    # 
    # If input velocity width instead of bandwidth, then convert to bandwidth
    if Velowidth > 0.0 and Bandwidth <= 0.0 and Frequency > 0.0:
        Bandwidth = (Velowidth/2.99792458e5) * Frequency # GHz
    # 
    # calculate velocity width from bandwidth
    if Bandwidth > 0.0 and Frequency > 0.0:
        Velowidth = (Bandwidth/Frequency) * 2.99792458e5 # km/s
    # 
    # If input Tint is not a list, make it a list
    if type(Tint) is not list:
        Tint = [Tint]
    #print(Tint, len(Tint))
    # 
    # If input Tsys is not a list, make it a list
    if type(Tsys) is not list:
        Tsys = [Tsys]
    #print(Tsys, len(Tsys))
    # 
    # If input Bandwidth is not given, print error
    if not Frequency > 0.0:
        print("Error! Frequency is not given (in GHz)!")
        return []
    # 
    # If input Bandwidth is not given, print error
    if not Bandwidth > 0.0:
        print("Error! Bandwidth is not given (in GHz)!")
        return []
    # 
    # If input Nantenna, Bandwidth, Frequency are valid, then do sensitivity calculation
    Output_2d = []
    if Bandwidth > 0.0 and Frequency > 0.0:
        Frequency = float(Frequency)
        Bandwidth = float(Bandwidth)
        # 
        Output_1d = []
        # 
        # Loop each Tint
        for i_Tint in range(len(Tint)):
            # 
            # prepare an array for each Tsys
            Output_1d = []
            # 
            # determine Tsys
            if len(Tsys) == 0:
                Tsys = [numpy.nan]
            # 
            # If input Tsys is a list, then loop each Tsys
            for i_Tsys in range(len(Tsys)):
                # 
                # determine \eta and JpK
                eta = numpy.nan
                JpK = numpy.nan
                bandnumb = numpy.nan
                telescop = ''
                beamsize = 0.0
                t_Nant = 0         # temporary variable, will be overriden if it has been given by the user. 
                t_Tsys = numpy.nan # temporary variable, will be overriden if it has been given by the user. 
                t_Tint = numpy.nan # temporary variable, will be overriden if it has been given by the user. 
                rms = numpy.nan
                # 
                if Telescope.upper().find('NOEMA')>=0:
                    telescop = 'NOEMA'
                    beamsize = calc_BeamSize(Frequency, 15.0)
                    # 
                    # determine Nant
                    t_Nant = 7 # ealier than 2017-09-14
                    t_Nant = 9 # later than 2017-09-14
                    # 
                    # determine Band
                    # Band 1 before 201703 was 80-116GHz
                    # Band 1 after 201703 was 70.9-121.6GHz
                    # Band 2 before 201703 was 130-177GHz
                    # Band 2 after 201703 was 124.4-183.6GHz
                    # Band 3 before 201703 was 202-267GHz
                    # Band 3 after 201703 was 196.4-279.6GHz
                    if Frequency >= 70.9 and Frequency <= 121.6:
                        bandnumb = 1    # NOEMA Band 1
                        eta = 0.9       # NOEMA Band 1, February 22, 2016
                        JpK = 22.0      # NOEMA Band 1, February 22, 2016
                        # JpK = calc_JanskyPerKelvin(numpy.pi*(15.0/2.0)**2 * 0.95, Frequency, 15.0) / eta      #<before><20170312><pms.iram.fr># 
                        # t_Tsys = 100.0 if(Frequency<110) else (Frequency-110)/(116-110)*(185.0-100.0)+100.0     #<before><20170312><pms.iram.fr># 
                        # t_Tsys = 85.0 if(Frequency<110) else (Frequency-110)/(121.6-110)*(185.0-100.0)+100.0
                        if(Weather.lower().find('winter')>=0):
                            database_Tsys = {'freq':[70., 80, 110, 122.],
                                             'Tsys':[140, 75, 85., 313.]} #<20170312># /Users/dzliu/Softwares/GILDAS/gildas-exe-10feb17/pro/noema-sensitivity-estimator.astro
                        else:
                            database_Tsys = {'freq':[70., 80, 110, 122.],
                                             'Tsys':[150, 85, 95., 323.]} #<20170312># /Users/dzliu/Softwares/GILDAS/gildas-exe-10feb17/pro/noema-sensitivity-estimator.astro
                        # 
                        t_Tsys = numpy.interp(Frequency, database_Tsys['freq'], database_Tsys['Tsys'])
                    elif Frequency >= 124.4 and Frequency <= 183.6:
                        bandnumb = 2    # NOEMA Band 2
                        eta = 0.8       # NOEMA Band 2, February 22, 2016
                        JpK = 29.0      # NOEMA Band 2, February 22, 2016
                        # JpK = calc_JanskyPerKelvin(numpy.pi*(15.0/2.0)**2 * 0.85, Frequency, 15.0) / eta #<TODO># dzliu
                        # t_Tsys = 150.0 if(Frequency<150) else (Frequency-150)/(177-150)*(200.0-150.0)+150.0
                        if(Weather.lower().find('winter')>=0):
                            database_Tsys = {'freq':[124, 126, 150, 184.],
                                             'Tsys':[110, 110, 110, 195.]} #<20170312># /Users/dzliu/Softwares/GILDAS/gildas-exe-10feb17/pro/noema-sensitivity-estimator.astro
                        else:
                            database_Tsys = {'freq':[124, 126, 150, 184.],
                                             'Tsys':[140, 140, 140, 242.]} #<20170312># /Users/dzliu/Softwares/GILDAS/gildas-exe-10feb17/pro/noema-sensitivity-estimator.astro
                        # 
                        t_Tsys = numpy.interp(Frequency, database_Tsys['freq'], database_Tsys['Tsys'])
                    elif Frequency >= 196.4 and Frequency <= 279.6:
                        bandnumb = 3    # NOEMA Band 3
                        eta = 0.6       # NOEMA Band 3, February 22, 2016
                        JpK = 35.0      # NOEMA Band 3, February 22, 2016
                        # JpK = calc_JanskyPerKelvin(numpy.pi*(15.0/2.0)**2 * 0.75, Frequency, 15.0) / eta #<TODO># dzliu
                        # t_Tsys = 250.0
                        if(Weather.lower().find('winter')>=0):
                            database_Tsys = {'freq':[195, 196, 230, 280.],
                                             'Tsys':[190, 190, 190, 190.]} #<20170312># /Users/dzliu/Softwares/GILDAS/gildas-exe-10feb17/pro/noema-sensitivity-estimator.astro
                        else:
                            database_Tsys = {'freq':[195, 196, 230, 280.],
                                             'Tsys':[250, 250, 250, 250.]} #<20170312># /Users/dzliu/Softwares/GILDAS/gildas-exe-10feb17/pro/noema-sensitivity-estimator.astro
                        # 
                        t_Tsys = numpy.interp(Frequency, database_Tsys['freq'], database_Tsys['Tsys'])
                # 
                elif Telescope.upper().find('ALMA')>=0:
                    # 
                    telescop = 'ALMA'
                    if Telescope.find('12m')>=0:
                        beamsize = calc_BeamSize(Frequency, 12.0)
                        telescop = telescop + ' 12m'
                        t_Nant = 40
                    elif Telescope.find('7m')>=0:
                        beamsize = calc_BeamSize(Frequency, 7.0)
                        telescop = telescop + ' 7m'
                        t_Nant = 10
                    # 
                    eta = 0.96 * 0.88 / 1.1 * (1.0 - 0.0) # ALMA_Cycle4_Technical_Handbook_08Sep2016.pdf -- the last 0.0 is shadowing
                    eta_ap_12m = {'3':0.71, '4':0.70, '5':0.00, '6':0.68, '7':0.63, '8':0.60, '9':0.43, '10':0.31} # ALMA_Cycle4_Technical_Handbook_08Sep2016.pdf -- PDF Page 130, Table 9.3
                    eta_ap_7m = {'3':0.71, '4':0.71, '5':0.00, '6':0.69, '7':0.66, '8':0.64, '9':0.52, '10':0.42} # ALMA_Cycle4_Technical_Handbook_08Sep2016.pdf -- PDF Page 130, Table 9.3
                    # 
                    if Frequency >= 84 and Frequency <= 119:
                        bandnumb = 3                                                # ALMA Band 3 (EU)
                        # 
                        if Telescope.find('12m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_12m[str(bandnumb)] * 113.1, Frequency, 12.0)
                        elif Telescope.find('7m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_7m[str(bandnumb)] * 38.5, Frequency, 7.0)
                        # 
                        t_Tsys = 70.0 if(Frequency<110) else (Frequency-110)/(116-110)*(170.0-70.0)+70.0
                    # 
                    elif Frequency >= 125 and Frequency <= 163:
                        bandnumb = 4                                                # ALMA Band 4 (JP)
                        # 
                        if Telescope.find('12m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_12m[str(bandnumb)] * 113.1, Frequency, 12.0)
                        elif Telescope.find('7m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_7m[str(bandnumb)] * 38.5, Frequency, 7.0)
                        # 
                        t_Tsys = 80.0 if(Frequency>130) else (Frequency-130)/(125-130)*(100.0-80.0)+80.0
                        if (Frequency>142 and Frequency<145): t_Tsys = 90.0
                    # 
                    elif Frequency >= 163 and Frequency <= 211:
                        bandnumb = 5                                                # ALMA Band 5 (EU)
                        # 
                        if Telescope.find('12m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_12m[str(bandnumb)] * 113.1, Frequency, 12.0)
                        elif Telescope.find('7m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_7m[str(bandnumb)] * 38.5, Frequency, 7.0)
                        # 
                        #t_Tsys = 
                    # 
                    elif Frequency >= 211 and Frequency <= 275:
                        bandnumb = 6                                                # ALMA Band 6 (US-EU)
                        # 
                        if Telescope.find('12m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_12m[str(bandnumb)] * 113.1, Frequency, 12.0)
                        elif Telescope.find('7m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_7m[str(bandnumb)] * 38.5, Frequency, 7.0)
                        # 
                        t_Tsys = 95.0 if(Frequency<220) else 120.0 #<TODO># 
                    # 
                    elif Frequency >= 275 and Frequency <= 370:
                        bandnumb = 7                                                # ALMA Band 7 (US-EU)
                        # 
                        if Telescope.find('12m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_12m[str(bandnumb)] * 113.1, Frequency, 12.0)
                        elif Telescope.find('7m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_7m[str(bandnumb)] * 38.5, Frequency, 7.0)
                        # 
                        t_Tsys = (Frequency-275)/(350-275)*(150.0-120.0)+120.0
                        if (Frequency>316 and Frequency<334): t_Tsys = 200.0
                        if (Frequency>320 and Frequency<330): t_Tsys = 999.0
                    # 
                    elif Frequency >= 385 and Frequency <= 500:
                        bandnumb = 8                                                # ALMA Band 8 (JP)
                        # 
                        if Telescope.find('12m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_12m[str(bandnumb)] * 113.1, Frequency, 12.0)
                        elif Telescope.find('7m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_7m[str(bandnumb)] * 38.5, Frequency, 7.0)
                        # 
                        t_Tsys = 500.0
                        if (Frequency>390 and Frequency<420): t_Tsys = 350.0
                        if (Frequency>425-5 and Frequency<425+5): t_Tsys = 999.0
                        if (Frequency>447-5 and Frequency<447+5): t_Tsys = 999.0
                        if (Frequency>475-5 and Frequency<475+5): t_Tsys = 999.0
                        if (Frequency>487-5 and Frequency<487+5): t_Tsys = 999.0
                    # 
                    elif Frequency >= 602 and Frequency <= 720:
                        bandnumb = 9                                                # ALMA Band 9 (US-EU)
                        # 
                        if Telescope.find('12m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_12m[str(bandnumb)] * 113.1, Frequency, 12.0)
                        elif Telescope.find('7m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_7m[str(bandnumb)] * 38.5, Frequency, 7.0)
                        # 
                        #t_Tsys = 
                    # 
                    elif Frequency >= 787 and Frequency <= 950:
                        bandnumb = 10                                               # ALMA Band 10 (JP)
                        # 
                        if Telescope.find('12m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_12m[str(bandnumb)] * 113.1, Frequency, 12.0)
                        elif Telescope.find('7m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap_7m[str(bandnumb)] * 38.5, Frequency, 7.0)
                        # 
                        #t_Tsys = 
                    # 
                # 
                if Nant > 0:
                    t_Nant = Nant
                if Tsys[i_Tsys] is not numpy.nan:
                    t_Tsys = float(Tsys[i_Tsys])
                if Tint[i_Tint] is not numpy.nan:
                    t_Tint = float(Tint[i_Tint])
                # 
                # If JpK could not be determined but the user input eta_ap
                if numpy.isnan(JpK):
                    if not numpy.isnan(eta_ap):
                        if Telescope.find('12m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap * 113.1, Frequency, 12.0)
                        elif Telescope.find('7m')>=0:
                            JpK = calc_JanskyPerKelvin(eta_ap * 38.5, Frequency, 7.0)
                # 
                if eta is not numpy.nan and JpK is not numpy.nan and t_Tsys is not numpy.nan and t_Tint is not numpy.nan:
                    # rms = ( 2 * k_B * Tsys ) / ( Aeff * sqrt( N * (N-1) * BW * Tint * Npol) )
                    rms = ( float(JpK) * float(t_Tsys) ) / ( float(eta) * numpy.sqrt(float(t_Nant)*float(t_Nant-1)*float(t_Tint)*float(Bandwidth)*1e9*float(Npol)) ) * 1e3 # mJy
                    if Verbose:
                        print("")
                        print("Telescope = %s"%(telescop))
                        print("Weather = %s"%(Weather))
                        print("Bandnumber = %s"%(bandnumb))
                        print("Frequency = %s GHz"%(Frequency))
                        print("Bandwidth = %s GHz"%(Bandwidth))
                        print("Velowidth = %s km/s"%(Velowidth))
                        print("Beamsize = %s arcsec"%(beamsize))
                        print("Jy/K = %s"%(JpK))
                        print("Nant = %s"%(t_Nant))
                        print("Tsys = %s K"%(t_Tsys))
                        print("Tint = %s s"%(t_Tint))
                        print("rms = %s mJy"%(rms))
                else:
                    print("")
                    print("Sorry! Could not determine eta and Tsys for Telescope %s Frequency %0.6f GHz!"%(Telescope, Frequency))
                # 
                # output item --> output 1d array --> output 2d array
                Output_item = {'Telescope':telescop, 'Bandnumber':bandnumb, 'Bandwidth':Bandwidth, 'Frequency':Frequency, 
                                'BeamSize':beamsize, 
                                'JpK':JpK, 'Tsys':t_Tsys, 
                                'eta':eta, 'Nant':t_Nant, 'Npol':Npol, 'Tint':t_Tint, 
                                'rms':rms,
                              }
                #print(Output_item)
                # 
                # next
            Output_1d.append(Output_item)
        Output_2d.append(Output_1d)
    # 
    Output_data = Output_2d
    # 
    if len(Tsys) == 1:
        Output_data = [x[0] for x in Output_data]
    # 
    if len(Tint) == 1:
        Output_data = Output_data[0]
    # 
    return Output_data
            



















import sys

try:
    import numpy
except ImportError:
    print("Error! Could not import numpy!")
    sys.exit()









