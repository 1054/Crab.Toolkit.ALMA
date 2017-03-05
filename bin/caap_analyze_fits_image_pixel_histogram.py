#!/usr/bin/env python2.7
# 
# 
# Last updates: 
#      20170224 01:52 CET
#      20170224 13:53 CET <20170224> added a check step to make sure we measure the FitGauss
#      20170228 if FitParam['mu'] < np.min(BinCents[FitRange]) or FitParam['mu'] > np.max(BinCents[FitRange])
# 


import os, sys
import numpy as np
import scipy
import astropy
from astropy.io import fits
import matplotlib
matplotlib.use('Qt5Agg') # must before import pyplot
import matplotlib.pyplot as pl
import matplotlib.mlab as mlab
from matplotlib.colors import LogNorm
from matplotlib.colors import hex2color, rgb2hex


from caap_analyze_fits_image_pixel_mode import mode
from caap_fit_Gaussian_1D import fit_Gaussian_1D


#print(pl.rcParams.keys())
#pl.rcParams['font.family'] = 'NGC'
pl.rcParams['font.size'] = 20
#pl.rcParams['axes.labelsize'] = 'large'
pl.rcParams['axes.labelpad'] = 12 # padding between axis and xy title (label)
#pl.rcParams['xtick.major.pad'] = 10 # padding between ticks and axis
#pl.rcParams['ytick.major.pad'] = 10 # padding between ticks and axis
pl.rcParams['xtick.labelsize'] = 18
pl.rcParams['ytick.labelsize'] = 18
pl.rcParams['xtick.minor.visible'] = True # 
pl.rcParams['ytick.minor.visible'] = True # 
pl.rcParams['figure.figsize'] = (21/2.0*0.95), (21/2.0*0.95)/16*9 # width = half A4 width , width/height=16/9. 


fig, axes = pl.subplots() # nrows=2, ncols=2 # ax0, ax1, ax2, ax3 = axes.flatten()




# 
# Check input arguments and pring usage
# 
if len(sys.argv) <= 1:
    print("Usage: ")
    print("  caap_analyze_fits_image_pixel_histogram.py \"aaa.fits\"")
    print("")
    sys.exit()


# 
# Get input fits file
# 
FitsFile = sys.argv[1]
print('Input fits file: %s\n'%(FitsFile))


# 
# Read input fits image
# 
FitsStruct = fits.open(FitsFile)
FitsImage = FitsStruct[0].data


# 
# Remove NaN and get the rest Bin pixel values
# 
BinVar = FitsImage.flatten()
BinVar = BinVar[~np.isnan(BinVar)]


# 
# Statistics of pixel values
# 
BinMin = np.min(BinVar)
BinMax = np.max(BinVar)
BinMean = np.mean(BinVar)
BinMedian = np.median(BinVar)
BinMode, BinModeCounts = mode(BinVar)
BinSigma = np.std(BinVar)
# output to txt file
with open('%s.pixel.statistics.txt'%(FitsFile), 'w') as fp:
    print(   "Min    = %.10g"  %(BinMin))
    fp.write("Min    = %.10g\n"%(BinMin))
    print(   "Max    = %.10g"  %(BinMax))
    fp.write("Max    = %.10g\n"%(BinMax))
    print(   "Mean   = %.10g"  %(BinMean))
    fp.write("Mean   = %.10g\n"%(BinMean))
    print(   "Median = %.10g"  %(BinMedian))
    fp.write("Median = %.10g\n"%(BinMedian))
    print(   "Mode   = %.10g"  %(BinMode))
    fp.write("Mode   = %.10g\n"%(BinMode))
    print(   "Sigma  = %.10g"  %(BinSigma))
    fp.write("Sigma  = %.10g\n"%(BinSigma))
    fp.close()



# 
# Loop to make sure we get Gaussian fitting for the histogram
# 

BinNumb = 0
BinLoop = True

while BinLoop and BinNumb <= (len(BinVar)/1.5):
    # 
    # Bin pixel value histogram
    # 
    BinNumb = BinNumb + 1000
    BinHists, BinEdges, BinPatches = pl.hist(BinVar, BinNumb, histtype='stepfilled', color=hex2color('#0000FF'), linewidth=0.2) # histtype='bar', 'step', 'stepfilled'
    BinCents = (BinEdges[:-1] + BinEdges[1:]) / 2.0
    
    
    # 
    # Fit the histogram
    # 
    FitInnerSigma = 5.0
    FitRange = []
    FitRange = np.where((BinCents>=(BinMean-FitInnerSigma*BinSigma)) & (BinCents<=(BinMean+FitInnerSigma*BinSigma))) # logical_and (() & ())
    if len(FitRange) == 0:
        FitRange = range(len(BinCents))
    print("Fitting_range = %.10g %.10g (nbins = %d, ndata = %d)"%(np.min(BinCents[FitRange]), np.max(BinCents[FitRange]), BinNumb, len(BinVar)))
    # 
    FitParam = {'A': np.nan, 'mu': np.nan, 'sigma': np.nan}
    # 
    # try fitting
    if True:
        try:
            FitGauss, FitParam = fit_Gaussian_1D(BinCents[FitRange], BinHists[FitRange], np.max(BinHists[FitRange]), np.min([BinMode,BinMedian]), BinSigma)
        except:
            FitParam = {'A': np.nan, 'mu': np.nan, 'sigma': np.nan}
        # 
        if FitParam['mu'] < np.min(BinCents[FitRange]) or FitParam['mu'] > np.max(BinCents[FitRange]):
            FitParam = {'A': np.nan, 'mu': np.nan, 'sigma': np.nan}
    # 
    # <20170228> added another trial fitting
    if FitParam['sigma'] == np.nan or FitParam['sigma'] <= 0.0:
        try:
            FitGauss, FitParam = fit_Gaussian_1D(BinCents[FitRange], BinHists[FitRange], np.max(BinHists[FitRange]), np.min([BinMode,BinMedian]), BinSigma/2.0)
        except:
            FitParam = {'A': np.nan, 'mu': np.nan, 'sigma': np.nan}
        # 
        if FitParam['mu'] < np.min(BinCents[FitRange]) or FitParam['mu'] > np.max(BinCents[FitRange]):
            FitParam = {'A': np.nan, 'mu': np.nan, 'sigma': np.nan}
    # 
    # <20170228> added another trial fitting
    if FitParam['sigma'] == np.nan or FitParam['sigma'] <= 0.0:
        try:
            FitGauss, FitParam = fit_Gaussian_1D(BinCents[FitRange], BinHists[FitRange], np.max(BinHists[FitRange]), np.min([BinMode,BinMedian]), BinSigma*2.0)
        except:
            FitParam = {'A': np.nan, 'mu': np.nan, 'sigma': np.nan}
        # 
        if FitParam['mu'] < np.min(BinCents[FitRange]) or FitParam['mu'] > np.max(BinCents[FitRange]):
            FitParam = {'A': np.nan, 'mu': np.nan, 'sigma': np.nan}
    # 
    # <20170224> added a check step to make sure we measure the FitGauss
    if FitParam['sigma'] != np.nan and FitParam['sigma'] > 0.0:
        # 
        pl.plot(BinCents[FitRange], FitGauss, color=hex2color('#FF0000'), linewidth=3, linestyle='solid') # marker='o', markerfacecolor='blue', markersize=12)
        pl.text(FitParam['mu']+1.0*FitParam['sigma'], FitParam['A'], 'sigma = %.10g'%(FitParam['sigma']), color=hex2color('#FF0000'), fontsize=18)
        # output to txt file
        with open('%s.pixel.statistics.txt'%(FitsFile), 'a') as fp:
            print(   "Gaussian_A     = %.10g"  %(FitParam['A'])     )
            fp.write("Gaussian_A     = %.10g\n"%(FitParam['A'])     )
            print(   "Gaussian_mu    = %.10g"  %(FitParam['mu'])    )
            fp.write("Gaussian_mu    = %.10g\n"%(FitParam['mu'])    )
            print(   "Gaussian_sigma = %.10g"  %(FitParam['sigma']) )
            fp.write("Gaussian_sigma = %.10g\n"%(FitParam['sigma']) )
            fp.close()
        # 
        BinLoop = False # this will jump out of the loop

#FitGauss = mlab.normpdf(BinEdges, BinMean, BinSigma)
#FitGauss = FitGauss / np.max(FitGauss) * np.max(BinHists)
pl.xlabel("Pixel Value")
pl.ylabel("N")


# 
# Save eps
# 
#pl.show()
pl.tight_layout()
fig.savefig('%s.pixel.histogram.eps'%(FitsFile), format='eps')
#os.system('open "%s.pixel.histogram.eps"'%(FitsFile))




# 
# Then also plot ylog
# 
#pl.show()
pl.clf()
pl.yscale('log')
pl.hist(BinVar, BinNumb, log=True, histtype='stepfilled', color=hex2color('#0000FF'), linewidth=0.2)
pl.ylim([-0.75, (np.max(BinHists))*10**0.35])

if type(FitParam) is dict and len(FitRange)>0:
    if FitParam['sigma'] != np.nan and FitParam['sigma'] > 0.0:
        pl.semilogy(BinCents[FitRange], FitGauss, color=hex2color('#FF0000'), linewidth=3, linestyle='solid') # -- You simply need to use semilogy instead of plot -- http://stackoverflow.com/questions/773814/plot-logarithmic-axes-with-matplotlib-in-python
        pl.text(FitParam['mu']+1.0*FitParam['sigma'], FitParam['A'], 'sigma = %.10g'%(FitParam['sigma']), color=hex2color('#FF0000'), fontsize=18)

pl.xlabel("Pixel Value")
pl.ylabel("log N")


# 
# Save eps
# 
#pl.show()
pl.tight_layout()
fig.savefig('%s.pixel.histogram.ylog.eps'%(FitsFile), format='eps')
#os.system('open "%s.pixel.histogram.ylog.eps"'%(FitsFile))


print('Done!')

