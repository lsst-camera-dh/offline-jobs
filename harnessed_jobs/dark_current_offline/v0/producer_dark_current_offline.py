#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
dark_files = siteUtils.datacatalog_glob('*_dark_dark_*.fits',
                                        testtype='DARK', 
                                        imgtype='DARK', 
                                        description='Dark files:')
mask_files = eotestUtils.glob_mask_files()
gains = eotestUtils.getSensorGains(jobname='fe55_offline')

task = sensorTest.DarkCurrentTask()
task.run(sensor_id, dark_files, mask_files, gains)
