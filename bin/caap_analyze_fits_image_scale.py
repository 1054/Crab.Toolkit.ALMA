#!/usr/bin/env python2.7
# 


import os, sys
import numpy as np
import scipy
import astropy
from astropy.io import fits
import matplotlib
import platform
if platform.system() == 'Darwin':
    matplotlib.use('Qt5Agg')
else:
    matplotlib.use('TkAgg') # must before import pyplot
import matplotlib.pyplot as pl
import matplotlib.mlab as mlab
from matplotlib.colors import LogNorm
from matplotlib.colors import hex2color, rgb2hex
from astropy.wcs import WCS
import wcsaxes
from astropy.visualization import MinMaxInterval, PercentileInterval, AsymmetricPercentileInterval, SqrtStretch, PowerStretch, ImageNormalize


from caap_analyze_fits_image_pixel_mode import mode
from caap_fit_Gaussian_1D import fit_Gaussian_1D


#print(pl.rcParams.keys())
#pl.rcParams['font.family'] = 'NGC'
pl.rcParams['font.size'] = 20
#pl.rcParams['axes.labelsize'] = 'large'
pl.rcParams['axes.labelpad'] = 12 # padding between axis and xy title (label)
#pl.rcParams['xtick.major.pad'] = 10 # padding between ticks and axis
#pl.rcParams['ytick.major.pad'] = 10 # padding between ticks and axis
pl.rcParams['xtick.labelsize'] = 20
pl.rcParams['ytick.labelsize'] = 20
pl.rcParams['xtick.minor.visible'] = True # 
pl.rcParams['ytick.minor.visible'] = True # 
pl.rcParams['figure.figsize'] = (21.0*0.90), (21.0*0.90) # width = 90% A4 width , height = width. 


fig = pl.figure()




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
print('Input fits file: %s'%(FitsFile))


# 
# Read input fits image
# 
FitsStruct = fits.open(FitsFile)
FitsImage = FitsStruct[0].data
FitsHeader = FitsStruct[0].header


# 
# Make sure 2D
# 
if len(FitsImage.shape) != 2:
    FitsImage = FitsImage.reshape((long(FitsHeader['NAXIS2']),long(FitsHeader['NAXIS1'])))
    

# 
# Fix fits header NAXIS>2 problem
# 
if long(FitsHeader['NAXIS'])>2:
    for i in range(3,long(FitsHeader['NAXIS'])+1):
        if 'NAXIS%d'%(i) in FitsHeader:
            del FitsHeader['NAXIS%d'%(i)]
            try:
                del FitsHeader['CRVAL%d'%(i)]
                del FitsHeader['CRPIX%d'%(i)]
                del FitsHeader['CTYPE%d'%(i)]
                del FitsHeader['CDELT%d'%(i)]
                del FitsHeader['CUNIT%d'%(i)]
            except:
                pass
            for j in range(i):
                try:
                    del FitsHeader['PC%02d_%02d'%(i,j+1)]
                    del FitsHeader['PC%02d_%02d'%(j+1,i)]
                except:
                    pass
FitsHeader['NAXIS'] = 2
#print(FitsHeader)
FitsImageWCS = WCS(FitsHeader)
FitsImagePixScale = astropy.wcs.utils.proj_plane_pixel_scales(FitsImageWCS) * 3600.0 # arcsec
#print(FitsImageWCS)

# 
# Make WCS plot
# 
panel_rect = [0.12,0.12,1.00-0.12-0.05,1.00-0.12-0.05] # l, b, w, h
axes = fig.add_axes(panel_rect, projection=FitsImageWCS)
axes.coords[0].set_major_formatter('hh:mm:ss.s')
axes.coords[1].set_major_formatter('dd:mm:ss')
axes.grid(False) # not working...
axes.set_xlabel('RA')
axes.set_ylabel('Dec')
# print info
print('Image dimension %s'%(str(FitsImage.shape)))
print("Pixel scale %.3f [arcsec/pixel]"%(np.mean(FitsImagePixScale)))


# 
# Plot the fits image
# 
pl.imshow(FitsImage, cmap='gray', origin='lower', aspect='equal') # cmap='binary' 'gray'
#cb = pl.colorbar()
# 
# Save eps
# 
fig.savefig('%s.scale.linear.jpg'%(FitsFile), format='jpg')
print('Output to %s'%('%s.scale.linear.jpg'%(FitsFile)))


# 
# Plot the fits image in logNorm
# 
pl.cla()
#fig.delaxes(fig.axes[-1]) # remove previous colorbar
#pl.subplots_adjust(left=panel_rect[0], bottom=panel_rect[1], right=panel_rect[0]+panel_rect[2], top=panel_rect[1]+panel_rect[3])
pl.imshow(FitsImage, cmap='gray', origin='lower', aspect='equal', norm=LogNorm())
#cb = pl.colorbar()
# 
# Save eps
# 
fig.savefig('%s.scale.log.jpg'%(FitsFile), format='jpg')
print('Output to %s'%('%s.scale.log.jpg'%(FitsFile)))


# 
# Plot the fits image in 99.5 percentile
# 
if [[ 1 == 0 ]]; then
    pl.cla()
    #fig.delaxes(fig.axes[-1]) # remove previous colorbar
    #pl.subplots_adjust(left=panel_rect[0], bottom=panel_rect[1], right=panel_rect[0]+panel_rect[2], top=panel_rect[1]+panel_rect[3])
    normfun = ImageNormalize(FitsImage, interval=AsymmetricPercentileInterval(19.5,99.5))
    pl.imshow(FitsImage, cmap='gray', origin='lower', aspect='equal', norm=normfun)
    #cb = pl.colorbar()
    # 
    # Save eps
    # 
    fig.savefig('%s.scale.995.jpg'%(FitsFile), format='jpg')
    print('Output to %s'%('%s.scale.995.jpg'%(FitsFile)))



print('Done!')

