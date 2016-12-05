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
        vendor_results = ItlResults(vendorDataDir)
        qe_values = vendor_results._qe_values()
        self.assertAlmostEqual(qe_values['u'], 68.0)
        self.assertAlmostEqual(qe_values['g'], 87.75)
        self.assertAlmostEqual(qe_values['r'], 93.0)
        self.assertAlmostEqual(qe_values['i'], 99.9)
        self.assertAlmostEqual(qe_values['z'], 93.2)
        self.assertAlmostEqual(qe_values['y'], 32.8)

if __name__ == '__main__':
    unittest.main()
