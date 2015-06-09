#!/usr/bin/env python
import os
import sys
import lsst.eotest.sensor as sensorTest
import siteUtils

sensor_id = siteUtils.getUnitId()
query = 'LSST_NUM=="%(sensor_id)s" && IMGTYPE=="FE55"' % locals()

datasets = siteUtils.datacatalog_query(query)
acq_job_id = max(datasets.job_ids())
fe55_files = datasets.full_paths(job_id=acq_job_id)

print fe55_files
sys.stdout.flush()

# Roll-off defects mask needs an input file to get the vendor
# geometry, and will be used for all analyses.
rolloff_mask_file = '%s_rolloff_defects_mask.fits' % sensor_id
sensorTest.rolloff_mask(fe55_files[0], rolloff_mask_file)

task = sensorTest.Fe55Task()
task.run(sensor_id, fe55_files, (rolloff_mask_file,))
