#!/usr/bin/env python2.7
# 
# Aim:
#     Simple image crop and photometry.
# 
# Last update:
#     20170308 -- measure weighted peak pixel position within each ellipse -- "cpix"
# 

try:
    import pkg_resources
except ImportError:
    raise SystemExit("Error! Failed to import pkg_resources!")

pkg_resources.require("numpy")
pkg_resources.require("astropy")
pkg_resources.require("matplotlib")
pkg_resources.require("scipy")

import os, sys, math, numpy, matplotlib
from matplotlib.patches import Ellipse, Circle, Rectangle
from astropy.wcs import WCS
from scipy import ndimage
import copy


























# 
def crop(image, zoomrect, imagewcs=[]):
    """
    Return the cropped image at the x1, x2, y1, y2 coordinates -- http://stackoverflow.com/questions/7665076/matplotlib-imshow-zoom-function
    """
    i0 = numpy.round(zoomrect[0]).astype(long)-1
    i1 = numpy.round(zoomrect[1]).astype(long)-1
    j0 = numpy.round(zoomrect[2]).astype(long)-1
    j1 = numpy.round(zoomrect[3]).astype(long)-1
    if i0 <= 0:
        i0 = 0
    if j0 <= 0:
        j0 = 0
    if i1 == -1 or i1 >= image.shape[1]-1:
        i1 = image.shape[1]-1
        # note that numpy image.shape[1] is NAXIS1
    if j1 == -1 or j1 >= image.shape[1]-1:
        j1 = image.shape[0]-1
        # note that numpy image.shape[0] is NAXIS2
    mask = numpy.zeros(image.shape)
    mask[j0:j1+1,i0:i1+1] = 1
    m = (mask>0)
    if imagewcs:
        zoomwcs = copy.copy(imagewcs)
        zoomwcs.wcs.crpix = imagewcs.wcs.crpix - numpy.array([i0, j0])
        #zoomwcs.wcs.cdelt does not change # = zoomwcs.wcs.cdelt / numpy.array((image.shape[1],image.shape[0])) / numpy.array((j1+1-j0, i1+1-i0))
        return image[m].reshape((j1+1-j0, i1+1-i0)), zoomwcs
    return image[m].reshape((j1+1-j0, i1+1-i0))





# 
def elliptical_Photometry(image, ellipse=Ellipse([0,0],0,0,0), imagewcs=[], verbose=True):
    """
    elliptical_Photometry, ellipse are ds9-style coordinates (starting from 1) with major and minor FWHM in unit of pixels and pos angle in degree. 
    e.g. [100,100,12,5,90]
    """
    if len(image)==0:
        print("Error! The input image of elliptical_Photometry() is empty!")
        sys.exit()
    if not ellipse:
        print("Error! The input ellipse of elliptical_Photometry() is empty!")
        sys.exit()
    # 
    xc = numpy.array(ellipse.center[0]).astype(float)
    yc = numpy.array(ellipse.center[1]).astype(float)
    i0 = numpy.round(ellipse.center[0]).astype(long)-1
    j0 = numpy.round(ellipse.center[1]).astype(long)-1
    amaj = numpy.array(ellipse.width).astype(float)
    amin = numpy.array(ellipse.height).astype(float)
    aang = numpy.array(ellipse.angle).astype(float) / 180.0 * math.pi # -pi to pi
    # 
    #xc = 742.0
    #yc = 740.0
    #amaj = 20.4 # 2.5
    #amin = 20.4 # 2.5
    #aang = 0.0
    # 
    #<BUGGY><20170313># mask_x, mask_y = zip( *( (x+1.0, y+1.0) for y in range(image.shape[1]) for x in range(image.shape[0]) ) ) # numpy.zeros(image.shape) # -- http://stackoverflow.com/questions/9082829/creating-2d-coordinates-map-in-python
    mask_x, mask_y = zip( *( (x+1.0, y+1.0) for y in range(image.shape[0]) for x in range(image.shape[1]) ) ) # numpy.zeros(image.shape) # -- http://stackoverflow.com/questions/9082829/creating-2d-coordinates-map-in-python
    mask_x = numpy.array(mask_x).reshape(image.shape)
    mask_y = numpy.array(mask_y).reshape(image.shape)
    #pprint(mask_x)
    #pprint(mask_y)
    #print(mask_x.shape)
    #print(mask_y.shape)
    mask_xdis = (mask_x-xc)
    mask_ydis = (mask_y-yc)
    mask_rdis = numpy.sqrt(mask_xdis**2 + mask_ydis**2)
    mask_aang = numpy.arctan2(mask_ydis, mask_xdis) # -pi to pi
    mask_rlim = numpy.sqrt((amaj/2.0*numpy.cos(aang-mask_aang))**2 + (amin/2.0*numpy.sin(aang-mask_aang))**2)
    mask_rsub = ( mask_rdis - mask_rlim )
    #pprint(mask_rdis)
    #pprint(rdis)
    # 
    # count pixels including fractional pixels near the edge
    mask = numpy.zeros(image.shape)
    npix = 0
    m = (mask_rsub<-0.5)
    mask[m] = 1.0
    m = ((mask_rsub>=-0.5) & (mask_rsub<0.0)) # consider fractional pixels
    mask[m] = 0.5-mask_rsub[m] # -0.5 -> 1.0, -0.0 -> 0.5
    m = ((mask_rsub>=0.0) & (mask_rsub<0.5)) # consider fractional pixels
    mask[m] = 0.5-mask_rsub[m] # 0.0 -> 0.5, 0.5 -> 0.0
    f = numpy.sum(image*mask)
    npix = numpy.sum(mask)
    # 
    # count integer pixels only
    mask_pix = numpy.zeros(image.shape)
    m_pix = (mask_rsub<=0.0)
    mask_pix[m_pix] = 1.0
    f_pix = numpy.sum(image*mask_pix)
    # 
    # compute weighted center
    #cpix_x = numpy.mean(numpy.sum(mask_x*image*mask)/numpy.sum(image*mask))
    #cpix_y = numpy.mean(numpy.sum(mask_y*image*mask)/numpy.sum(image*mask))
    #cpix_x = numpy.mean(numpy.sum(mask_x*image*mask_pix)/numpy.sum(image*mask_pix))
    #cpix_y = numpy.mean(numpy.sum(mask_y*image*mask_pix)/numpy.sum(image*mask_pix))
    # compute weighted center <bug><fixed><20170503><dzliu>
    #print(numpy.sum(mask_x*image*mask, axis=1) / numpy.sum(image*mask, axis=1))
    #print(numpy.sum(mask_y*image*mask, axis=0) / numpy.sum(image*mask, axis=0))
    # compute weighted center with image*mask_negative
    #mask_negative = copy.copy(mask)
    #m_negative = (image<=0.0)
    #mask_negative[m_negative] = 0.0
    #print(numpy.sum(mask_negative))
    #cpix_x = numpy.nanmean(numpy.sum(mask_x*image*mask_negative, axis=1) / numpy.sum(image*mask_negative, axis=1)) # sum(axis=1) should be summing image X rows for each Y
    #cpix_y = numpy.nanmean(numpy.sum(mask_y*image*mask_negative, axis=0) / numpy.sum(image*mask_negative, axis=0)) # sum(axis=0) should be summing image Y cols for each X
    #cpix = (cpix_x, cpix_y)
    # compute weighted center with image*mask_negative with scipy
    mask_negative = copy.copy(mask)
    m_negative = (image<=0.0)
    mask_negative[m_negative] = 0.0
    print(image*mask)
    cpix = ndimage.measurements.center_of_mass(image*mask)
    cpix_x, cpix_y = cpix
    # 
    # compute image ra dec if imagewcs
    #if imagewcs:
    #    radec_c = imagewcs.wcs_pix2world(xc, yc, 1) # 3rd arg: origin is the coordinate in the upper left corner of the image. In FITS and Fortran standards, this is 1. In Numpy and C standards this is 0.
    #    if(verbose):
    #        print("elliptical_Photometry: xc=%.2f yc=%.2f ra=%.7f dec=%.7f amaj/2=%.2f amin/2=%.2f aang=%.2f npix=%.2f cpix=[%.2f,%.2f] fpix=%g f=%g"%(xc, yc, radec_c[0], radec_c[1], amaj/2.0, amin/2.0, aang/math.pi*180.0, npix, cpix_x, cpix_y, f_pix, f))
    #else:
    #    if(verbose):
    #        print("elliptical_Photometry: xc=%.2f yc=%.2f amaj/2=%.2f amin/2=%.2f aang=%.2f npix=%.2f cpix=[%.2f,%.2f] fpix=%g f=%g"%(xc, yc, amaj/2.0, amin/2.0, aang/math.pi*180.0, npix, cpix_x, cpix_y, f_pix, f))
    if(verbose):
        print("elliptical_Photometry: xc=%.2f yc=%.2f amaj/2=%.2f amin/2=%.2f aang=%.2f npix=%.2f cpix=[%.2f,%.2f] fpix=%g f=%g"%(xc, yc, amaj/2.0, amin/2.0, aang/math.pi*180.0, npix, cpix_x, cpix_y, f_pix, f))
    #print(image[0,0])
    return f, npix, cpix




























