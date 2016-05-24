"""
Base class for FITS translators of vendor FITS files.
"""
from __future__ import absolute_import, print_function
import os
import glob
import datetime
import astropy.io.fits as fits
import lsst.eotest.sensor as sensorTest

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
        """
        Constructor.
        lsst_num = LSST-assigned ID number. (LSST_NUM in FITS headers).
        rootdir = Top level directory containing the vendor files
        outputBaseDir = Directory where translated files (within
                        their subfolders)will be written.
        """
        self.lsst_num = lsst_num
        self.rootdir = rootdir
        self.output_base_dir = outputBaseDir
        self.outfiles = []

    def _infiles(self, pattern):
        "glob for files with the specified pattern"
        return sorted(glob.glob(os.path.join(self.rootdir, pattern)))

    def _write_file(self, hdulist, local_vars, verbose=True):
        "Write translated files with conforming filenames."
        outfile = "%(lsst_num)s_%(test_type)s_%(image_type)s_%(seqno)s_%(time_stamp)s.fits" % local_vars
        outdir = os.path.join(self.output_base_dir, local_vars['test_type'],
                              local_vars['time_stamp'])
        try:
            os.makedirs(outdir)
        except OSError:
            pass
        outfile = os.path.join(outdir, outfile)
        if os.path.relpath(outfile) not in self.outfiles:
            if verbose:
                print("writing", outfile)
            hdulist.writeto(outfile, checksum=True, output_verify='fix')
            self.outfiles.append(os.path.relpath(outfile))

    @staticmethod
    def _set_amp_geom(hdulist):
        "Set the amplifier geometry of the translated FITS file."
        detxsize = 8*hdulist[1].header['NAXIS1']
        detysize = 2*hdulist[1].header['NAXIS2']
        amp_geom = sensorTest.AmplifierGeometry(detxsize=detxsize,
                                               detysize=detysize)
        hdulist[0].header['DETSIZE'] = amp_geom.DETSIZE
        for hdu in range(1, 17):
            amp = hdulist[hdu].header['AMPNO']
            hdulist[hdu].header['DETSIZE'] = amp_geom[amp]['DETSIZE']
            hdulist[hdu].header['DATASEC'] = amp_geom[amp]['DATASEC']
            hdulist[hdu].header['DETSEC'] = amp_geom[amp]['DETSEC']

    def _process_files(self, test_type, image_type, pattern, seqno_prefix=None,
                       time_stamp=None, verbose=True, skip_zero_exptime=False):
        """
        Process the files based on the test type, image type and glob
        pattern.
        """
        my_pattern = os.path.join(self.rootdir, pattern)
        infiles = self._infiles(my_pattern)
        if verbose and not infiles:
            print("\nWARNING:")
            print("No files found for TESTTYPE=%(test_type)s, IMGTYPE=%(image_type)s and file pattern %(my_pattern)s\n" % locals())
        if time_stamp is None:
            time_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        for iframe, infile in enumerate(infiles):
            if verbose:
                print("processing", os.path.basename(infile))
            if (skip_zero_exptime and
                fits.open(infile)[0].header['EXPTIME'] == 0):
                if verbose:
                    print("skipping zero exposure frame.")
                continue
            seqno = '%03i' % iframe
            if seqno_prefix is not None:
                seqno = seqno_prefix + seqno
            self.translate(infile, test_type, image_type, seqno,
                           time_stamp=time_stamp, verbose=verbose)
        return time_stamp

    def lambda_scan(self, pattern=None, time_stamp=None, verbose=True,
                    monowl_keyword='MONOWL'):
        "Process the QE dataset."
        if pattern is None:
            raise ValueError("A pattern argument or keyword is required.")
        if time_stamp is None:
            time_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        infiles = self._infiles(pattern)
        for infile in infiles:
            if verbose:
                print("processing", os.path.basename(infile))
            hdr = fits.open(infile)[0].header
            try:
                if hdr['EXPTIME'] == 0:
                    # Skip the bias frame that ITL includes in their
                    # set of QE files.
                    continue
            except KeyError:
                # This must be an e2v-produced file since they don't
                # fill the EXPTIME keyword and that only gets set by
                # the call to the e2vFitsTranslator.translate below.
                pass
            seqno = "%04i" % int(hdr[monowl_keyword])
            self.translate(infile, 'lambda', 'flat', seqno,
                           time_stamp=time_stamp, verbose=verbose)
        return time_stamp
