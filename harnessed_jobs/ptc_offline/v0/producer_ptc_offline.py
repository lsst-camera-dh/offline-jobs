#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
flat_files = siteUtils.datacatalog_glob('*_flat*flat?_*.fits',
                                        testtype='FLAT',
                                        imgtype='FLAT',
                                        description='Flat files:')
mask_files = eotestUtils.glob_mask_files()
gains = eotestUtils.getSensorGains(jobname='fe55_offline')

task = sensorTest.PtcTask()
task.run(sensor_id, flat_files, mask_files, gains)
