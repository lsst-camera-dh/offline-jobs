#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
sflat_files = siteUtils.datacatalog_glob('*_sflat_500_*.fits',
                                         testtype='SFLAT_500',
                                         imgtype='FLAT',
                                         description='Superflat files:')
mask_files = eotestUtils.glob_mask_files()

task = sensorTest.CteTask()
task.run(sensor_id, sflat_files, mask_files)
