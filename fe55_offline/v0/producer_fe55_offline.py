#!/usr/bin/env python
import os
import lsst.eotest.sensor as sensorTest
import siteUtils

sensor_id = siteUtils.getUnitId()
fe55_files = siteUtils.datacatalog_glob('*_fe55_fe55_*.fits',
                                        testtype="FE55",
                                        imgtype="FE55",
                                        description='Fe55 files:')

# Roll-off defects mask needs an input file to get the vendor
# geometry and will be used for all analyses.
rolloff_mask_file = '%s_rolloff_defects_mask.fits' % sensor_id
sensorTest.rolloff_mask(fe55_files[0], rolloff_mask_file)

task = sensorTest.Fe55Task()
task.run(sensor_id, fe55_files, (rolloff_mask_file,))
