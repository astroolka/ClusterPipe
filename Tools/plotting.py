"""
This file contains general plotting tools in common 
with Ana and Sim modules.

"""

#==================================================
# Requested imports
#==================================================

import os
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.pylab as pl
from matplotlib.colors import SymLogNorm
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS
import numpy as np
from scipy import interpolate
import scipy.ndimage as ndimage
import random

from ClusterPipe.Tools import plotting_irf
from ClusterPipe.Tools import plotting_obsfile

import gammalib

#==================================================
# Style
#==================================================

cta_energy_range   = [0.02, 100.0]*u.TeV
fermi_energy_range = [0.1, 300.0]*u.GeV

def set_default_plot_param():
    
    dict_base = {'font.size':        16, 
                 'legend.fontsize':  16,
                 'xtick.labelsize':  16,
                 'ytick.labelsize':  16,
                 'axes.labelsize':   16,
                 'axes.titlesize':   16,
                 'figure.titlesize': 16,
                 'figure.figsize':[8.0, 6.0],
                 'figure.subplot.right':0.97,
                 'figure.subplot.left':0.18, # Ensure enough space on the left so that all plot can be aligned
                 'font.family':'serif',
                 'figure.facecolor': 'white',
                 'legend.frameon': True}

    plt.rcParams.update(dict_base)
    
    
#==================================================
# Get the CTA PSF given the IRF
#==================================================

def get_cta_psf(caldb, irf, emin, emax, w8_slope=-2):
    """
    Return the on-axis maximum PSF between emin and emax.

    Parameters
    ----------
    - caldb (str): the calibration database
    - irf (str): input response function
    - emin (float): the minimum energy considered (TeV)
    - emax (float): the maximum energy considered (TeV)
    - w8_slope (float): spectral slope assumed to weight 
    the PSF when extracting the mean

    Outputs
    --------
    - PSF (FWHM, deg): on axis point spread function
    """

    CTOOLS_dir = os.getenv('CTOOLS')

    data_file = CTOOLS_dir+'/share/caldb/data/cta/'+caldb+'/bcf/'+irf+'/irf_file.fits'
    hdul = fits.open(data_file)
    data_PSF = hdul[2].data
    hdul.close()

    theta_mean = (data_PSF['THETA_LO'][0,:]+data_PSF['THETA_HI'][0,:])/2.0
    eng_mean = (data_PSF['ENERG_LO'][0,:]+data_PSF['ENERG_HI'][0,:])/2.0
    PSF_E = data_PSF['SIGMA_1'][0,0,:] # This is on axis
    
    fitpl  = interpolate.interp1d(eng_mean, PSF_E, kind='cubic')
    e_itpl = np.logspace(np.log10(emin), np.log10(emax), 1000)
    PSF_itpl = fitpl(e_itpl)
    PSF_itpl = PSF_itpl * 2*np.sqrt(2*np.log(2)) # Convert to FWHM
                     
    weng = (e_itpl > emin) * (e_itpl < emax)

    PSF = np.sum(PSF_itpl[weng] * e_itpl[weng]**w8_slope) / np.sum(e_itpl[weng]**w8_slope)
    
    return PSF


#==================================================
#Show the IRF
#==================================================

def show_irf(caldb_in, irf_in, plotfile,
             emin=None, emax=None,
             tmin=None, tmax=None):
    """
    Show the IRF by calling the ctools function

    Parameters
    ----------
    - caldb_in (str list): the calibration database
    - irf_in (str list): input response function
    - emin (min energy): minimal energy in TeV
    - emax (max energy): maximal energy in TeV
    - tmin (min energy): minimal angle in deg
    - tmax (max energy): maximal angle in deg

    """

    set_default_plot_param()

    # Select all the unique IRF
    list_use  = []
    caldb_use = []
    irf_use   = []
    for i in range(len(caldb_in)):
        if caldb_in[i] + irf_in[i] not in list_use:
            list_use.append(caldb_in[i] + irf_in[i])
            caldb_use.append(caldb_in[i])
            irf_use.append(irf_in[i])

    # ----- Loop over all caldb+irf used
    for i in range(len(caldb_use)):
           
        # Convert to gammalib format
        caldb = gammalib.GCaldb('cta', caldb_use[i])
        irf   = gammalib.GCTAResponseIrf(irf_use[i], caldb)

        # Build selection string
        selection  = ''
        eselection = ''
        tselection = ''
        if emin != None and emax != None:
            eselection += '%.3f-%.1f TeV' % (emin, emax)
        elif emin != None:
            eselection += ' >%.3f TeV' % (emin)
        elif emax != None:
            eselection += ' <%.1f TeV' % (emax)
        if tmin != None and tmax != None:
            tselection += '%.1f-%.1f deg' % (tmin, tmax)
        elif tmin != None:
            tselection += ' >%.1f deg' % (tmin)
        elif tmax != None:
            tselection += ' <%.1f deg' % (tmax)
        if len(eselection) > 0 and len(tselection) > 0:
            selection = ' (%s, %s)' % (eselection, tselection)
        elif len(eselection) > 0:
            selection = ' (%s)' % (eselection)
        elif len(tselection) > 0:
            selection = ' (%s)' % (tselection)

        # Build title
        mission    = irf.caldb().mission()
        instrument = irf.caldb().instrument()
        response   = irf.rspname()
        title      = '%s "%s" Instrument Response Function "%s"%s' % \
            (gammalib.toupper(mission), instrument, response, selection)

        # Create figure
        fig = plt.figure(figsize=(16,12))
        
        # Add title
        fig.suptitle(title, fontsize=16)
        
        # Plot Aeff
        ax1 = fig.add_subplot(231)
        plotting_irf.plot_aeff(ax1, irf.aeff(), emin=emin, emax=emax, tmin=tmin, tmax=tmax)
        
        # Plot Psf
        ax2 = fig.add_subplot(232)
        plotting_irf.plot_psf(ax2, irf.psf(), emin=emin, emax=emax, tmin=tmin, tmax=tmax)
        
        # Plot Background
        ax3 = fig.add_subplot(233)
        plotting_irf.plot_bkg(ax3, irf.background(), emin=emin, emax=emax, tmin=tmin, tmax=tmax)
        
        # Plot Edisp
        fig.add_subplot(234)
        plotting_irf.plot_edisp(irf.edisp(), emin=emin, emax=emax, tmin=tmin, tmax=tmax)
        
        # Show plots or save it into file
        plt.savefig(plotfile+'_'+list_use[i]+'.png')
        plt.close()

    return


#==================================================
# Show map
#==================================================

def show_map(mapfile, outfile,
             smoothing_FWHM=0.0*u.deg,
             cluster_ra=None,
             cluster_dec=None,
             cluster_t500=None,
             cluster_name='',
             ps_name=[],
             ps_ra=[],
             ps_dec=[],
             ptg_ra=None,
             ptg_dec=None,
             PSF=None,
             maptitle='',
             bartitle='',
             rangevalue=[None, None],
             logscale=True,
             significance=False,
             cmap='magma'):
    """
    Plot maps to show.

    Parameters
    ----------
    Mandatory parameters:
    - mapfile (str): the map fits file to use
    - outfile (str): the ooutput plot file

    Optional parameters:
    - smoothing_FWHM (angle unit): FWHM used for smoothing
    - cluster_ra,dec (deg) : the center of the cluster in RA Dec
    - cluster_t500 (deg): cluster theta 500
    - cluster_name (str): name of the cluster
    - ps_name (str list): list of point source names
    - ps_ra,dec (deg list): list of point source RA and Dec
    - ptg_ra,dec (deg): pointing RA, Dec
    - PSF (deg): the PSF FWHM in deg
    - maptitle (str): title
    - bartitle (str): title of the colorbar
    - rangevalue (float list): range of teh colorbar
    - logscale (bool): apply log color bar
    - significance (bool): is this a significance map?
    - cmap (str): colormap

    Outputs
    --------
    - validation plot map
    """

    set_default_plot_param()

    #---------- Read the data
    data = fits.open(mapfile)[0]
    image = data.data
    wcs_map = WCS(data.header)
    reso = abs(wcs_map.wcs.cdelt[0])
    Npixx = image.shape[0]
    Npixy = image.shape[1]
    fov_x = Npixx * reso
    fov_y = Npixy * reso
            
    #---------- Smoothing
    sigma_sm = (smoothing_FWHM/(2*np.sqrt(2*np.log(2)))).to_value('deg')/reso
    image = ndimage.gaussian_filter(image, sigma=sigma_sm)

    if significance:
        norm = 2*sigma_sm*np.sqrt(np.pi) # Mean noise reduction when smoothing, assuming gaussian non correlated noise
        image *= norm
        print('WARNING: The significance is boosted accounting for smoothing.')
        print('         This assumes weak noise spatial variarion (w.r.t. smoothing), gaussian regime, and uncorrelated pixels.')
        
    #--------- map range
    if rangevalue[0] is None:
        vmin = np.amin(image)
    else:
        vmin = rangevalue[0]

    if rangevalue[1] is None:
        vmax = np.amax(image)
    else:
        vmax = rangevalue[1]
        
    #---------- Plot
    if not ((np.amax(image) == 0) and (np.amin(image) == 0)) :
        fig = plt.figure(1, figsize=(12, 12))
        ax = plt.subplot(111, projection=wcs_map)

        if logscale :
            plt.imshow(image, origin='lower', cmap=cmap, norm=SymLogNorm(1), vmin=vmin, vmax=vmax)
        else:
            plt.imshow(image, origin='lower', cmap=cmap, vmin=vmin, vmax=vmax)
            
        # Show cluster t500
        if (cluster_t500 is not None) * (cluster_ra is not None) * (cluster_dec is not None) :
            circle_rad = 2*cluster_t500/np.cos(cluster_dec*np.pi/180)
            circle_500 = matplotlib.patches.Ellipse((cluster_ra, cluster_dec),
                                                    circle_rad,
                                                    2*cluster_t500,
                                                    linewidth=2, fill=False, zorder=2,
                                                    edgecolor='lightgray', linestyle='dashed',
                                                    facecolor='none',
                                                    transform=ax.get_transform('fk5'))
            ax.add_patch(circle_500)
            txt_r500 = plt.text(cluster_ra - cluster_t500, cluster_dec - cluster_t500,
                                '$R_{500}$',
                                transform=ax.get_transform('fk5'), fontsize=10,
                                color='lightgray',
                                horizontalalignment='center',verticalalignment='center')

        # Show the pointing
        if (ptg_ra is not None) * (ptg_dec is not None) :
            ax.scatter(ptg_ra, ptg_dec,
                       transform=ax.get_transform('icrs'), color='white', marker='x', s=100)

            try:
                txt_ptg = plt.text(ptg_ra, ptg_dec+0.2, 'Pointing',
                                   transform=ax.get_transform('fk5'),fontsize=10,
                                   color='white', horizontalalignment='center',
                                   verticalalignment='center')
            except:
                txt_ptg = plt.text(ptg_ra[0], ptg_dec[0]+0.2, 'Pointings',
                                   transform=ax.get_transform('fk5'),fontsize=10,
                                   color='white', horizontalalignment='center',
                                   verticalalignment='center')

                
        # Show the cluster center
        if (cluster_ra is not None) * (cluster_dec is not None) :
            ax.scatter(cluster_ra, cluster_dec,
                       transform=ax.get_transform('icrs'), color='cyan', marker='x', s=100)
            txt_clust = plt.text(cluster_ra, cluster_dec-0.2, cluster_name,
                             transform=ax.get_transform('fk5'), fontsize=10,
                             color='cyan', horizontalalignment='center',
                             verticalalignment='center')

        # Show the point sources
        for i in range(len(ps_name)): 
            if (ps_ra[i] is not None) * (ps_dec[i] is not None) :
                ax.scatter(ps_ra[i], ps_dec[i],
                           transform=ax.get_transform('icrs'), s=200, marker='o',
                           facecolors='none', edgecolors='green')
                txt_ps = plt.text(ps_ra[i]-0.1, ps_dec[i]+0.1, ps_name[i],
                                  transform=ax.get_transform('fk5'),fontsize=10, color='green')
                
        # Show the PSF
        if PSF is not None:
            dec_mean_cor = np.cos((wcs_map.wcs.crval[1]-(wcs_map.wcs.crpix*wcs_map.wcs.cdelt)[1]+0.3) * np.pi/180.0)
            circle_ra = wcs_map.wcs.crval[0]-(wcs_map.wcs.crpix*wcs_map.wcs.cdelt)[0]/dec_mean_cor-0.3
            circle_dec = wcs_map.wcs.crval[1]-(wcs_map.wcs.crpix*wcs_map.wcs.cdelt)[1]+0.3
            circle_PSF = matplotlib.patches.Ellipse((circle_ra, circle_dec),
                                                    PSF/dec_mean_cor, PSF,
                                                    angle=0, linewidth=1, fill=True,
                                                    zorder=2, facecolor='lightgray',
                                                    edgecolor='white',
                                                    transform=ax.get_transform('fk5'))
            txt_ra  = wcs_map.wcs.crval[0]-(wcs_map.wcs.crpix*wcs_map.wcs.cdelt)[0]/dec_mean_cor-0.6
            txt_dec = wcs_map.wcs.crval[1]-(wcs_map.wcs.crpix*wcs_map.wcs.cdelt)[1]+0.3
            txt_psf = plt.text(txt_ra, txt_dec, 'PSF',
                               transform=ax.get_transform('fk5'), fontsize=12,
                               color='white',  verticalalignment='center')
            ax.add_patch(circle_PSF)

        # Formating and end
        ax.set_xlabel('R.A. (deg)')
        ax.set_ylabel('Dec (deg)')
        ax.set_title(maptitle)
        cbar = plt.colorbar()
        cbar.set_label(bartitle)
        fig.savefig(outfile, bbox_inches='tight')
        plt.close()

    else :
        print('!!!!!!!!!! WARNING: empty map, '+str(outfile)+' was not created')
        

#==================================================
# Show map
#==================================================

def show_profile(proffile, outfile,
                 theta500=None,
                 logscale=True):
    """
    Plot the profile to show.

    Parameters
    ----------
    Mandatory parameters:
    - mapfile (str): the map fits file to use
    - outfile (str): the ooutput plot file
    - cluster_t500 (deg): cluster theta 500

    Outputs
    --------
    - validation plot profile
    """

    set_default_plot_param()

    #---------- Read the data
    data = fits.open(proffile)[1]
    prof = data.data
    r_unit = data.columns['radius'].unit
    p_unit = data.columns['profile'].unit
    
    #---------- Plot
    fig, ax1 = plt.subplots()
    ax1.set_xlabel('Radius ('+str(r_unit)+')', color='k')
    ax1.set_ylabel('Profile ('+str(p_unit)+')', color='k')

    if logscale:
        ax1.set_xscale('log')
        ax1.set_yscale('log')
        w_pos = prof['profile'] > 0
        w_neg = prof['profile'] < 0
        ax1.errorbar(prof['radius'][w_pos], prof['profile'][w_pos], yerr=prof['error'][w_pos],
                     color='blue',marker='o',linestyle='', label='values > 0')
        ax1.errorbar(prof['radius'][w_neg], -prof['profile'][w_neg], yerr=prof['error'][w_neg],
                     color='orange',marker='.',linestyle='', label='values < 0')
        ax1.set_xlim(np.amin(prof['radius'])*0.5, np.amax(prof['radius']))
    else:
        ax1.errorbar(prof['radius'], prof['profile'], yerr=prof['error'], color='blue',marker='o',linestyle='')
        ax1.set_xlim(0, np.amax(prof['radius']))
        
    if theta500 is not None:
        ax1.axvline(theta500.to_value(r_unit), ymin=1e-300, ymax=1e300,
                    color='black', label='$\\theta_{500}$', linestyle='--')
    ax1.legend()
    fig.savefig(outfile)
    plt.close()

    
#==================================================
# Quicklook of the event
#==================================================

def events_quicklook(evfile, outfile):
    """
    Basic plots directly made from the event file.

    Parameters
    ----------
    - evfile: event file name
    - outfile : output filename

    Outputs
    --------
    - event vizualisation plot
    """

    set_default_plot_param()
    
    events_hdu = fits.open(evfile)

    try:
        events_data1 = events_hdu[1].data
        events_data2 = events_hdu[2].data
        
        events_hdr0 = fits.getheader(evfile, 0)  # get default HDU (=0), i.e. primary HDU's header
        events_hdr1 = fits.getheader(evfile, 1)  # get primary HDU's header
        events_hdr2 = fits.getheader(evfile, 2)  # the second extension
        
        events_hdu.close()

        fig = plt.figure(1, figsize=(18, 14))
        
        # Plot the photon counts in RA-Dec
        Npt_plot = 1e5
        if len(events_data1) > Npt_plot:
            w = np.random.uniform(0,1,size=len(events_data1)) < Npt_plot/len(events_data1)
            events_data1_reduce = events_data1[w]
        else :
            events_data1_reduce = events_data1
        
        plt.subplot(221)
        plt.plot(events_data1_reduce['RA'], events_data1_reduce['DEC'], 'ko', ms=0.4, alpha=0.2)
        plt.xlim(np.amax(events_data1_reduce['RA']), np.amin(events_data1_reduce['RA']))
        plt.ylim(np.amin(events_data1_reduce['DEC']), np.amax(events_data1_reduce['DEC']))
        plt.xlabel('RA (deg)')
        plt.ylabel('Dec (deg)')
        plt.title('Photon coordinate map')
        plt.axis('scaled')
        
        # Energy histogram
        plt.subplot(222)
        plt.hist(np.log10(events_data1['ENERGY']), bins=50, color='black', log=True, alpha=0.3)
        plt.xlabel('log E/TeV')
        plt.ylabel('Photon counts')
        plt.title('Photon energy histogram')
        
        # Time counts histogram
        plt.subplot(223)
        plt.hist((events_data1['TIME'] - np.amin(events_data1['TIME']))/3600.0, bins=200, log=False, color='black', alpha=0.3)
        plt.xlabel('Time (h)')
        plt.ylabel('Photon counts')
        plt.title('Photon time histogram')
        
        # Information
        plt.subplot(224)
        i1 = 'ObsID: '+events_hdr1['OBS_ID']
        i2 = 'Date obs: '+events_hdr1['DATE-OBS']+'-'+events_hdr1['TIME-OBS']
        i3 = 'Date end: '+events_hdr1['DATE-END']+'-'+events_hdr1['TIME-END']
        i4 = 'Live time: '+str(events_hdr1['LIVETIME'])+' '+events_hdr1['TIMEUNIT']
        t1 = 'Number of events: \n..... '+str(len(events_data1))
        t2 = 'Median energy: \n..... '+str(np.median(events_data1['ENERGY']))+events_hdr1['EUNIT']
        t3 = 'Median R.A.,Dec.: \n..... '+str(np.median(events_data1_reduce['RA']))+' deg \n..... '+str(np.median(events_data1_reduce['DEC']))+' deg'
        plt.text(0.1, 0.85, i1, ha='left', rotation=0, wrap=True)
        plt.text(0.1, 0.80, i2, ha='left', rotation=0, wrap=True)
        plt.text(0.1, 0.75, i3, ha='left', rotation=0, wrap=True)
        plt.text(0.1, 0.70, i4, ha='left', rotation=0, wrap=True)

        plt.text(0.1, 0.55, t1, ha='left', rotation=0, wrap=True)
        plt.text(0.1, 0.40, t2, ha='left', rotation=0, wrap=True)
        plt.text(0.1, 0.20, t3, ha='left', rotation=0, wrap=True)
        plt.axis('off')
        
        fig.savefig(outfile, bbox_inches='tight', dpi=200)
        plt.close()
        
    except:
        print('')
        print('!!!!! Could not apply events_quicklook. Event file may be empty !!!!!')

        
#==================================================
# Get the pointing patern from a file
#==================================================

def get_pointings(filename):
    """
    Extract pointings from XML file

    Parameters
    ----------
    filename : str
        File name of observation definition XML file

    Returns
    -------
    pnt : list of dict
        Pointings
    """
    # Initialise pointings
    pnt = []

    # Open XML file
    xml = gammalib.GXml(filename)

    # Get observation list
    obs = xml.element('observation_list')

    # Get number of observations
    nobs = obs.elements('observation')

    # Loop over observations
    for i in range(nobs):

        # Get observation
        run = obs.element('observation', i)

        # Get pointing parameter
        npars   = run.elements('parameter')
        ra      = None
        dec     = None
        roi_ra  = None
        roi_dec = None
        roi_rad = None
        evfile  = None
        obsid   = run.attribute('id')
        for k in range(npars):
            par = run.element('parameter', k)
            if par.attribute('name') == 'Pointing':
                ra  = float(par.attribute('ra'))
                dec = float(par.attribute('dec'))
            elif par.attribute('name') == 'RegionOfInterest':
                roi_ra  = float(par.attribute('ra'))
                roi_dec = float(par.attribute('dec'))
                roi_rad = float(par.attribute('rad'))
            elif par.attribute('name') == 'EventList':
                evfile = par.attribute('file')

        # Add valid pointing
        if ra != None:
            p   = gammalib.GSkyDir()
            p.radec_deg(ra, dec)
            entry = {'l': p.l_deg(), 'b': p.b_deg(),
                     'ra': ra, 'dec': dec,
                     'roi_ra': roi_ra, 'roi_dec': roi_dec, 'roi_rad': roi_rad,
                     'evfile': evfile, 'obsid':obsid}
            pnt.append(entry)

    return pnt


#==================================================
# Plot the pointings
#==================================================

def show_pointings(xml_file, plotfile):
    """
    Plot information

    Parameters
    ----------
    - xml_file (str) : Observation definition xml file
    - plotfile (str): Plot filename
    """

    set_default_plot_param()

    pnt = get_pointings(xml_file)
    
    # Create figure
    plt.figure()
    fig = plt.figure(1, figsize=(20, 20))
    ax  = plt.subplot(111)
    colors = pl.cm.jet(np.linspace(0,1,len(pnt)))

    # Loop over pointings
    xmin = []
    xmax = []
    ymin = []
    ymax = []
    i = 0
    for p in pnt:
        ra  = p['ra']
        dec = p['dec']
        roi_ra  = p['roi_ra']
        roi_dec = p['roi_dec']
        roi_rad = p['roi_rad']
        obsid   = p['obsid']

        #color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
        color = colors[i]
        
        ax.scatter(ra, dec, s=150, marker='x', color=color)
        circle = matplotlib.patches.Ellipse(xy=(roi_ra, roi_dec),
                                            width=2*roi_rad/np.cos(dec*np.pi/180),
                                            height=2*roi_rad,
                                            alpha=0.1,
                                            linewidth=1,
                                            color=color,
                                            edgecolor=color, label='ObsID'+obsid)
        ax.add_patch(circle)
        
        xmin.append(roi_ra-roi_rad/np.cos(dec*np.pi/180))
        xmax.append(roi_ra+roi_rad/np.cos(dec*np.pi/180))
        ymin.append(roi_dec-roi_rad)
        ymax.append(roi_dec+roi_rad)
        i += 1

    xctr = (np.amax(xmax) + np.amin(xmin)) / 2.0
    yctr = (np.amax(ymax) + np.amin(ymin)) / 2.0
    fovx = (np.amax(xmax) - np.amin(xmin))*1.1/np.cos(yctr*np.pi/180)
    fovy = (np.amax(ymax) - np.amin(ymin))*1.1
        
    plt.xlim(xctr-fovx/2, xctr+fovx/2)
    plt.ylim(yctr-fovy/2, yctr+fovy/2)
    plt.legend()
        
    # Plot title and labels
    plt.xlabel('R.A. (deg)')
    plt.ylabel('Dec. (deg)')

    # Show plots or save it into file
    plt.savefig(plotfile)
    plt.close()

    return


#==================================================
# Plot the pointings
#==================================================

def show_obsdef(xml_file, coord, plotfile):
    """
    Plot information

    Parameters
    ----------
    - xml_file (str) : Observation definition xml file
    - coord (SkyCoord): coordinates of the target
    - plotfile (str): Plot filename
    """

    set_default_plot_param()
    info = plotting_obsfile.run_csobsinfo(xml_file,
                                          coord.icrs.ra.to_value('deg'),
                                          coord.icrs.dec.to_value('deg'))
    plotting_obsfile.plot_information(info,
                                      coord.icrs.ra.to_value('deg'),
                                      coord.icrs.dec.to_value('deg'),
                                      plotfile)
    
    return


#==================================================
# Plot the spectrum of sources
#==================================================

def show_model_spectrum(xml_file, plotfile,
                        emin=0.01, emax=100.0, enumbins=100):
    """
    Plot information

    Parameters
    ----------
    - xml_file (str) : Observation definition xml file
    - plotfile (str): Plot filename
    - emin (min energy): minimal energy in TeV
    - emax (max energy): maximal energy in TeV
    - enumbins (int): number of energy bins

    """

    set_default_plot_param()

    # Setup energy axis
    e_min   = gammalib.GEnergy(emin, 'TeV')
    e_max   = gammalib.GEnergy(emax, 'TeV')
    ebounds = gammalib.GEbounds(enumbins, e_min, e_max)

    # Read models XML file
    models = gammalib.GModels(xml_file)

    # Plot spectra in loop
    plt.figure(figsize=(12,8))
    plt.loglog()
    plt.grid()
    colors = pl.cm.jet(np.linspace(0,1,len(models)))
    
    for imod in range(len(models)):
        model = models[imod]
        if model.type() == 'DiffuseSource' or model.type() == 'PointSource':
            spectrum = model.spectral()
            # Setup lists of x and y values
            x   = []
            y   = []
            for i in range(enumbins):
                energy = ebounds.elogmean(i)
                value  = spectrum.eval(energy)
                x.append(energy.TeV())
                y.append(value)
            plt.loglog(x, y, linewidth=3, color=colors[imod], label=model.name()+' ('+spectrum.type()+')')

    plt.xlabel('Energy (TeV)')
    plt.ylabel(r'dN/dE (ph s$^{-1}$ cm$^{-2}$ MeV$^{-1}$)')
    plt.legend()
    plt.savefig(plotfile)
    plt.close()
    
    return
