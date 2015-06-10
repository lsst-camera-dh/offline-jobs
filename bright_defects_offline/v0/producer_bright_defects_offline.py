#!/usr/bin/env python
import sys
import lsst.eotest.sensor as sensorTest
from lcatr.harness.helpers import dependency_glob
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
query = 'LSST_NUM=="%(sensor_id)s" && IMGTYPE=="DARK" && TESTTYPE=="DARK"' % locals()
datasets = siteUtils.datacatalog_query(query)

# Filter on '_dark_dark_' to avoid *_dark_median_*.fits files in the
# Data Catalog from any previous analyses.
dark_files = [x for x in datasets.full_paths() if x.find('_dark_dark_') != -1]

mask_files = dependency_glob('*_mask.fits', jobname='fe55_offline')

print dark_files
print mask_files
sys.stdout.flush()

gains = eotestUtils.getSensorGains(sensor_id, jobname='fe55_offline')

task = sensorTest.BrightPixelsTask()
task.run(sensor_id, dark_files, mask_files, gains)
