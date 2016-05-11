"""
Unit test code for vendorFitsTranslators.py module
"""
import os
import glob
import shutil
import unittest
import astropy.io.fits as fits
from vendorFitsTranslators import VendorFitsTranslator, ItlFitsTranslator

_itl_test_file = 'ID089_SN20234_linearity.0058.fits'
if not os.path.isfile(_itl_test_file):
    _itl_test_file = None

_itl_8amp_test_file = 'ID004_sn21467_linearity.0001.fits'
if not os.path.isfile(_itl_8amp_test_file):
    _itl_8amp_test_file = None

class DummyVendorFitsTranslator(VendorFitsTranslator):
    "Dummy subclass to provide stubs for base class template methods."

    def __init__(self, lsst_num, rootdir, outputBaseDir):
        "Constructor stub"
        super(DummyVendorFitsTranslator, self).__init__(lsst_num, rootdir,
                                                        outputBaseDir)

    def translate(self, infile, test_type, image_type, seqno,
                  time_stamp=None, verbose=True):
        "Re-write the input FITS file with the conforming name."
        lsst_num = self.lsst_num
        time_stamp = '000'
        self._writeFile(fits.open(infile), locals(), verbose=verbose)

class VendorTranslatorTestCase(unittest.TestCase):
    """
    TestCase class for VendorFitsTranslator base class.
    """
    _wls = (350, 450, 500, 750, 800, 1000)
    def setUp(self):
        self._generate_ITL_lambda_files()
        self._generate_e2v_lambda_files()

    def tearDown(self):
        for item in self._ITL_files:
            os.remove(item)
        for item in self._e2v_files:
            os.remove(item)
        shutil.rmtree('./lambda')

    def _generate_ITL_lambda_files(self):
        self._ITL_files = []
        for i, wl in enumerate(self._wls):
            filename = 'ITL_lambda_scan_%02i.fits' % i
            hdulist = fits.HDUList()
            hdulist.append(fits.PrimaryHDU())
            if i == 0:
                hdulist[0].header['EXPTIME'] = 0.0
            else:
                hdulist[0].header['EXPTIME'] = float(i*0.3)
            hdulist[0].header['MONOWL'] = wl
            hdulist.writeto(filename, clobber=True)
            self._ITL_files.append(filename)

    def _generate_e2v_lambda_files(self):
        self._e2v_files = []
        for i, wl in enumerate(self._wls):
            filename = 'e2v_lambda_scan_%02i.fits' % i
            hdulist = fits.HDUList()
            hdulist.append(fits.PrimaryHDU())
            hdulist[0].header['MONOWL'] = wl
            hdulist.writeto(filename, clobber=True)
            self._e2v_files.append(filename)

    def test_lambda_scan_for_ITL(self):
        translator = DummyVendorFitsTranslator('000-00', '.', '.')
        translator.lambda_scan(pattern='ITL_lambda_scan_*.fits')
        files = sorted(glob.glob('lambda/000/000-00_lambda_flat_*.fits'))
        self.assertEqual(len(files), 5)
        for item in files:
            header = fits.open(item)[0].header
            self.assertNotEqual(header['EXPTIME'], 0)
            self.assertNotEqual(header['MONOWL'], 350)

    def test_lambda_scan_for_e2v(self):
        translator = DummyVendorFitsTranslator('000-00', '.', '.')
        translator.lambda_scan(pattern='e2v_lambda_scan_*.fits')
        files = sorted(glob.glob('lambda/000/000-00_lambda_flat_*.fits'))
        self.assertEqual(len(files), 6)
        for i, item in enumerate(files):
            header = fits.open(item)[0].header
            self.assertRaises(KeyError, header.__getitem__, 'EXPTIME')
            self.assertEqual(header['MONOWL'], self._wls[i])

class ItlFitsTranslatorsTestCase(unittest.TestCase):
    """
    TestCase class for ItlFitsTranlator class.
    """
    def setUp(self):
        self._itl_lsst_num = 'ITL-3800C-089'
        self._itl_translator = ItlFitsTranslator(self._itl_lsst_num, '.')

    def tearDown(self):
        shutil.rmtree('./linearity')

    @unittest.skipUnless(_itl_test_file, "No ITL test file available")
    def test_ItlTranslation(self):
        test_type = 'linearity'
        image_type = 'flat'
        seqno = 16
        time_stamp = '000'
        self._itl_translator.translate(_itl_test_file, test_type, image_type,
                                       seqno, time_stamp=time_stamp)

    @unittest.skipUnless(_itl_8amp_test_file,
                         "No 8 amp ITL test file available")
    def test_8amp_ItlTranslation(self):
        test_type = 'linearity'
        image_type = 'flat'
        seqno = 8
        time_stamp = '000'
        self._itl_translator.translate(_itl_8amp_test_file, test_type,
                                       image_type, seqno, time_stamp=time_stamp)

if __name__ == '__main__':
    unittest.main()
