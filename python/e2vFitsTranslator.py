"""
FITS file translator for e2v vendor data.
"""
from __future__ import absolute_import, print_function
import os
import datetime
import astropy.io.fits as fits
import astropy.time
from VendorFitsTranslator import VendorFitsTranslator

__all__ = ['e2vFitsTranslator']

class e2vFitsTranslator(VendorFitsTranslator):
    """
    FITS Translator for e2v data based on their delta TRR package.
    """
    def __init__(self, lsst_num, rootdir, outputBaseDir='.'):
        """
        Constructor.
        lsst_num = LSST-assigned ID number. (LSST_NUM in FITS headers).
        rootdir = Top level directory containing the vendor files
        outputBaseDir = Directory where translated files (within
                        their subfolders)will be written.
        """
        super(e2vFitsTranslator, self).__init__(lsst_num, rootdir,
                                                outputBaseDir)

    def _extract_date_obs(self, hdulist):
        """
        e2v puts the date and time into the DATE-OBS FITS keyword using
        isot format.
        """
        date_obs = hdulist[0].header['DATE-OBS'][:len('2017-02-10T16:44:00')]
        time = astropy.time.Time(date_obs)
        self.obs_dates.append(time)

    def translate(self, infile, test_type, image_type, seqno, time_stamp=None,
                  verbose=True):
        """
        Method to translate e2v files to minimally conforming FITS
        files for analysis with the eotest package.
        """
        try:
            hdulist = fits.open(infile)
        except IOError, eobj:
            print(eobj)
            print("skipping")
            return
        lsst_num = self.lsst_num
        exptime = hdulist[0].header['EXPOSURE']
        hdulist[0].header['LSST_NUM'] = lsst_num
        hdulist[0].header['CCD_MANU'] = 'E2V'
        hdulist[0].header['CCD_SERN'] = hdulist[0].header['DEV_ID']
        hdulist[0].header['EXPTIME'] = exptime
        hdulist[0].header['MONOWL'] = hdulist[0].header['WAVELEN']

        if test_type == 'lambda':
            # Let this fail if LIGHTPOW is set with an invalid value,
            # i.e., an unquoted NaN.
            hdulist[0].header['MONDIODE'] = hdulist[0].header['LIGHTPOW']
        else:
            # This is so that the flat pairs analysis can proceed
            # using the exposure time as a proxy for the incident
            # flux.
            del hdulist[0].header['MONDIODE']
            hdulist[0].header['MONDIODE'] = 1.
            #
            # If LIGHTPOW is set, ensure that it has a valid value.
            #
            try:
                hdulist[0].header['LIGHTPOW']
            except fits.verify.VerifyError:
                del hdulist[0].header['LIGHTPOW']
                hdulist[0].header['LIGHTPOW'] = ''  # empty string

        hdulist[0].header['CCDTEMP'] = hdulist[0].header['TEMP_MEA']
        hdulist[0].header['TESTTYPE'] = test_type.upper()
        hdulist[0].header['IMGTYPE'] = image_type.upper()
        self._set_amp_geom(hdulist)
        # e2v has added extensions that are improperly formatted after
        # the image extension for the 16th segment.  We don't use
        # those extensions so omit them to avoid write errors.
        self._write_file(hdulist[:17], locals(), verbose=verbose)

    def fe55(self, pattern='*_xray_xray_*.fits', time_stamp=None,
             verbose=True):
        "Process Fe55 dataset."
        return self._process_files('fe55', 'fe55', pattern,
                                   time_stamp=time_stamp, verbose=verbose)

    def bias(self, pattern='*_noims_nois_*.fits', time_stamp=None,
             verbose=True):
        "Process bias frame dataset."
        return self._process_files('fe55', 'bias', pattern,
                                   time_stamp=time_stamp, verbose=verbose)

    def dark(self, pattern='*_dark_dark_*.fits', time_stamp=None,
             verbose=True):
        "Process dark frame dataset."
        return self._process_files('dark', 'dark', pattern,
                                   time_stamp=time_stamp, verbose=verbose)

    def trap(self, pattern='*_trapspp_cycl*.fits', time_stamp=None,
             verbose=True):
        "Process trap dataset."
        return self._process_files('trap', 'ppump', pattern,
                                   time_stamp=time_stamp, verbose=verbose)

    def sflat_500_high(self, pattern='*_sflath_illu_*.fits', time_stamp=None,
                       verbose=True):
        "Process high flux level superflat dataset."
        return self._process_files('sflat_500', 'flat', pattern,
                                   time_stamp=time_stamp, verbose=verbose,
                                   seqno_prefix='H')

    def sflat_500_low(self, pattern='*_sflatl_illu_*.fits', time_stamp=None,
                      verbose=True):
        "Process low flux level superflat dataset."
        return self._process_files('sflat_500', 'flat', pattern,
                                   time_stamp=time_stamp, verbose=verbose,
                                   seqno_prefix='L')

    def spot(self, pattern='*_xtalk_illu_*.fits', time_stamp=None,
             verbose=True):
        "Process spot dataset"
        return self._process_files('spot', 'spot', pattern,
                                   time_stamp=time_stamp, verbose=verbose)

    def flat(self, pattern='*_ifwm_illu_*.fits', time_stamp=None,
             verbose=True):
        "Process flat pair data set for full well and ptc analyses."
        if time_stamp is None:
            time_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        exptime = lambda x: fits.open(x)[0].header['EXPOSURE']
        infiles = self._infiles(pattern)
        for infile in infiles:
            if verbose:
                print("processing", os.path.basename(infile))
            seqno = '%03i_flat1' % exptime(infile)
            self.translate(infile, 'flat', 'flat', seqno, time_stamp=time_stamp,
                           verbose=verbose)
        return time_stamp

    def lambda_scan(self, pattern='*_flat_*_illu_*.fits',
                    time_stamp=None, verbose=True, monowl_keyword=None):
        "Process the QE dataset."
        return super(e2vFitsTranslator, self).lambda_scan(pattern,
                                                          time_stamp=time_stamp,
                                                          verbose=verbose,
                                                          monowl_keyword='WAVELEN')

    def run_all(self):
        "Run all of the methods for each test type"
        time_stamp = self.fe55()
        self.bias(time_stamp=time_stamp)
        self.dark()
        self.trap()
        time_stamp = self.sflat_500_high()
        self.sflat_500_low(time_stamp=time_stamp)
        self.spot()
        self.flat()
        self.lambda_scan()
