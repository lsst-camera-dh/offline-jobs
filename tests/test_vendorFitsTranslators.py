"""
Unit test code for vendorFitsTranslators.py module
"""
from __future__ import print_function, absolute_import
import os
import glob
import shutil
import unittest
import astropy.io.fits as fits
from ItlFitsTranslator import ItlFitsTranslator
from e2vFitsTranslator import e2vFitsTranslator

_itl_test_file = '/nfs/farm/g/lsst/u1/vendorData/ITL/ITL-3800C-089/Dev/16310/report1/linearity/ID089_SN20234_linearity.0058.fits'
if not os.path.isfile(_itl_test_file):
    _itl_test_file = None

_itl_8amp_test_file = '/nfs/farm/g/lsst/u1/vendorData/ftp/ITL/LSST_Wavefront/20160420/report1/linearity/ID004_sn21467_linearity.0001.fits'
if not os.path.isfile(_itl_8amp_test_file):
    _itl_8amp_test_file = None

_wls = (350, 450, 500, 750, 800, 1000)

class DummyItlVendorFitsTranslator(ItlFitsTranslator):
    "Dummy subclass to provide stubs for base class template methods."
    def __init__(self, lsst_num, rootdir, outputBaseDir):
        "Constructor stub"
        super(DummyItlVendorFitsTranslator, self).__init__(lsst_num, rootdir,
                                                           outputBaseDir)

    def translate(self, infile, test_type, image_type, seqno,
                  time_stamp=None, verbose=True):
        "Re-write the input FITS file with the conforming name."
        lsst_num = self.lsst_num
        time_stamp = '000'
        self._write_file(fits.open(infile), locals(), verbose=verbose)

    @staticmethod
    def _compute_incident_flux():
        return dict((wl, 1) for wl in _wls)

class Dummye2vVendorFitsTranslator(e2vFitsTranslator):
    "Dummy subclass to provide stubs for base class template methods."
    def __init__(self, lsst_num, rootdir, outputBaseDir):
        "Constructor stub"
        super(Dummye2vVendorFitsTranslator, self).__init__(lsst_num, rootdir,
                                                           outputBaseDir)

    def translate(self, infile, test_type, image_type, seqno,
                  time_stamp=None, verbose=True):
        "Re-write the input FITS file with the conforming name."
        lsst_num = self.lsst_num
        time_stamp = '000'
        self._write_file(fits.open(infile), locals(), verbose=verbose)

class VendorTranslatorTestCase(unittest.TestCase):
    """
    TestCase class for VendorFitsTranslator base class.
    """
    def setUp(self):
        "Generate the test files for each vendor."
        self._generate_ITL_lambda_files()
        self._generate_e2v_lambda_files()

    def tearDown(self):
        "Clean up the generated files and directories."
        for item in self._ITL_files:
            os.remove(item)
        for item in self._e2v_files:
            os.remove(item)
        shutil.rmtree('./lambda')

    def _generate_ITL_lambda_files(self):
        "Generate ITL files including one with a zero time exposure."
        self._ITL_files = []
        for i, wl in enumerate(_wls):
            filename = 'ITL_lambda_scan_%02i.fits' % i
            hdulist = fits.HDUList()
            hdulist.append(fits.PrimaryHDU())
            if i == 0:
                hdulist[0].header['EXPTIME'] = 0.0
            else:
                hdulist[0].header['EXPTIME'] = float(i*0.3)
            hdulist[0].header['MONOWL'] = wl
            hdulist[0].header['MONDIODE'] = 1
            hdulist.writeto(filename, clobber=True)
            self._ITL_files.append(filename)

    def _generate_e2v_lambda_files(self):
        "Generate e2v files."
        self._e2v_files = []
        for i, wl in enumerate(_wls):
            filename = 'e2v_lambda_scan_%02i.fits' % i
            hdulist = fits.HDUList()
            hdulist.append(fits.PrimaryHDU())
            hdulist[0].header['WAVELEN'] = wl
            hdulist[0].header['MONOWL'] = wl
            hdulist.writeto(filename, clobber=True)
            self._e2v_files.append(filename)

    def test_lambda_scan_for_ITL(self):
        "Test that the zero exposure time frame is not translated."
        translator = DummyItlVendorFitsTranslator('000-00', '.', '.')
        translator.lambda_scan(pattern='ITL_lambda_scan_*.fits')
        files = sorted(glob.glob('lambda/000/000-00_lambda_flat_*.fits'))
        self.assertEqual(len(files), 5)
        for item in files:
            header = fits.open(item)[0].header
            self.assertNotEqual(header['EXPTIME'], 0)
            self.assertNotEqual(header['MONOWL'], 350)

    def test_lambda_scan_for_e2v(self):
        "Test that all e2v files are expected."
        translator = Dummye2vVendorFitsTranslator('000-00', '.', '.')
        translator.lambda_scan(pattern='e2v_lambda_scan_*.fits')
        files = sorted(glob.glob('lambda/000/000-00_lambda_flat_*.fits'))
        self.assertEqual(len(files), 6)
        for i, item in enumerate(files):
            header = fits.open(item)[0].header
            self.assertRaises(KeyError, header.__getitem__, 'EXPTIME')
            self.assertEqual(header['MONOWL'], _wls[i])

class ItlFitsTranslatorsTestCase(unittest.TestCase):
    """
    TestCase class for ItlFitsTranlator class.
    """
    def setUp(self):
        "Set up the ItlFitsTranslator object"
        self._itl_lsst_num = 'ITL-3800C-089'
        self._itl_translator = ItlFitsTranslator(self._itl_lsst_num, '.')

    def tearDown(self):
        "Clean up the linearity directory"
        shutil.rmtree('./linearity')

    @unittest.skipUnless(_itl_test_file, "No ITL test file available")
    def test_ItlTranslation(self):
        "Test the translation for science sensors."
        test_type = 'linearity'
        image_type = 'flat'
        seqno = 16
        time_stamp = '000'
        self._itl_translator.translate(_itl_test_file, test_type, image_type,
                                       seqno, time_stamp=time_stamp)

    @unittest.skipUnless(_itl_8amp_test_file,
                         "No 8 amp ITL test file available")
    def test_8amp_ItlTranslation(self):
        "Test the translation for wavefront sensors."
        test_type = 'linearity'
        image_type = 'flat'
        seqno = 8
        time_stamp = '000'
        self._itl_translator.translate(_itl_8amp_test_file, test_type,
                                       image_type, seqno, time_stamp=time_stamp)

if __name__ == '__main__':
    unittest.main()
