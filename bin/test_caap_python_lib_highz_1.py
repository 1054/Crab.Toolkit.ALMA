#!/usr/bin/env python2.7
# 

from caap_python_lib_highz import *
from pprint import pprint

Cat = Highz_Catalogue('/Users/dzliu/Temp/20161226_COSMOS_ALMA_crossmatch/auto/run_cycle2_new/Match_cycle2_new_detections_1.5arcsec.fits')

print(Cat.ra(1))
print(Cat.ra_2(1))
print(Cat.ra([0,1,2]))
print(Cat.ra_2([0,1,2]))
#pprint(Cat.col(ColName=['NUMBER','ALPHA_J2000','DELTA_J2000','OBJECT','RA','DEC'], ColSelect=[4,5,6,1,2,4], RowSelect=[0,1,2,3], CheckExistence=True))
#pprint(Cat.col(ColName=['NUMBER','ALPHA_J2000','DELTA_J2000','OBJECT','RA2','DEC'], ColSelect=[4,5,6,1,2,3], RowSelect=[0,1,2,3], CheckExistence=True))
pprint(Cat.col(ColName=['NUMBER','ALPHA_J2000','DELTA_J2000','OBJECT','RA','DEC'], ColSelect=[4,5,6,1,2,3], RowSelect=[0,1,2,3], CheckExistence=True))




