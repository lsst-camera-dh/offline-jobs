#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
trap_file = siteUtils.datacatalog_glob('*_trap_ppump_*.fits',
                                       testtype='TRAP',
                                       imgtype='PPUMP',
                                       description='Trap file:')[0]
mask_files = eotestUtils.glob_mask_files()
gains = eotestUtils.getSensorGains(jobname='fe55_offline')

task = sensorTest.TrapTask()
task.run(sensor_id, trap_file, mask_files, gains)
