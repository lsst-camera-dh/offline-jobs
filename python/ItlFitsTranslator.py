"""
FITS file translator for ITL vendor data.
"""
from __future__ import absolute_import, print_function, division
import os
import subprocess
from collections import OrderedDict
import ConfigParser
import datetime
import scipy.constants
import astropy.io.fits as fits
import astropy.time
from VendorFitsTranslator import VendorFitsTranslator

__all__ = ['ItlFitsTranslator']

planck = scipy.constants.h  # J-s
clight = scipy.constants.c  # m/s

class ItlFitsTranslator(VendorFitsTranslator):
    """
    FITS Translator for ITL data.
    """
    def __init__(self, lsst_num, rootdir, outputBaseDir='.'):
        """
        Constructor.
        lsst_num = LSST-assigned ID number. (LSST_NUM in FITS headers).
        rootdir = Top level directory containing the vendor files
        outputBaseDir = Directory where translated files (within
                        their subfolders)will be written.
        """
        super(ItlFitsTranslator, self).__init__(lsst_num, rootdir,
                                                outputBaseDir)
        # Identify the directory containing the subdirectories with
        # the data for the various tests.
        my_rootdir = rootdir.rstrip('/') # remove any trailing slashes
        my_rootdir = subprocess.check_output('find %s/ -name superflat1 -print'
                                             % my_rootdir, shell=True)
        self.rootdir = os.path.split(my_rootdir)[0]

    def _extract_date_obs(self, hdulist):
        """
        ITL files split the date and time into DATE-OBS and TIME-OBS
        header keywords.
        """
        date_obs = hdulist[0].header['DATE-OBS']
        time_obs = hdulist[0].header['TIME-OBS'][:len('22:50:32')]
        time = astropy.time.Time('T'.join((date_obs, time_obs)))
        self.obs_dates.append(time)

    def translate(self, infile, test_type, image_type, seqno, time_stamp=None,
                  verbose=True):
        """
        Method to translate ITL files to minimally conforming FITS
        files for analysis with the eotest package.
        """
        try:
            hdulist = fits.open(infile)
        except IOError as eobj:
            print(eobj)
            print("skipping")
            return
        lsst_num = self.lsst_num
        hdulist[0].header['LSST_NUM'] = lsst_num
        hdulist[0].header['CCD_MANU'] = 'ITL'
        hdulist[0].header['MONOWL'] = float(hdulist[0].header['MONOWL'])
        hdulist[0].header['TESTTYPE'] = test_type.upper()
        hdulist[0].header['IMGTYPE'] = image_type.upper()
        self._write_file(hdulist, locals(), verbose=verbose)

    def fe55(self, pattern='fe55/*fe55.*.fits', time_stamp=None,
             verbose=True):
        "Process Fe55 dataset."
        return self._process_files('fe55', 'fe55', pattern,
                                   time_stamp=time_stamp, verbose=verbose,
                                   skip_zero_exptime=True)

    def bias(self, pattern='bias/*bias.*.fits', time_stamp=None,
             verbose=True):
        "Process bias frame dataset."
        return self._process_files('fe55', 'bias', pattern,
                                   time_stamp=time_stamp, verbose=verbose)

    def dark(self, pattern='dark/*dark.*.fits', time_stamp=None,
             verbose=True):
        "Process dark frame dataset."
        return self._process_files('dark', 'dark', pattern,
                                   time_stamp=time_stamp, verbose=verbose,
                                   skip_zero_exptime=True)

    def trap(self, pattern='pocketpump/*pocketpump*.fits', time_stamp=None,
             verbose=True):
        "Process trap dataset."
        if time_stamp is None:
            time_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        infiles = self._infiles(os.path.join(self.rootdir, pattern))
        image_type = lambda x: fits.open(x)[0].header['OBJECT']
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

    def sflat_500_high(self, pattern='superflat2/*superflat.*.fits',
                       time_stamp=None, verbose=True):
        "Process high flux level superflat dataset."
        return self._process_files('sflat_500', 'flat', pattern,
                                   time_stamp=time_stamp, verbose=verbose,
                                   seqno_prefix='H')

    def sflat_500_low(self, pattern='superflat1/*superflat.*.fits',
                      time_stamp=None, verbose=True):
        "Process low flux level superflat dataset."
        return self._process_files('sflat_500', 'flat', pattern,
                                   time_stamp=time_stamp, verbose=verbose,
                                   seqno_prefix='L')

    def spot(self, pattern='', time_stamp=None, verbose=True):
        "Process spot dataset"
        raise NotImplementedError("ITL spot dataset translation not implemented.")

    def linearity(self, pattern='linearity/*linearity.*.fits', time_stamp=None,
                  verbose=True):
        "Process special linearity dataset for ITL data."
        return self._process_files('linearity', 'flat', pattern,
                                   time_stamp=time_stamp, verbose=verbose)

    def flat(self, pattern='ptc/*ptc.*.fits', time_stamp=None,
             verbose=True):
        "Process flat pair data set for full well and ptc analyses."
        if time_stamp is None:
            time_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        exptime = lambda x: fits.open(x)[0].header['EXPTIME']
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

    def lambda_scan(self, pattern='qe/*qe.*.fits', time_stamp=None,
                    verbose=True, monowl_keyword='MONOWL'):
        "Process the QE dataset."
        time_stamp = super(ItlFitsTranslator, self).lambda_scan(pattern,
                                                                time_stamp=time_stamp,
                                                                verbose=verbose)
        flux = self._compute_incident_flux()
        sensor_id = self.lsst_num
        command = 'find . -name %(sensor_id)s_lambda_flat*.fits -print' % locals()
        files = subprocess.check_output(command, shell=True).split()
        for item in files:
            fits_obj = fits.open(item)
            wl = int(fits_obj[0].header[monowl_keyword])
            fits_obj[0].header['MONDIODE_ORIG'] = fits_obj[0].header['MONDIODE']
            fits_obj[0].header['MONDIODE'] = flux[wl]
            fits_obj.writeto(item, clobber=True)
        return time_stamp

    @staticmethod
    def _compute_incident_flux():
        """
        Read in qe.txt file and compute the incident fluxes as a function
        of wavelength.  In that file, there are two notes on computing
        the flux at the sensor:

           Note1 = Flux @ sensor is Flux*Throughput/CalScal
           Note2 = Flux is [photons/sec/mm^2@diode]

        """
        vendor_data_dir = os.readlink('vendorData')
        command = 'find %(vendor_data_dir)s/ -name qe.txt -print' % locals()
        qe_txt_file = subprocess.check_output(command, shell=True).split()[0]
        parser = ConfigParser.ConfigParser()
        parser.read(qe_txt_file)
        cal_scale = float(dict(parser.items('Info'))['calscale'])
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
            lightpow = flux*energy_per_photon*mm2_per_cm2*throughput/cal_scale
            flux_at_sensor[wl] = lightpow
        return flux_at_sensor

    def run_all(self):
        "Run all of the methods for each test type"
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
