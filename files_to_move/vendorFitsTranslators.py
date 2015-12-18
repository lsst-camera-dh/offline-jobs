import os
import glob
import subprocess
from collections import OrderedDict
import ConfigParser
import datetime
import scipy.constants
import pyfits
import lsst.eotest.sensor as sensorTest

planck = scipy.constants.h  # J-s
clight = scipy.constants.c  # m/s

class VendorFitsTranslator(object):
    """
    Translate vendor data to conform to LCA-10140.  Current
    implementations only perform minimal header changes to allow
    eotest to run.

    Valid test types, image types, and filename format are

    test_types: fe55 dark flat lambda trap sflat_nnn spot
    image_types: bias dark fe55 flat spot ppump
    filenames: <lsst_num>_<test_type>_<image_type>_<seqno>_<time_stamp>.fits
    """
    def __init__(self, lsst_num, rootdir, outputBaseDir):
        self.lsst_num = lsst_num
        self.rootdir = rootdir
        self.outputBaseDir = outputBaseDir
        self.outfiles = []
    def _infiles(self, x):
        return sorted(glob.glob(os.path.join(self.rootdir, x)))
    def _writeFile(self, hdulist, local_vars, verbose=True):
        outfile = "%(lsst_num)s_%(test_type)s_%(image_type)s_%(seqno)s_%(time_stamp)s.fits" % local_vars
        outdir = os.path.join(self.outputBaseDir, local_vars['test_type'],
                              local_vars['time_stamp'])
        try:
            os.makedirs(outdir)
        except OSError:
            pass
        outfile = os.path.join(outdir, outfile)
        if os.path.relpath(outfile) not in self.outfiles:
            if verbose:
                print "writing", outfile
            hdulist.writeto(outfile, checksum=True)
            self.outfiles.append(os.path.relpath(outfile))
    def _setAmpGeom(self, hdulist):
        detxsize = 8*hdulist[1].header['NAXIS1']
        detysize = 2*hdulist[1].header['NAXIS2']
        ampGeom = sensorTest.AmplifierGeometry(detxsize=detxsize,
                                               detysize=detysize)
        hdulist[0].header['DETSIZE'] = ampGeom.DETSIZE
        for hdu in range(1, 17):
            amp = hdulist[hdu].header['AMPNO']
            hdulist[hdu].header['DETSIZE'] = ampGeom[amp]['DETSIZE']
            hdulist[hdu].header['DATASEC'] = ampGeom[amp]['DATASEC']
            hdulist[hdu].header['DETSEC'] = ampGeom[amp]['DETSEC']
    def _processFiles(self, test_type, image_type, pattern, seqno_prefix=None,
                      time_stamp=None, verbose=True, skip_zero_exptime=False):
        my_pattern = os.path.join(self.rootdir, pattern)
        infiles = self._infiles(my_pattern)
        if verbose and not infiles:
            print
            print "WARNING:"
            print "No files found for TESTTYPE=%(test_type)s, IMGTYPE=%(image_type)s and file pattern %(my_pattern)s" % locals()
            print
        if time_stamp is None:
            time_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        for iframe, infile in enumerate(infiles):
            if verbose:
                print "processing", os.path.basename(infile)
            if (skip_zero_exptime and 
                pyfits.open(infile)[0].header['EXPTIME'] == 0):
                if verbose:
                    print "skipping zero exposure frame."
                continue
            seqno = '%03i' % iframe
            if seqno_prefix is not None:
                seqno = seqno_prefix + seqno
            self.translate(infile, test_type, image_type, seqno,
                           time_stamp=time_stamp, verbose=verbose)
        return time_stamp
    def lambda_scan(self, pattern, time_stamp=None, verbose=True,
                    monowl_keyword='MONOWL'):
        if time_stamp is None:
            time_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        wl = lambda x : pyfits.open(x)[0].header[monowl_keyword]
        infiles = self._infiles(pattern)
        for infile in infiles:
            if verbose:
                print "processing", os.path.basename(infile)
            seqno = "%04i" % int(wl(infile))
            self.translate(infile, 'lambda', 'flat', seqno,
                           time_stamp=time_stamp, verbose=verbose)
        return time_stamp
        
class ItlFitsTranslator(VendorFitsTranslator):
    """
    FITS Translator for ITL data.
    """
    def __init__(self, lsst_num, rootdir, outputBaseDir='.'):
        super(ItlFitsTranslator, self).__init__(lsst_num, rootdir,
                                                outputBaseDir)
        # Identify the directory containing the subdirectories with
        # the data for the various tests.
        my_rootdir = rootdir.rstrip('/') # remove any trailing slashes
        my_rootdir = subprocess.check_output('find %s/ -name superflat1 -print'
                                             % my_rootdir, shell=True)
        self.rootdir = os.path.split(my_rootdir)[0]
    def translate(self, infile, test_type, image_type, seqno, time_stamp=None,
                  verbose=True):
        try:
            hdulist = pyfits.open(infile)
        except IOError, eobj:
            print eobj
            print "skipping"
            return
        lsst_num = self.lsst_num
        hdulist[0].header['LSST_NUM'] = lsst_num
        hdulist[0].header['CCD_MANU'] = 'ITL'
        #hdulist[0].header['CCD_SERN'] = 
        hdulist[0].header['MONOWL'] = float(hdulist[0].header['MONOWL'])
        hdulist[0].header['TESTTYPE'] = test_type.upper()
        hdulist[0].header['IMGTYPE'] = image_type.upper()
        self._writeFile(hdulist, locals(), verbose=verbose)
    def fe55(self, pattern='fe55/*_fe55.*.fits', time_stamp=None,
             verbose=True):
        return self._processFiles('fe55', 'fe55', pattern,
                                  time_stamp=time_stamp, verbose=verbose,
                                  skip_zero_exptime=True)
    def bias(self, pattern='bias/*_bias.*.fits', time_stamp=None,
             verbose=True):
        return self._processFiles('fe55', 'bias', pattern,
                                  time_stamp=time_stamp, verbose=verbose)
    def dark(self, pattern='dark/*_dark.*.fits', time_stamp=None,
             verbose=True):
        return self._processFiles('dark', 'dark', pattern,
                                  time_stamp=time_stamp, verbose=verbose,
                                  skip_zero_exptime=True)
    def trap(self, pattern='pocketpump/*_pocketpump*.fits', time_stamp=None,
             verbose=True):
        if time_stamp is None:
            time_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        infiles = self._infiles(os.path.join(self.rootdir, pattern))
        image_type = lambda x : pyfits.open(x)[0].header['OBJECT']
        infiles = dict([(image_type(item), item) for item in infiles])
        self.translate(infiles['pocketpump first bias'], 'trap', 'bias', '000',
                       time_stamp=time_stamp, verbose=verbose)
        
        # Handle the various ways ITL specifies the pocket pumped
        # exposure in their data packages.
        try:
            self.translate(infiles['pocket pump'], 'trap', 'ppump', '000',
                           time_stamp=time_stamp, verbose=verbose)
        except KeyError:
            try:
                self.translate(infiles['pocketpumped flat'], 'trap', 'ppump', 
                               '000', time_stamp=time_stamp, verbose=verbose)
            except KeyError:
                self.translate(infiles['pocketpump flat'], 'trap', 'ppump', 
                               '000', time_stamp=time_stamp, verbose=verbose)

        self.translate(infiles['pocketpump second bias'], 'trap', 'bias', '001',
                       time_stamp=time_stamp, verbose=verbose)
        self.translate(infiles['pocket pump reference flat'],
                       'trap', 'flat', '000',
                       time_stamp=time_stamp, verbose=verbose)
        return time_stamp
    def sflat_500_high(self, pattern='superflat2/*_superflat.*.fits', 
                       time_stamp=None, verbose=True):
        return self._processFiles('sflat_500', 'flat', pattern,
                                  time_stamp=time_stamp, verbose=verbose,
                                  seqno_prefix='H')
    def sflat_500_low(self, pattern='superflat1/*_superflat.*.fits', 
                      time_stamp=None, verbose=True):
        return self._processFiles('sflat_500', 'flat', pattern,
                                  time_stamp=time_stamp, verbose=verbose,
                                  seqno_prefix='L')
    def spot(self, pattern='', time_stamp=None,
             verbose=True):
        raise NotImplemented("ITL spot dataset translation not implemented.")
    def linearity(self, pattern='linearity/*linearity.*.fits', time_stamp=None,
                  verbose=True):
        return self._processFiles('linearity', 'flat', pattern,
                                  time_stamp=time_stamp, verbose=verbose)
    def flat(self, pattern='ptc/*_ptc.*.fits', time_stamp=None,
             verbose=True):
        if time_stamp is None:
            time_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        exptime = lambda x : pyfits.open(x)[0].header['EXPTIME']
        infiles = self._infiles(pattern)
        # Group files by exposure time and therefore into pairs, presumably.
        groups = OrderedDict()
        for infile in infiles:
            my_exptime = exptime(infile)
            if not groups.has_key(my_exptime):
                groups[my_exptime] = []
            groups[my_exptime].append(infile)
        # Translate first two files in each exptime group as flat1 and flat2.
        for key, infiles in groups.items():
            if key == 0 or len(infiles) < 2:
                # Skip zero exposure frames and groups with only one frame.
                continue
            seqno = '%09.4f_flat1' % key
            self.translate(infiles[0], 'flat', 'flat', seqno,
                           time_stamp=time_stamp, verbose=verbose)
            seqno = '%09.4f_flat2' % key
            self.translate(infiles[1], 'flat', 'flat', seqno,
                           time_stamp=time_stamp, verbose=verbose)
        return time_stamp

    def lambda_scan(self, pattern='qe/*_qe.*.fits', time_stamp=None,
                    verbose=True):
        time_stamp = super(ItlFitsTranslator, self).lambda_scan(pattern,
                                                                time_stamp=time_stamp,
                                                                verbose=verbose)
        flux = self._compute_incident_flux()
        sensor_id = self.lsst_num
        command = 'find . -name %(sensor_id)s_lambda_flat*.fits -print' % locals()
        files = subprocess.check_output(command, shell=True).split()
        for item in files:
            fits_obj = pyfits.open(item)
            wl = int(fits_obj[0].header['MONOWL'])
            fits_obj[0].header['MONDIODE_ORIG'] = fits_obj[0].header['MONDIODE']
            fits_obj[0].header['MONDIODE'] = flux[wl]
            fits_obj.writeto(item, clobber=True)
        return time_stamp

    def _compute_incident_flux(self):
        #
        # Read in qe.txt file and compute the incident fluxes as a function
        # of wavelength.  In that file, there are two notes on computing
        # the flux at the sensor:
        #
        #    Note1 = Flux @ sensor is Flux*Throughput/CalScal
        #    Note2 = Flux is [photons/sec/mm^2@diode]
        #
        vendorDataDir = os.readlink('vendorData')
        command = 'find %(vendorDataDir)s/ -name qe.txt -print' % locals()
        qe_txt_file = subprocess.check_output(command, shell=True).split()[0]
        parser = ConfigParser.ConfigParser()
        parser.read(qe_txt_file)
        CalScale = float(dict(parser.items('Info'))['calscale'])
        data = parser.items('QE')
        flux_at_sensor = {}
        for key, value in data:
            if not key.startswith('qe'):
                continue
            tokens = value.split()
            wl = int(float(tokens[0])) # nm
            flux = float(tokens[4])    # photons/s/mm^2
            throughput = float(tokens[5])
            # Convert to nW/cm^2
            energy_per_photon = 1e9*planck*clight/(wl*1e-9)   # nJ
            mm2_per_cm2 = 100.
            lightpow = flux*energy_per_photon*mm2_per_cm2*throughput/CalScale
            flux_at_sensor[wl] = lightpow
        return flux_at_sensor

    def run_all(self):
        time_stamp = self.fe55()
        self.bias(time_stamp=time_stamp)
        self.dark()
        self.trap()
        time_stamp = self.sflat_500_high()
        self.sflat_500_low(time_stamp=time_stamp)
        #self.spot()
        self.flat()
        self.linearity()
        self.lambda_scan()

class e2vFitsTranslator(VendorFitsTranslator):
    """
    FITS Translator for e2v data based on their delta TRR package.
    """
    def __init__(self, lsst_num, rootdir, outputBaseDir='.'):
        super(e2vFitsTranslator, self).__init__(lsst_num, rootdir,
                                                outputBaseDir)
    def translate(self, infile, test_type, image_type, seqno, time_stamp=None,
                  verbose=True):
        try:
            hdulist = pyfits.open(infile)
        except IOError, eobj:
            print eobj
            print "skipping"
            return
        lsst_num = self.lsst_num
        exptime = hdulist[0].header['EXPOSURE']
        hdulist[0].header['LSST_NUM'] = lsst_num
        hdulist[0].header['CCD_MANU'] = 'E2V'
        hdulist[0].header['CCD_SERN'] = hdulist[0].header['DEV_ID']
        hdulist[0].header['EXPTIME'] = exptime
        hdulist[0].header['MONOWL'] = hdulist[0].header['WAVELEN']
        if hdulist[0].header['LIGHTPOW'] != 0:
            hdulist[0].header['MONDIODE'] = hdulist[0].header['LIGHTPOW']
        else:
            # This is so that the flat pairs analysis can proceed
            # using the exposure time as a proxy for the incident
            # flux.
            hdulist[0].header['MONDIODE'] = 1.  
        hdulist[0].header['CCDTEMP'] = hdulist[0].header['TEMP_MEA']
        hdulist[0].header['TESTTYPE'] = test_type.upper()
        hdulist[0].header['IMGTYPE'] = image_type.upper()
        self._setAmpGeom(hdulist)
        self._writeFile(hdulist, locals(), verbose=verbose)
    def fe55(self, pattern='*_xray_xray_*.fits', time_stamp=None,
             verbose=True):
        return self._processFiles('fe55', 'fe55', pattern, 
                                  time_stamp=time_stamp, verbose=verbose)
    def bias(self, pattern='*_noims_nois_*.fits', time_stamp=None,
             verbose=True):
        return self._processFiles('fe55', 'bias', pattern,
                                  time_stamp=time_stamp, verbose=verbose)
    def dark(self, pattern='*_dark_dark_*.fits', time_stamp=None,
             verbose=True):
        return self._processFiles('dark', 'dark', pattern,
                                  time_stamp=time_stamp, verbose=verbose)
    def trap(self, pattern='*_trapspp_cycl*.fits', time_stamp=None,
             verbose=True):
        return self._processFiles('trap', 'ppump', pattern,
                                  time_stamp=time_stamp, verbose=verbose)
    def sflat_500_high(self, pattern='*_sflath_illu_*.fits', time_stamp=None,
                       verbose=True):
        return self._processFiles('sflat_500', 'flat', pattern,
                                  time_stamp=time_stamp, verbose=verbose,
                                  seqno_prefix='H')
    def sflat_500_low(self, pattern='*_sflatl_illu_*.fits', time_stamp=None,
                      verbose=True):
        return self._processFiles('sflat_500', 'flat', pattern,
                                  time_stamp=time_stamp, verbose=verbose,
                                  seqno_prefix='L')
    def spot(self, pattern='*_xtalk_illu_*.fits', time_stamp=None,
             verbose=True):
        return self._processFiles('spot', 'spot', pattern,
                                  time_stamp=time_stamp, verbose=verbose)
    def flat(self, pattern='*_ifwm_illu_*.fits', time_stamp=None,
             verbose=True):
        if time_stamp is None:
            time_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        exptime = lambda x : pyfits.open(x)[0].header['EXPOSURE']
        infiles = self._infiles(pattern)
        for infile in infiles:
            if verbose:
                print "processing", os.path.basename(infile)
            seqno = '%03i_flat1' % exptime(infile)
            self.translate(infile, 'flat', 'flat', seqno, time_stamp=time_stamp,
                           verbose=verbose)
        return time_stamp
    def lambda_scan(self, pattern='*_flat_*_illu_*.fits',
                    time_stamp=None, verbose=True):
        return super(e2vFitsTranslator, self).lambda_scan(pattern,
                                                          time_stamp=time_stamp,
                                                          verbose=verbose,
                                                          monowl_keyword='WAVELEN')
    def run_all(self):
        time_stamp = self.fe55()
        self.bias(time_stamp=time_stamp)
        self.dark()
        self.trap()
        time_stamp = self.sflat_500_high()
        self.sflat_500_low(time_stamp=time_stamp)
        self.spot()
        self.flat()
        self.lambda_scan()
