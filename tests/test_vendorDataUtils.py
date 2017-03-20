"""
Unit tests for vendorDataUtils module.
"""
from __future__ import print_function, absolute_import
import os
import unittest
import siteUtils
import vendorDataUtils

class VendorDataUtilsTestCase(unittest.TestCase):
    """
    TestCase class for vendor data utilities.
    """
    def setUp(self):
        "Set up each test."
        self.sensor_ids = ('ITL-3800C-004', 'ITL-4400B-006', 'E2V-CCD250-107')
        self.system_noise_files = ('/nfs/farm/g/lsst/u1/jobHarness/jh_archive/ITL-CCD/ITL-3800C-004/vendorIngest/v0/1688/ITL-3800C-004_system_noise.txt',
                                   None,
                                   None)
        os.environ['LCATR_LIMS_URL'] = \
            'http://lsst-camera.slac.stanford.edu:80/eTraveler/Prod'

    def tearDown(self):
        "Clean up after each test."
        del os.environ['LCATR_LIMS_URL']

    def test_vendor_datacatalog_folder(self):
        """
        Test that the expected Data Catalog folder is returned for a
        given sensor.
        """
        for sensor_id in self.sensor_ids:
            folder = vendorDataUtils.vendor_DataCatalog_folder(sensor_id)
            expected = os.path.join('/LSST/mirror/SLAC-prod/prod/*',
                                    sensor_id, 'vendorIngest')
            self.assertEqual(folder, expected)

    @unittest.skipUnless(siteUtils.getSiteName() == 'SLAC',
                         'This test can only be run at SLAC')
    def test_query_for_system_noise(self):
        "Query for known vendor system noise folder at SLAC."
        for i, sensor_id in enumerate(self.sensor_ids):
            os.environ['LCATR_UNIT_ID'] = sensor_id
            folder = vendorDataUtils.vendor_DataCatalog_folder(sensor_id)
            system_noise_file = self.system_noise_files[i]
            filepath = vendorDataUtils.query_for_vendor_system_noise(folder)
            self.assertEqual(filepath, system_noise_file)

    def test_parse_system_noise(self):
        "Test the function to parse system noise files"
        system_noise_file = 'test_system_noise.txt'
        system_noise_input = dict((amp, 1+amp) for amp in range(1, 17))
        with open(system_noise_file, 'w') as output:
            output.write('# amp      system noise (ADU)\n')
            for amp, value in system_noise_input.items():
                output.write('%i   %f\n' % (amp, value))
        system_noise = vendorDataUtils.parse_system_noise_file(system_noise_file)
        for amp in system_noise:
            self.assertEqual(system_noise[amp], system_noise_input[amp])
        os.remove(system_noise_file)

    @unittest.skipUnless(siteUtils.getSiteName() == 'SLAC',
                         'This test can only be run at SLAC')
    def test_get_system_noise(self):
        "Test system noise retrieval for abstract function."
        gains = dict((amp, 1) for amp in range(1, 17))
        for i, sensor_id in enumerate(self.sensor_ids):
            os.environ['LCATR_UNIT_ID'] = sensor_id
            os.environ['LCATR_UNIT_TYPE'] = sensor_id.split('-')[0] + '-CCD'
            system_noise = vendorDataUtils.getSystemNoise(gains)
            filepath = self.system_noise_files[i]
            if filepath is None:
                system_noise_expected = vendorDataUtils.default_system_noise[siteUtils.getCcdVendor()]
            else:
                system_noise_expected = vendorDataUtils.parse_system_noise_file(filepath)
            for amp in system_noise:
                self.assertEqual(system_noise[amp], system_noise_expected[amp])

    def test_get_e2v_xls_values(self):
        xls_file = os.path.join(os.environ['OFFLINEJOBSDIR'], 'tests',
                                'e2v_test_data',
                                '16013-05-01_Pkg195_Mechanical_Shim_Test_Sheet.xls')
        results = vendorDataUtils.get_e2v_xls_values(xls_file)
        self.assertAlmostEqual(results['Mean Height'], 13.0002979240849)
        self.assertAlmostEqual(results['Deviation from Znom'],
                               0.000888893586400545)

        xls_file = os.path.join(os.environ['OFFLINEJOBSDIR'], 'tests',
                                'e2v_test_data',
                                '16013-10-04_Pkg163_Mechanical_Shim_Test_Sheet.xls')
        results = vendorDataUtils.get_e2v_xls_values(xls_file)
        self.assertAlmostEqual(results['Mean Height'], 12.9978611111111)
        self.assertAlmostEqual(results['Deviation from Znom'], 0.004)

        xls_file = os.path.join(os.environ['OFFLINEJOBSDIR'], 'tests',
                                'e2v_test_data',
                                '15433-03-04_Pkg107_Mechanical_Shim_Test_Sheet.xls')
        results = vendorDataUtils.get_e2v_xls_values(xls_file)
        self.assertAlmostEqual(results['Mean Height'], 13.0019166666667)
        self.assertRaises(KeyError, results.__getitem__, 'Deviation from Znom')

if __name__ == '__main__':
    unittest.main()
