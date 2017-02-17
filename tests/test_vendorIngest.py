"""
Unit tests for validator_vendorIngest.py code.
"""
from __future__ import print_function
import os
import sys
import unittest
sys.path.insert(0, '../harnessed_jobs/vendorIngest/v0')
schema_dir = os.path.join(os.environ['OFFLINEJOBSDIR'],
                          'harnessed_jobs', 'vendorIngest', 'v0')
os.environ['LCATR_SCHEMA_PATH'] = \
    ":".join((schema_dir, os.environ['LCATR_SCHEMA_PATH']))
from validator_vendorIngest import ITL_metrology_files, ItlResults, \
    extract_ITL_metrology_date, e2vResults, e2v_metrology_files

class e2vResults_TestCase(unittest.TestCase):
    """
    Test case class for e2v EO vendor data.
    """
    def setUp(self):
        pass

    def tearDoown(self):
        pass

    def test_linearity_values(self):
        vendorDataDir = '.'
        vendor_results = e2vResults(vendorDataDir)
        results = vendor_results.flat_pairs()
        max_frac_devs = dict([(item['amp'], item['max_frac_dev'])
                              for item in results])
        self.assertAlmostEqual(0.135196/100., max_frac_devs[1])
        self.assertAlmostEqual(0.119365/100., max_frac_devs[8])

    def test_metrology_results(self):
        vendorDataDir = '.'
        vendor_results = e2vResults(vendorDataDir)
        results = vendor_results.metrology()[0]
        schema_keys = 'mounting_grade height_grade znom zmean zmedian zsdev z95halfband flatness_grade flatnesshalfband_95'.split()
        self.assertAlmostEqual(results['zmean'], 12.99786111)
        self.assertAlmostEqual(results['deviation_from_znom'], 0.004)
        for key in 'znom zmedian zsdev z95halfband flatnesshalfband_95'.split():
            self.assertEqual(results[key], -999)

class ITL_metrology_files_TestCase(unittest.TestCase):
    """
    TestCase class for ITL_metrology_files function.
    """
    def setUp(self):
        "Two possible filename patterns for metrology scan data."
        self.met_dir = os.path.join('tmp_metrology')
        self.expected_fn = os.path.join(self.met_dir,
                                        'IDxxx_SNxxxxxx_Z_Inspect_xxx.txt')
        self.non_std_fn = os.path.join(self.met_dir,
                                       'LSST_STA3800_Z_Inspect_R3.0_sn313.txt')
        try:
            os.makedirs(self.met_dir)
        except OSError:
            pass

    def tearDown(self):
        "Clean up temporary files and temporary directory."
        for fn in (self.expected_fn, self.non_std_fn):
            try:
                os.remove(fn)
            except OSError:
                pass
        os.rmdir(self.met_dir)

    def test_ITL_metrology_files(self):
        """
        Test for both possible filenames for metrology scan data.
        """
        rootdir = '.'
        with open(self.expected_fn, 'w') as output:
            output.write('\n')
        met_files = ITL_metrology_files(rootdir)
        self.assertEqual(len(met_files), 1)
        self.assertEqual(met_files[0], os.path.join(rootdir, self.expected_fn))
        os.remove(self.expected_fn)

        with open(self.non_std_fn, 'w') as output:
            output.write('  \n')
            output.write('Program')
        met_files = ITL_metrology_files(rootdir)
        self.assertEqual(len(met_files), 1)
        self.assertEqual(met_files[0], os.path.join(rootdir, self.non_std_fn))
        os.remove(self.non_std_fn)

    def test_ITL_metrology_results(self):
        """
        Test the persisting of the ITL results harvested from the
        delivered metrology.txt file.
        """
        vendorDataDir = '.'
        vendor_results = ItlResults(vendorDataDir, verbose=False)
        test_results = vendor_results._metrology_test_results()
        self.assertEqual(test_results['mounting_grade'], 'PASS')
        self.assertEqual(test_results['height_grade'], 'N/A')
        self.assertEqual(test_results['flatness_grade'], 'PASS')
        self.assertEqual(test_results['znom'], '12.9920')
        self.assertEqual(test_results['zmean'], '12.9921')
        self.assertEqual(test_results['zmedian'], '12.9922')
        self.assertEqual(test_results['zsdev'], '0.0011')
        self.assertEqual(test_results['z95halfband'], '0.0020')
        self.assertEqual(test_results['flatnesshalfband_95'], '1.5')

    def test_extract_ITL_metrology_date(self):
        """
        Test the function to extract the date from the first line of
        an ITL metrology scan file.
        """
        txtfile = os.path.join(os.environ['OFFLINEJOBSDIR'], 'tests',
                               'itl_test_data', 'metrology',
                               'ITL_metrology_scan_file_date_example')
        self.assertEqual(extract_ITL_metrology_date(txtfile),
                         '2016-10-28T11:32:43')

class ITL_EO_files_TestCase(unittest.TestCase):
    """
    Test the parsing of the ITL vendor results.
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_qe_values(self):
        vendorDataDir = '.'
        vendor_results = ItlResults(vendorDataDir, verbose=False)
        qe_values = vendor_results._qe_values()
        self.assertAlmostEqual(qe_values['u'], 68.0)
        self.assertAlmostEqual(qe_values['g'], 87.75)
        self.assertAlmostEqual(qe_values['r'], 93.0)
        self.assertAlmostEqual(qe_values['i'], 99.9)
        self.assertAlmostEqual(qe_values['z'], 93.2)
        self.assertAlmostEqual(qe_values['y'], 32.8)

if __name__ == '__main__':
    unittest.main()
