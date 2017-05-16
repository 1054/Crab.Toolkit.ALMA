#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# 

################################
# 
# class calc_SMF()
# 
#   Example: 
#            TODO
# 
################################

try:
    import pkg_resources
except ImportError:
    raise SystemExit("Error! Failed to import pkg_resources!")

pkg_resources.require("numpy")
pkg_resources.require("astropy>=1.3")
pkg_resources.require("matplotlib")
pkg_resources.require("wcsaxes") # http://wcsaxes.readthedocs.io/en/latest/getting_started.html

import os
import sys
import re
import glob
import inspect
import math
import numpy
import astropy
import astropy.io.ascii as asciitable
#from astropy import units
#from astropy.io import fits
#from astropy.wcs import WCS
#import wcsaxes
#from scipy import spatial
#from scipy.spatial import KDTree
from pprint import pprint


try: 
    import matplotlib
except ImportError:
    raise SystemExit("Error! Failed to import matplotlib!")

import platform
if platform.system() == 'Darwin':
    matplotlib.use('Qt5Agg')
else:
    matplotlib.use('TkAgg')

try: 
    from matplotlib import pyplot
except ImportError:
    raise SystemExit("Error! Failed to import pyplot from matplotlib!")

try: 
    from matplotlib.colors import hex2color, rgb2hex
except ImportError:
    raise SystemExit("Error! Failed to import hex2color, rgb2hex from matplotlib.colors!")

try:
    from matplotlib.patches import Ellipse, Circle, Rectangle
except ImportError:
    raise SystemExit("Error! Failed to import Ellipse, Circle, Rectangle from matplotlib.patches!")

try:
    from astropy.visualization import MinMaxInterval, PercentileInterval, AsymmetricPercentileInterval, SqrtStretch, PowerStretch, ImageNormalize
except ImportError:
    raise SystemExit("Error! Failed to import MinMaxInterval, PercentileInterval, AsymmetricPercentileInterval, SqrtStretch, PowerStretch, ImageNormalize from astropy.visualization!")
# ImageNormalize requires astropy>=1.3



import warnings

warnings.filterwarnings("ignore",".*GUI is implemented.*")



from caap_python_lib_plot import *










# 
def calc_Schecheter(lgMchar, Phi, alpha, lgMchar_2=None, Phi_2=None, alpha_2=None, min_lgMstar=6.0, max_lgMstar=14.0):
    # 
    # Prepare Schechter function stellar masses
    SchechterM = numpy.linspace(min_lgMstar,max_lgMstar,num=1000)
    # 
    # Check input variable type
    if type(lgMchar) is numpy.string_:
        lgMchar = float(lgMchar)
    if type(Phi) is numpy.string_:
        Phi = float(Phi)
    if type(alpha) is numpy.string_:
        alpha = float(alpha)
    if type(lgMchar_2) is numpy.string_:
        lgMchar_2 = float(lgMchar_2)
    if type(Phi_2) is numpy.string_:
        Phi_2 = float(Phi_2)
    if type(alpha_2) is numpy.string_:
        alpha_2 = float(alpha_2)
    # 
    if type(lgMchar) is str:
        lgMchar = float(lgMchar)
    if type(Phi) is str:
        Phi = float(Phi)
    if type(alpha) is str:
        alpha = float(alpha)
    if type(lgMchar_2) is str:
        lgMchar_2 = float(lgMchar_2)
    if type(Phi_2) is str:
        Phi_2 = float(Phi_2)
    if type(alpha_2) is str:
        alpha_2 = float(alpha_2)
    # 
    # Construct Schechter function
    SchechterM_pow10 = 10**(SchechterM-lgMchar)
    SchechterS = (Phi*10**((SchechterM-lgMchar)*(1.0+alpha)))
    SchechterP = numpy.exp(-SchechterM_pow10)*SchechterS*numpy.log(10) # Muzzin2013 needs to multiply ln(10) 
    # 
    if lgMchar_2:
        if Phi_2:
            if Phi_2>0:
                if alpha_2:
                    SchechterM_1 = SchechterM_pow10
                    SchechterS_1 = SchechterS
                    SchechterP_1 = SchechterP
                    # 
                    SchechterM_2 = 10**(SchechterM-lgMchar_2)
                    SchechterS_2 = (Phi_2*10**((SchechterM-lgMchar_2)*(1.0+alpha_2)))
                    SchechterP_2 = numpy.exp(-SchechterM_2)*SchechterS_2*numpy.log(10) # Muzzin2013 needs to multiply ln(10) 
                    SchechterP = SchechterP_1 + SchechterP_2
    # 
    SchechterP_log10 = SchechterP*0.0-99
    SchechterP_log10[SchechterP>0] = numpy.log10(SchechterP[SchechterP>0])
    # 
    return SchechterP, 10**SchechterM





# 
def calc_SMF(SMF_name = 'Davidzon', SMF_type = '', do_Plot = False):
    SMF_dir = '%s/data/Galaxy_SMF'%(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    SMF_file_ALL = ''
    SMF_file_SFG = ''
    SMF_file_QG = ''
    SMF_func_refer = ''
    SMF_func_format = ''
    # 
    # Choose SMF
    if SMF_name.lower().find('davidzon')>=0:
        # Davidzon et al. 2017 (2017arXiv170102734D) is using Chabrier IMF, Same as ours.
        SMF_file_ALL = 'datatable_Davidzon2017_SMF_ALL.txt'
        SMF_file_SFG = 'datatable_Davidzon2017_SMF_SFG.txt'
        SMF_file_QG = 'datatable_Davidzon2017_SMF_QG'
        SMF_func_refer = 'Davidzon2017'
        SMF_func_format = 'Chabrier IMF, double Schecheter, '
    elif SMF_name.lower().find('muzzin')>=0:
        # Muzzin et al. 2013 is using Kroupa IMF, 
        # lg-KroupaIMF-SFR = lg-ChabrierIMF-SFR + 0.04 dex
        SMF_file_ALL = 'datatable_Muzzin2013_SMF_ALL.txt'
        SMF_file_SFG = 'datatable_Muzzin2013_SMF_SFG_FixedSlope.txt'
        SMF_file_QG = ''
        SMF_func_refer = 'Muzzin2013'
        SMF_func_format = 'Kroupa IMF, '
    elif SMF_name.lower().find('ilbert')>=0:
        # Ilbert et al. 2013 is using Chabrier IMF, Same as ours.
        # <Done> need to compare with Ilbert2013 Figure A.2, yes, matched!
        SMF_file_ALL = 'datatable_Ilbert2013_SMF_ALL.txt'
        SMF_file_SFG = 'datatable_Ilbert2013_SMF_SFG.txt'
        SMF_file_QG = ''
        SMF_func_refer = 'Ilbert2013'
        SMF_func_format = 'Chabrier IMF, '
    # 
    # Print info
    print("Loading galaxy stellar mass function: %s"%(SMF_func_refer))
    # 
    # Read SMF data file
    if os.path.isfile('%s/%s'%(SMF_dir,SMF_file_ALL)):
        SMF_data_ALL = asciitable.read('%s/%s'%(SMF_dir,SMF_file_ALL))
        # 
        # Correct IMF
        if SMF_func_format.find('Kroupa IMF') >= 0:
            SMF_data_ALL['lgMchar'] = SMF_data_ALL['lgMchar'] - 0.04
        elif SMF_func_format.find('Salpeter IMF') >= 0:
            SMF_data_ALL['lgMchar'] = SMF_data_ALL['lgMchar'] - numpy.log10(1.73)
        # 
        # prepare plotting SMF
        if do_Plot:
            SMF_plot = CrabPlot()
        # 
        # calc_Schecheter
        for i in range(len(SMF_data_ALL['zLo'])):
            TMP_rho, TMP_mass = calc_Schecheter(SMF_data_ALL[i]['lgMchar'], SMF_data_ALL[i]['Phi_1'], SMF_data_ALL[i]['alpha_1'], 
                                               SMF_data_ALL[i]['lgMchar'], SMF_data_ALL[i]['Phi_2'], SMF_data_ALL[i]['alpha_2'])
            if i == 0:
                SMF_rho_ALL = numpy.vstack((TMP_rho,))
                SMF_mass_ALL = numpy.vstack((TMP_mass,))
            else:
                #print(type(SMF_rho_ALL))
                #print(SMF_rho_ALL.shape)
                SMF_rho_ALL = numpy.vstack((SMF_rho_ALL,TMP_rho))
                SMF_mass_ALL = numpy.vstack((SMF_mass_ALL,TMP_mass))
                
            if do_Plot:
                print('Plotting SMF at redshift bin %.4f - %.4f'%(SMF_data_ALL['zLo'][i], SMF_data_ALL['zHi'][i]))
                SMF_plot.plot_xy(x = TMP_mass, y = TMP_rho, xlog = True, ylog = True, xrange = [1e6, 1e14], yrange = [1e-8, 1e4], 
                                 xtitle = 'M_{*}', ytitle = 'N', 
                                 linestyle = '-', linewidth = 2.0, drawstyle = 'steps-mid', symbol = None, fillstyle = 'full', color = 'red', facecolor = 'red', edgecolor = 'red', 
                                 current = True)
                #SMF_plot.plot_xy(x = TMP_mass, y = TMP_rho, xlog = True, ylog = True, xrange = [1e6, 1e14], yrange = [1e-8, 1e4], 
                #                 xtitle = 'M_{*}', ytitle = 'N', 
                #                 fmt = 'ro-', 
                #                 current = True)
                #SMF_plot.plot_xy(x = TMP_mass, y = TMP_rho, xlog = True, ylog = True, xrange = [1e6, 1e14], yrange = [1e-8, 1e4], 
                #                 xtitle = 'M_{*}', ytitle = 'N', 
                #                 symbol = 'o', color = 'blue', 
                #                 current = True)
                SMF_plot.show()
                break
        # 
        pyplot.show(block=True)
        # 
        # Print info
        #pprint(SMF_data_ALL)
        #pprint(SMF_mass_ALL)
        #pprint(SMF_rho_ALL)
        
        
    return




















