#!/usr/bin/env python2.7
# 
# 

import os, sys

if len(sys.argv) <= 1:
    print('Usage: caap_generate_PSF_Gaussian_2D "input.image.fits" "output.PSF_Gaussian_2D.fits"')
    sys.exit()



import os, sys
import numpy
import astropy
from astropy.modeling.models import Gaussian2D
from astropy.convolution import Gaussian2DKernel
from astropy.convolution import convolve, convolve_fft
from astropy.io import fits
from astropy.wcs import WCS



# Open input fits file
hdulist = fits.open(sys.argv[1])

# Prepare output fits file
outfile = sys.argv[1].replace('.fits', '.PSF_Gaussian_2D.fits')
if len(sys.argv) >= 3:
    outfile = sys.argv[2]


# search BMAJ, BMIN and BPA keywords, make 2D Gaussian, then output to outfile
if 'BMAJ' in hdulist[0].header and 'BMIN' in hdulist[0].header and 'BPA' in hdulist[0].header:
    
    fitswcs = WCS(hdulist[0].header)
    pixscale_array = astropy.wcs.utils.proj_plane_pixel_scales(fitswcs)
    pixscale_ra = pixscale_array[0] * 3600.0 # arcsec
    pixscale_dec = pixscale_array[0] * 3600.0 # arcsec
    pixscale = numpy.sqrt(pixscale_ra**2 + pixscale_dec**2) # arcsec
    print('psf pixscale in arcsec %.4f %.4f'%(pixscale_ra, pixscale_dec))
    
    stddev_major = float(hdulist[0].header['BMAJ']) * 3600.0 / (2.0*numpy.sqrt(2.0*numpy.log(2.0))) # arcsec
    stddev_minor = float(hdulist[0].header['BMIN']) * 3600.0 / (2.0*numpy.sqrt(2.0*numpy.log(2.0))) # arcsec
    theta = float(hdulist[0].header['BPA']) # degree, from +Y, https://github.com/astropy/astropy/issues/3550
    print('psf major minor theta %.4f %.4f %.2f'%(stddev_major, stddev_minor, theta))
    
    #theta = 0.0 # theta = 0.0 is +X direction! checked by dzliu 20170305.
    #theta = 90.0/180.0*numpy.pi # theta = 90.0 is +Y direction! checked by dzliu 20170305.
    
    PsfModel = Gaussian2D(1.0000, 0.0, 0.0, stddev_major/pixscale, stddev_minor/pixscale, (theta+90.0)/180.0*numpy.pi) # amplitude, x_mean, y_mean, x_stddev, y_stddev, theta
    PsfNAXIS = numpy.max([stddev_major, stddev_minor]) / pixscale * 15.0
    PsfNAXIS = numpy.round((PsfNAXIS-1.0)/2.0)*2+1 # make it odd number
    PsfNAXIS = numpy.array([PsfNAXIS, PsfNAXIS])
    print('psf model model naxis %d %d'%(PsfNAXIS[0], PsfNAXIS[1]))
    PsfModel.bounding_box = ((-(PsfNAXIS[0]-1)/2, (PsfNAXIS[0]-1)/2), (-(PsfNAXIS[1]-1)/2, (PsfNAXIS[1]-1)/2))
    PsfImage = PsfModel.render()
    #print(PsfModel.render())
    
    hdr = fits.Header()
    hdr['BMAJ'] = hdulist[0].header['BMAJ']
    hdr['BMIN'] = hdulist[0].header['BMIN']
    hdr['BPA'] = hdulist[0].header['BPA']
    hdr['PIXSCALE'] = pixscale
    hdu = fits.PrimaryHDU(PsfImage, header=hdr)
    hduli = fits.HDUList([hdu])
    
    # output to outfile
    if os.path.isfile(outfile):
        os.system('mv \"%s\" \"%s\"'%(outfile, outfile.replace('.fits','.backup.fits')))
        print('Backed up existing \"%s\" as \"%s\"!'%(outfile, outfile.replace('.fits','.backup.fits')))
    hduli.writeto(outfile, overwrite=False)
    print('Output to \"%s\"!'%(outfile))


