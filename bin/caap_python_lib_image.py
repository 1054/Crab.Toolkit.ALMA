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

import os, sys, math, numpy, matplotlib
from matplotlib.patches import Ellipse, Circle, Rectangle
from astropy.wcs import WCS
























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
    if j1 == -1 or j1 >= image.shape[1]-1:
        j1 = image.shape[0]-1
    mask = numpy.zeros(image.shape)
    mask[j0:j1+1,i0:i1+1] = 1
    m = (mask>0)
    if imagewcs:
        zoomwcs = imagewcs
        zoomwcs.crpix = imagewcs.crpix - numpy.array([i0, j0])
        return image[m].reshape((j1+1-j0, i1+1-i0)), zoomwcs
    return image[m].reshape((j1+1-j0, i1+1-i0))





# 
def elliptical_Photometry(image, ellipse=Ellipse([0,0],0,0,0)):
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
    mask_x, mask_y = zip( *( (x+1.0, y+1.0) for y in range(image.shape[1]) for x in range(image.shape[0]) ) ) # numpy.zeros(image.shape) # -- http://stackoverflow.com/questions/9082829/creating-2d-coordinates-map-in-python
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
    cpix_x = numpy.mean(numpy.sum(mask_x*image*mask)/numpy.sum(image*mask))
    cpix_y = numpy.mean(numpy.sum(mask_y*image*mask)/numpy.sum(image*mask))
    cpix = (cpix_x, cpix_y)
    # 
    print("elliptical_Photometry: xc=%.2f yc=%.2f amaj/2=%.2f amin/2=%.2f aang=%.2f npix=%.2f"%(xc, yc, amaj/2.0, amin/2.0, aang/math.pi*180.0, numpy.sum(mask)))
    #print(image[0,0])
    return f, npix, cpix




























