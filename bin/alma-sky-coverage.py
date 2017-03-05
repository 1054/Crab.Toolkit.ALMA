#!/usr/bin/env python2.7
# 


try:
    import pkg_resources
except ImportError:
    raise SystemExit("Error! Failed to import pkg_resources!")

pkg_resources.require("numpy")
pkg_resources.require("astropy>=1.3")

import os
import sys
import time
import glob
import math
import numpy
import astropy
from astropy import units
from astropy import constants
from astropy.io import fits
import astropy.io.ascii as asciitable

from pprint import pprint
from datetime import datetime
from dateutil import parser

import matplotlib
matplotlib.use('Qt5Agg') # must before import pyplot
from matplotlib import pyplot
from matplotlib.colors import hex2color, rgb2hex
from matplotlib.patches import Ellipse, Circle, Rectangle, Polygon
from matplotlib.lines import Line2D
from astropy.visualization import astropy_mpl_style
from astropy.visualization import MinMaxInterval, PercentileInterval, AsymmetricPercentileInterval, SqrtStretch, PowerStretch, ImageNormalize
from astropy.wcs import WCS

import wcsaxes







# 
# Check input arguments
# 
if len(sys.argv) <= 1:
    print("Usage: ")
    print("  alma-sky-coverage.py \"fits_image.fits\"")
    print("  alma-sky-coverage.py \"fits_image.fits\" \"more_coverage_polygon.txt\"")
    print("")
    sys.exit()

InputFitsFile = sys.argv[1]

if not os.path.isfile(InputFitsFile):
    print("Error! \"%s\" does not exist!"%(InputFitsFile))
    sys.exit()








# 
# Auxillary Class
# 
class ZoomPan:
    # 
    # -- http://stackoverflow.com/questions/11551049/matplotlib-plot-zooming-with-scroll-wheel
    # 
    def __init__(self):
        self.press = None
        self.cur_xlim = None
        self.cur_ylim = None
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.xpress = None
        self.ypress = None
    # 
    def zoom_factory(self, ax, base_scale = 2.):
        def zoom(event):
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()

            xdata = event.xdata # get event x location
            ydata = event.ydata # get event y location

            if event.button == 'down':
                # deal with zoom in
                scale_factor = 1 / base_scale
            elif event.button == 'up':
                # deal with zoom out
                scale_factor = base_scale
            else:
                # deal with something that should never happen
                scale_factor = 1
                print event.button

            new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
            new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

            relx = (cur_xlim[1] - xdata)/(cur_xlim[1] - cur_xlim[0])
            rely = (cur_ylim[1] - ydata)/(cur_ylim[1] - cur_ylim[0])

            ax.set_xlim([xdata - new_width * (1-relx), xdata + new_width * (relx)])
            ax.set_ylim([ydata - new_height * (1-rely), ydata + new_height * (rely)])
            ax.figure.canvas.draw()

        fig = ax.get_figure() # get the figure of interest
        fig.canvas.mpl_connect('scroll_event', zoom)

        return zoom
    # 
    def pan_factory(self, ax):
        def onPress(event):
            if event.inaxes != ax: return
            self.cur_xlim = ax.get_xlim()
            self.cur_ylim = ax.get_ylim()
            self.press = self.x0, self.y0, event.xdata, event.ydata
            self.x0, self.y0, self.xpress, self.ypress = self.press
        # 
        def onRelease(event):
            self.press = None
            ax.figure.canvas.draw()
        # 
        def onMotion(event):
            if self.press is None: return
            if event.inaxes != ax: return
            dx = event.xdata - self.xpress
            dy = event.ydata - self.ypress
            self.cur_xlim -= dx
            self.cur_ylim -= dy
            ax.set_xlim(self.cur_xlim)
            ax.set_ylim(self.cur_ylim)
            
            ax.figure.canvas.draw()
        # 
        fig = ax.get_figure() # get the figure of interest
        # 
        # attach the call back
        fig.canvas.mpl_connect('button_press_event',onPress)
        fig.canvas.mpl_connect('button_release_event',onRelease)
        fig.canvas.mpl_connect('motion_notify_event',onMotion)
        # 
        #return the function
        return onMotion



# 
# Auxillary function
# 
def rotate(origin, points, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.
    
    The angle should be given in degrees.
    
    http://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
    """
    rotated_points = []
    
    for point in points:
        ox, oy = origin
        px, py = point
        qx = ox + numpy.cos(numpy.deg2rad(angle)) * (px - ox) - numpy.sin(numpy.deg2rad(angle)) * (py - oy)
        qy = oy + numpy.sin(numpy.deg2rad(angle)) * (px - ox) + numpy.cos(numpy.deg2rad(angle)) * (py - oy)
        rotated_points.append( (qx, qy) )
    
    return rotated_points



# 
# Auxillary function
# 
def calc_alma_beam_from_freq_str(freq_str):
    # 
    # compute beam size which varies with frequency
    # 
    freq_list = [item.split(',') for item in freq_str.split(' U ')]
    freq_list = [item for sublist in freq_list for item in sublist]
    freq_list = [item.split('..') for item in freq_list]
    freq_list = [item for sublist in freq_list for item in sublist]
    freq_list = [item.split('[') for item in freq_list]
    freq_list = [item for sublist in freq_list for item in sublist]
    freq_list = [item.split(']') for item in freq_list]
    freq_list = [item for sublist in freq_list for item in sublist]
    freq_list = [item for item in freq_list if not (item == '')]
    freq_list = [item for item in freq_list if not (item.startswith('null'))]
    freq_list = [item for item in freq_list if not (item.endswith('kHz'))]
    freq_list = [item.replace('GHz','') for item in freq_list]
    freq_list = [item.replace('XX','NaN') for item in freq_list]
    freq_list = [item.replace('YY','NaN') for item in freq_list]
    freq_list = [item.replace('XY','NaN') for item in freq_list]
    freq_list = [item.replace('YX','NaN') for item in freq_list]
    freq_list = [item.replace(' ','') for item in freq_list]
    freq_list = [item.replace('NaNNaN','NaN') for item in freq_list]
    freq_list = [item.replace('NaNNaN','NaN') for item in freq_list]
    freq_list = [item.replace('NaNNaN','NaN') for item in freq_list]
    freq_list = [item.replace('NaNNaN','NaN') for item in freq_list]
    #print(freq_list)
    freq_list = [float(item) for item in freq_list]
    freq_mean = numpy.nanmean(freq_list) # GHz
    beam_size = 1.02 * (constants.c.to('m/s').value/(freq_mean*1e9)) / 12.0 / math.pi * 180.0 * 3600.0 # 12m telescope HPBW -- https://www.iram.fr/IRAMFR/ARC/documents/cycle3/alma-technical-handbook.pdf Equation(3.4)
    # 
    return beam_size, freq_mean, freq_list

# 
# Auxillary function
# 
def find_closest_data_point(points, posxy):
    return sorted( points, key=lambda p: (p[0]-posxy[0])*(p[0]-posxy[0])+(p[1]-posxy[1])*(p[1]-posxy[1]) )[0]

































# 
# MAIN PROGRAM
# 


# 
# ALMA archive file
# 
#AlmaTableFile = '%s/data/COSMOS_1degree_ALMA_Archive_asa_query_result_2016-12-29_11-28-04_edited_by_dzliu.fits'%(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AlmaTableFile = '%s/data/alma_archive_queried_all_v20170215.csv'%(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# 
# Read ALMA Table
# 
if AlmaTableFile.endswith('.fits'):
    print "Reading Fits Table: %s"%(AlmaTableFile)
    FitsTableStruct = fits.open(AlmaTableFile)
    TableColumns = []
    TableData = []
    TableHeaders = []
    # 
    for TableId in range(len(FitsTableStruct)):
        if type(FitsTableStruct[TableId]) is astropy.io.fits.hdu.table.BinTableHDU:
            TableColumns = FitsTableStruct[TableId].columns
            TableData = FitsTableStruct[TableId].data
    # 
    if(len(TableData)==0):
        print "Error! Empty Fits Table or failed to read the Fits Table!"
        sys.exit()
    else:
        TableHeaders = TableColumns.names
    # 
    #print a column
    #print(TableData.field('FWHM_MAJ_FIT'))
else:
    print "Reading ALMA Archive Table: %s"%(AlmaTableFile)
    TableData = asciitable.read(AlmaTableFile)
    # 
    #print a column
    #print(TableData.field('Project code'))


# 
# Get data columns
# 
List_Project = TableData.field('Project code')
List_Source = TableData.field('Source name')
List_RA = TableData.field('RA')
List_Dec = TableData.field('Dec')
List_FreqStr = TableData.field('Frequency support') # str
List_DateObsStr = TableData.field('Observation date') # str
List_DatePubStr = TableData.field('Release date') # str
List_Integration = TableData.field('Integration')
List_DateObs = []
List_DatePub = []
List_FreqSpw = []
List_Freq = []
List_Beam = []

# for i in range(len(List_Project)):
#     #print(type(List_Project[i])) # str
#     #print(type(List_Source[i]))  # str
#     #print(type(List_RA[i]))      # float
#     #print(type(List_Dec[i]))     # float
#     #print(type(List_Freq[i]))    # str
#     #print((List_Project[i]))
#     #print((List_Source[i]))
#     #print((List_RA[i]))
#     #print((List_Dec[i]))
#     beam_size, freq_mean, freq_list = calc_alma_beam_from_freq_str(List_FreqStr[i])
#     List_FreqSpw.append(freq_list)
#     List_Freq.append(freq_mean)
#     List_Beam.append(beam_size)
#     #print(Temp_Freq)
#     #print(List_Beam)
#     #break
#     # 
#     if List_DateObsStr[i] != '':
#         List_DateObs.append(parser.parse(List_DateObsStr[i]))
#     else:
#         List_DateObs.append(datetime(10,1,1))
#     # 
#     if List_DatePubStr[i] != '':
#         List_DatePub.append(parser.parse(List_DatePubStr[i]))
#     else:
#         List_DatePub.append(datetime(10,1,1))
#     # 
#     #if i == 0:
#     #    print(type((List_DateObs[i])))
# 
# #pprint(zip(List_Project,List_Source,List_Freq,List_Beam))
# #pprint(zip(List_Project, List_Source, List_RA, List_Dec, List_FreqSpw, List_Freq, List_Beam))
# 
# List_Records = numpy.array(
#                    zip(List_Project, List_Source, List_RA, List_Dec, List_Beam, List_Freq, List_FreqSpw, List_DateObs, List_DatePub, List_Integration), 
#                    dtype = numpy.dtype({'names':['Project','Source','RA','Dec','BeamSize','Frequency','FrequencySpw','DateObs','DatePub','Integration'], 
#                                         'formats':['S30', 'S100', float, float, float, float, list, datetime, datetime, float]})
#                )
# 
# List_Records = numpy.rec.array(List_Records, dtype=List_Records.dtype)
# 
# List_Records.sort(order='DateObs')
# 
# #pprint(List_Records[['Source','BeamSize','DateObs']])
# #print("")













# 
# Read Fits Image
# 
FitsImageFile = InputFitsFile # 'pep_COSMOS_green_Map.DR1.sci.fits'
print("Reading FitsImageFile %s"%(FitsImageFile))
FitsImageStruct = fits.open(FitsImageFile)
FitsImageData = []
FitsImageHeader = []
for ExtId in range(len(FitsImageStruct)):
    print("Reading extension %d: %s"%(ExtId, FitsImageStruct[ExtId]))
    if type(FitsImageStruct[ExtId]) is astropy.io.fits.hdu.image.PrimaryHDU or \
       type(FitsImageStruct[ExtId]) is astropy.io.fits.hdu.image.ImageHDU:
       if 'NAXIS' in FitsImageStruct[ExtId].header:
            if long((FitsImageStruct[ExtId].header)['NAXIS']) >= 2:
                FitsImageData = FitsImageStruct[ExtId].data
                FitsImageHeader = FitsImageStruct[ExtId].header
                FitsImageWCS = WCS(FitsImageHeader)
                FitsImagePixScale = astropy.wcs.utils.proj_plane_pixel_scales(FitsImageWCS) * 3600.0 # arcsec
                print("Getting FitsImagePixScale = %.3f [arcsec/pixel]"%(numpy.mean(FitsImagePixScale)))
                break
# 
if len(FitsImageData) == 0:
    print("Error to read FitsImageFile %s!"%(FitsImageFile))
    sys.exit()
# 
# fix fits image shape
if len(FitsImageData.shape) != 2:
    if 'NAXIS1' in FitsImageHeader and 'NAXIS2' in FitsImageHeader:
        FitsImageData.reshape( (long(FitsImageHeader['NAXIS2']), long(FitsImageHeader['NAXIS1'])) )
    else:
        FitsImageData.reshape( ((FitsImageData.shape)[len(FitsImageData.shape)-2], (FitsImageData.shape)[len(FitsImageData.shape)-1]))








# 
# Create Plot Device
# 
pyplot.style.use(astropy_mpl_style)
pyplot.rcParams.update({
    'font.family': 'NGC', 
    'font.size': 18, 
    'xtick.minor.visible': True, 
    'ytick.minor.visible': True, 
    'figure.figsize': [12, 10], 
    })
# add figure as plot device
PlotDevice = pyplot.figure()
# add wcs axis as plot panel -- https://media.readthedocs.org/pdf/wcsaxes/latest/wcsaxes.pdf
PlotPanel = PlotDevice.add_axes([0.10, 0.10, 0.85, 0.85], projection=FitsImageWCS) # plot RA Dec axes #  PlotPanel = PlotDevice.add_subplot(1,1,1)
# set wcs axis tick font size (not working...)
#for PlotTicks in (PlotPanel.get_xticklabels()+PlotPanel.get_yticklabels()):
#    PlotTicks.set_fontsize(50) # -- http://stackoverflow.com/questions/3899980/how-to-change-the-font-size-on-a-matplotlib-plot
# # set wcs axis tick str format
PlotPanel.coords[0].set_major_formatter('hh:mm:ss.s')
PlotPanel.coords[1].set_major_formatter('dd:mm:ss')
PlotPanel.grid(False) # not working...
PlotPanel.set_xlabel('RA')
PlotPanel.set_ylabel('Dec')
# set normalization function for image display
NormFunc = ImageNormalize(FitsImageData, interval=AsymmetricPercentileInterval(19.5,99.5))
PlotImage = PlotPanel.imshow(FitsImageData, origin='lower', cmap='binary', norm=NormFunc, aspect='equal')
# set anchor point for annotation text
PlotAnchor = [] # look for an anchor point where we show the annotation text
# loop 
for i in range(len(List_Source)):
    Source = List_Source[i]
    posxy = FitsImageWCS.wcs_world2pix(float(List_RA[i]), float(List_Dec[i]), 1) # 3rd arg: origin is the coordinate in the upper left corner of the image. In FITS and Fortran standards, this is 1. In Numpy and C standards this is 0.
    if posxy[0] >= 0 and posxy[0] <= (FitsImageData.shape)[1] and \
       posxy[1] >= 0 and posxy[1] <= (FitsImageData.shape)[0] :
        beam_size, freq_mean, freq_list = calc_alma_beam_from_freq_str(List_FreqStr[i])
        radxy = beam_size / numpy.mean(FitsImagePixScale)
        color = "mediumseagreen" # "mediumseagreen" for COSMOS
        alpha_min = 0.2 # 0.0 for COSMOS with other overlaying sky coverages
        alpha_max = 0.9 # 0.5 for COSMOS with other overlaying sky coverages
        integ = numpy.sqrt(float(List_Integration[i]) / 3600.0) # transparency. propotional to integration time, 
        if integ > alpha_max: integ = alpha_max
        if integ < alpha_min: integ = alpha_min
        PlotItem = Circle(xy=posxy, radius=radxy, edgecolor='none', facecolor=color, alpha=integ, linewidth=1, zorder=2) # set zorder=1 to make it at lowest layer
        #print("Drawing Circle %s"%(PlotItem))
        PlotPanel.add_artist(PlotItem)
        print("Getting ALMA pointing \"%s\" RA Dec %.7f %.7f at Freqyency %.3f GHz with BeamSize %.3f arcsec (%d/%d)" % \
                (Source, List_RA[i], List_Dec[i], freq_mean, beam_size, i+1, len(List_Source)))
        #pyplot.draw()
        #pyplot.pause(0.05)
        #break
        # 
        # look for an anchor point where we show the annotation text
        # here we use the Northest point
        if len(PlotAnchor) == 0:
            PlotAnchor = {'posxy':posxy, 'radxy':radxy, 'integ':integ}
        else:
            if PlotAnchor['posxy'][1] < posxy[1] and radxy*numpy.mean(FitsImagePixScale) > 30 and integ > 0.2:
                PlotAnchor = {'posxy':posxy, 'radxy':radxy, 'integ':integ}

pyplot.draw()
pyplot.pause(0.05)

# draw annotation text
print("Plotting Annotation at %.3f %.3f (ALMA archive pointings)"%(PlotAnchor['posxy'][0], PlotAnchor['posxy'][1]))
pyplot.text(PlotAnchor['posxy'][0], PlotAnchor['posxy'][1], 'ALMA archive pointings', color='seagreen', fontsize=16, horizontalalignment='left', verticalalignment='bottom', zorder=5)
pyplot.draw()
pyplot.pause(0.05)















###############################
#                             #
# Plot more coverage polygons #
#                             #
###############################

for i in range(2,len(sys.argv)):
    InputPolygonFile = sys.argv[i]
    if os.path.isfile(InputPolygonFile):
        with open(InputPolygonFile) as fp:
            t_coverage_name = ''
            t_coverage_color = 'red'
            t_coverage_linecolor = ''
            t_coverage_fontcolor = ''
            t_coverage_linewidth = 2.05
            t_coverage_linestyle = 'solid'
            t_coverage_transparency = 1.0
            t_coverage_fontsize = 16
            t_polygon_points = []
            t_anchor_point = [] # look for an anchor point where we show the annotation text
            for tmpstr in fp:
                if not tmpstr.startswith('#'):
                    if len(t_polygon_points) >= 0:
                        t_polygon_point = FitsImageWCS.wcs_world2pix(float(tmpstr.split()[0]), float(tmpstr.split()[1]), 1) # 3rd arg: origin is the coordinate in the upper left corner of the image. In FITS and Fortran standards, this is 1. In Numpy and C standards this is 0.
                        t_polygon_points.append((t_polygon_point[0],t_polygon_point[1]))
                elif tmpstr.replace(' ','').startswith('#color'):
                    if tmpstr.replace(' ','').replace('#color','').strip() != '':
                        t_coverage_color = tmpstr.replace(' ','').replace('#color','').strip()
                elif tmpstr.replace(' ','').startswith('#linecolor'):
                    if tmpstr.replace(' ','').replace('#linecolor','').strip() != '':
                        t_coverage_linecolor = tmpstr.replace(' ','').replace('#linecolor','').strip()
                elif tmpstr.replace(' ','').startswith('#linewidth'):
                    if tmpstr.replace(' ','').replace('#linewidth','').strip() != '':
                        t_coverage_linewidth = float(tmpstr.replace(' ','').replace('#linewidth','').strip())
                elif tmpstr.replace(' ','').startswith('#linestyle'):
                    if tmpstr.replace(' ','').replace('#linewidth','').strip() != '':
                        t_coverage_linewidth = tmpstr.replace(' ','').replace('#linewidth','').strip()
                elif tmpstr.replace(' ','').startswith('#fontsize'):
                    if tmpstr.replace(' ','').replace('#fontsize','').strip() != '':
                        t_coverage_fontsize = float(tmpstr.replace(' ','').replace('#fontsize','').strip())
                elif tmpstr.replace(' ','').startswith('#fontcolor'):
                    if tmpstr.replace(' ','').replace('#fontcolor','').strip() != '':
                        t_coverage_fontcolor = tmpstr.replace(' ','').replace('#fontcolor','').strip()
                elif tmpstr.replace(' ','').startswith('#transparency'):
                    if tmpstr.replace(' ','').replace('#transparency','').strip() != '':
                        t_coverage_transparency = 1.0 - float(tmpstr.replace(' ','').replace('#transparency','').strip())
                else:
                    if tmpstr.replace('#','').strip() != '':
                        t_coverage_name = tmpstr.replace('#','').strip()
            # determine color
            if t_coverage_linecolor == '':
                t_coverage_linecolor = t_coverage_color
            if t_coverage_fontcolor == '':
                if t_coverage_color == 'cyan':
                    t_coverage_color = hex2color('#00e0e0')
                t_coverage_fontcolor = t_coverage_color
            # find anchor point
            #t_anchor_radec = FitsImageWCS.wcs_pix2world(long(FitsImageHeader['NAXIS1'])-1, long(FitsImageHeader['NAXIS2'])-1, 1) # 3rd arg: origin is the coordinate in the upper left corner of the image. In FITS and Fortran standards, this is 1. In Numpy and C standards this is 0.
            #t_anchor_point = find_closest_data_point(t_polygon_points, t_anchor_radec)
            t_corner_point = (long(FitsImageHeader['NAXIS1'])-1, long(FitsImageHeader['NAXIS2'])-1)
            t_anchor_point = find_closest_data_point(t_polygon_points, t_corner_point)
            # plot a polygon
            PlotShape = Polygon(t_polygon_points, closed=True, edgecolor=t_coverage_linecolor, facecolor="none", alpha=t_coverage_transparency, linewidth=t_coverage_linewidth, linestyle=t_coverage_linestyle, zorder=5)
            PlotPanel.add_artist(PlotShape)
            #pyplot.draw()
            #pyplot.pause(0.05)
            fp.close()
            # 
            # draw annotation text
            #posxy = FitsImageWCS.wcs_world2pix(149.78583, 1.505, 1) # 3rd arg: origin is the coordinate in the upper left corner of the image. In FITS and Fortran standards, this is 1. In Numpy and C standards this is 0.
            posxy = t_anchor_point
            print("Plotting Annotation at %.3f %.3f (%s)"%(posxy[0], posxy[1], InputPolygonFile))
            pyplot.text(posxy[0], posxy[1], t_coverage_name, color=t_coverage_fontcolor, fontsize=t_coverage_fontsize, horizontalalignment='center', verticalalignment='bottom')
            pyplot.draw()
            pyplot.pause(0.05)












# 
# Make the image zoomable
zp = ZoomPan()
figScale = 1.05
figZoom = zp.zoom_factory(PlotPanel, base_scale=figScale)
figPan = zp.pan_factory(PlotPanel)
PlotDevice.savefig('alma_sky_coverage.pdf', dpi=300)
print("Written to alma_sky_coverage.pdf!")
print("Done!")
#pyplot.show()










        