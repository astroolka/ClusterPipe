"""
This file contains parser to ctools for scripts related
to imaging.
"""

#==================================================
# Imports
#==================================================

import ctools
import cscripts
import numpy as np

#==================================================
# Sky maps
#==================================================

def skymap(inobs, outmap,
           npix, reso, cra, cdec,
           emin=1e-2,
           emax=1e+3,
           caldb=None,
           irf=None,
           bkgsubtract='NONE',
           roiradius=0.1,
           inradius=1.0,
           outradius=2.0,
           iterations=3,
           threshold=3,
           logfile=None,
           silent=False):
    """
    Compute sky map.
    See http://cta.irap.omp.eu/ctools/users/reference_manual/ctskymap.html

    Parameters
    ----------
    - inobs (str): input Event file or xml listing event file
    - outmap (str): full path to fits skymap
    - npix (int): number of pixels
    - reso(float): map resolution in deg
    - cra,cdec (float): map RA,Dec center in deg
    - emin,emax (float) min and max energy considered in TeV
    - caldb (str): calibration database
    - irf (str): instrument response function
    - bkgsubtract (str): 'NONE', 'IRF', or 'RING' method for 
    background subtraction
    - roiradius (float): for each pixel, radius around which on region is considered
    - inradius (float): inner radius for ring off region
    - outradius (float): outer radius for ring off region
    - iterations (int): number of iteration for flagging source regions
    - threshold (float): S/N threshold for flagging source region
    - silent (bool): print information or not

    Outputs
    --------
    - create sky map fits

    """
    
    smap = ctools.ctskymap()    

    smap['inobs']    = inobs
    if caldb is not None: smap['caldb'] = caldb
    if irf   is not None: smap['irf']   = irf
    smap['inmap']    = 'NONE'
    smap['outmap']   = outmap
    smap['emin']     = emin
    smap['emax']     = emax
    smap['usepnt']   = False
    smap['nxpix']    = npix
    smap['nypix']    = npix
    smap['binsz']    = reso
    smap['coordsys'] = 'CEL'
    smap['proj']     = 'TAN'
    smap['xref']     = cra
    smap['yref']     = cdec
    
    smap['bkgsubtract'] = bkgsubtract
    smap['roiradius']   = roiradius
    smap['inradius']    = inradius
    smap['outradius']   = outradius
    smap['iterations']  = iterations
    smap['threshold']   = threshold
    smap['inexclusion'] = 'NONE'
    smap['usefft']      = True
    if logfile is not None: smap['logfile'] = logfile

    if logfile is not None: smap.logFileOpen()
    smap.execute()
    if logfile is not None: smap.logFileClose()

    if not silent:
        print(smap)
        print('')

    return smap


#==================================================
# Source detect maps
#==================================================

def src_detect(inskymap, outmodel, outds9file,
               threshold=5.0,
               maxsrcs=20,
               avgrad=1.0,
               corr_rad=0.2,
               exclrad=0.2,
               logfile=None,
               silent=False):
    """
    Detect sources from a map
    See http://cta.irap.omp.eu/ctools/users/reference_manual/cssrcdetect.html

    Parameters
    ----------
    - inskymap (str): input skymap file
    - outmodel (str): output xml model filename
    - outds9file (str): output ds9 region filename
    - threshold (float): treshold (sigma gaussian) for detection
    - maxsrcs (int): maximum number of sources
    - avgrad (float): averaging radius for significance computation (degrees)
    - corr_rad (float): correlation kernel (deg)
    - exclrad (float): Radius around a detected source that is excluded 
    from further source detection (degrees).
    - silent (bool): print information or not

    Outputs
    --------
    - Write xml model file
    - Write a DS9 region file
    """
    
    srcdet = cscripts.cssrcdetect()    

    
    srcdet['inmap']      = inskymap
    srcdet['outmodel']   = outmodel
    srcdet['outds9file'] = outds9file
    srcdet['srcmodel']   = 'POINT'   # For the moment, only point source + power law
    srcdet['bkgmodel']   = 'NONE'    # NONE|IRF|AEFF|CUBE|RACC
    srcdet['threshold']  = threshold
    srcdet['maxsrcs']    = maxsrcs
    srcdet['avgrad']     = avgrad
    srcdet['corr_rad']   = corr_rad
    srcdet['corr_kern']  = 'GAUSSIAN' #<NONE|DISK|GAUSSIAN>
    srcdet['exclrad']    = exclrad
    srcdet['fit_pos']    = True
    srcdet['fit_shape']  = True
    if logfile is not None: srcdet['logfile'] = logfile

    if logfile is not None: srcdet.logFileOpen()
    srcdet.execute()
    if logfile is not None: srcdet.logFileClose()
    
    if not silent:
        print(srcdet)
        print('')

    return srcdet


#==================================================
# TS map
#==================================================

def tsmap(inobs, inmodel, outmap, srcname,
          npix, reso, cra, cdec,
          expcube=None, 
          psfcube=None,
          bkgcube=None,
          edispcube=None,
          caldb=None,
          irf=None,
          edisp=False,
          statistic='DEFAULT',
          like_accuracy=0.005,
          max_iter=50,
          logfile=None,
          silent=False):
    """
    Compute TS map.
    http://cta.irap.omp.eu/ctools/users/reference_manual/cttsmap.html

    Parameters
    ----------
    - inobs (string): input observation file
    - inmodel (string): input model
    - outmap (string): output map file
    - srcname (string): name of the source to consider
    - npix (int): number of map pixel
    - reso (float): map resolution in degrees
    - cra, cdec (float): map center RA,Dec in degrees
    - expcube (string): exposure map cube
    - psfcube (string): psfcube 
    - bkgcube (string): background cube
    - edispcube (string): energy dispersion cube
    - caldb (string): calibration database
    - irf (string): instrument response function
    - edisp (bool): apply energy dispersion
    - statistic (string): which statistic to use
    - like_accuracy (float): likelihood accuracy
    - max_iter (int): maximum number of iteration
    - silent (bool): print information or not
    Outputs
    --------
    - create TS map fits
    - return a TS map object
    """

    ts_map = ctools.cttsmap()
    
    ts_map['inobs']         = inobs
    ts_map['inmodel']       = inmodel
    ts_map['srcname']       = srcname
    if expcube   is not None: ts_map['expcube']   = expcube
    if psfcube   is not None: ts_map['psfcube']   = psfcube
    if edispcube is not None: ts_map['edispcube'] = edispcube
    if bkgcube   is not None: ts_map['bkgcube']   = bkgcube
    if caldb     is not None: ts_map['caldb']     = caldb
    if irf       is not None: ts_map['irf']       = irf
    ts_map['edisp']         = edisp
    ts_map['outmap']        = outmap
    ts_map['errors']        = False
    ts_map['statistic']     = statistic
    ts_map['like_accuracy'] = like_accuracy
    ts_map['max_iter']      = max_iter
    ts_map['usepnt']        = False
    ts_map['nxpix']         = npix
    ts_map['nypix']         = npix
    ts_map['binsz']         = reso
    ts_map['coordsys']      = 'CEL'
    ts_map['proj']          = 'TAN'
    ts_map['xref']          = cra
    ts_map['yref']          = cdec
    #ts_map['binmin']        = -1
    #ts_map['binmax']        = -1
    #ts_map['logL0']         = -1.0
    if logfile is not None: ts_map['logfile'] = logfile

    if logfile is not None: ts_map.logFileOpen()
    ts_map.execute()
    if logfile is not None: ts_map.logFileClose()
    
    if not silent:
        print(ts_map)
        print('')
        
    return ts_map


#==================================================
# Residual maps
#==================================================

def resmap(inobs, inmodel, output_map,
           npix, reso, cra, cdec,
           emin=1e-2, emax=1e+3, enumbins=20, ebinalg='LOG',
           modcube=None, 
           expcube=None, 
           psfcube=None,
           bkgcube=None,
           edispcube=None,
           caldb=None,
           irf=None,
           edisp=False,
           algo='SIGNIFICANCE',
           logfile=None,
           silent=False):
    """
    Compute a residual map.
    
    Parameters
    ----------
    - inobs (string): input observation file
    - inmodel (string): input model
    - output_map (string): output map file
    - npix (int): number of map pixel
    - reso (float): map resolution in degrees
    - cra, cdec (float): map center RA,Dec in degrees
    - emin,emax (float) min and max energy considered in TeV
    - enumbins (int): number of energy bins
    - ebinalg (string): energy bining algorithm
    - modcube (string): model map cube
    - expcube (string): exposure map cube
    - psfcube (string): psfcube 
    - bkgcube (string): background cube
    - edispcube (string): energy dispersion cube
    - caldb (string): calibration database
    - irf (string): instrument response function
    - edisp (bool): apply energy dispersion
    - algo (string): wich algorithm to use
    - silent (bool): print information or not

    Outputs
    --------
    - create residual map fits
    - return a residual map object
    """

    rmap = cscripts.csresmap()
    
    rmap['inobs']     = inobs
    rmap['inmodel']   = inmodel
    if modcube   is not None: rmap['modcube']   = modcube
    if expcube   is not None: rmap['expcube']   = expcube
    if psfcube   is not None: rmap['psfcube']   = psfcube
    if edispcube is not None: rmap['edispcube'] = edispcube
    if bkgcube   is not None: rmap['bkgcube']   = bkgcube
    if caldb     is not None: rmap['caldb']     = caldb
    if irf       is not None: rmap['irf']       = irf
    rmap['edisp']     = edisp
    rmap['outmap']    = output_map
    rmap['ebinalg']   = ebinalg
    rmap['emin']      = emin   
    rmap['emax']      = emax
    rmap['enumbins']  = enumbins
    rmap['ebinfile']  = 'NONE'
    rmap['coordsys']  = 'CEL'
    rmap['proj']      = 'TAN'
    rmap['xref']      = cra
    rmap['yref']      = cdec
    rmap['nxpix']     = npix
    rmap['nypix']     = npix
    rmap['binsz']     = reso
    rmap['algorithm'] = algo
    if logfile is not None: rmap['logfile'] = logfile

    if logfile is not None: rmap.logFileOpen()
    rmap.execute()
    if logfile is not None: rmap.logFileClose()
    
    if not silent:
        print(rmap)
        print('')
    
    return rmap

