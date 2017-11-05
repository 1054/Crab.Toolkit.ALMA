
### About PyBDSF ###

PyBDSF (or PyBDSM) is an astronomical image blob detection tool. See [http://www.astron.nl/citt/pybdsf](http://www.astron.nl/citt/pybdsf).



### How to compile PyBDSF ###

This is how we compile and install PyBDSF into our 'Crab.Toolkit.CAAP' directory. We use "--prefix" to specify the target directory. 

First, install necessary python package dependencies. 

```
pip-2.7 install --ignore-installed --prefix="$HOME/Cloud/Github/Crab.Toolkit.CAAP/bin/3rd_party/python_packages/" pyfits pywcs
```

Here we assume that you alread have 'numpy', 'scipy' in your python path. 

Before next step, if you have IRAF, remove "/PATH/TO/IRAF/iraf.macx.x86_64/" otherwise the f77.sh in the IRAF directory will cause error. 

Then, clone the PyBDSF code from github, then compile and install. 

```
git clone https://github.com/lofar-astron/PyBDSF.git
cd PyBDSF
rm -rf build/
brew install boost --with-python
brew install boost-python
export PYTHONPATH="$HOME/Cloud/Github/Crab.Toolkit.CAAP/bin/3rd_party/python_packages/lib/python2.7/site-packages"
python2.7 setup.py build_ext --inplace --include-dirs="/opt/local/include" --library-dirs="/opt/local/lib/gcc48:/opt/local/lib" install --prefix="$HOME/Cloud/Github/Crab.Toolkit.CAAP/bin/3rd_party/python_packages"
```

Then, we still need to copy some library files manually

```
cp bdsf/*.so        "/Users/dzliu/Cloud/Github/Crab.Toolkit.CAAP/bin/3rd_party/python_packages/lib/python2.7/site-packages/bdsf-1.8.12-py2.7-macosx-10.12-x86_64.egg/bdsf/"
cp bdsf/nat/*.so    "/Users/dzliu/Cloud/Github/Crab.Toolkit.CAAP/bin/3rd_party/python_packages/lib/python2.7/site-packages/bdsf-1.8.12-py2.7-macosx-10.12-x86_64.egg/bdsf/nat/"
```



### How to use PyBDSF ###

```python
import numpy
import scipy
import pybdsf

```


