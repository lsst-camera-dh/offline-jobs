"""
Unit tests for validator_vendorIngest.py code.
"""
import os
import sys
import unittest
sys.path.insert(0, '../harnessed_jobs/vendorIngest/v0')
from validator_vendorIngest import ITL_metrology_files, ItlResults

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
        vendor_results = ItlResults(vendorDataDir)
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

if __name__ == '__main__':
    unittest.main()
