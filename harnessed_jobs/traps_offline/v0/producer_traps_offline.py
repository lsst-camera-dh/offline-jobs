#!/usr/bin/env python
from __future__ import print_function
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()

trap_file = siteUtils.datacatalog_glob('*_trap_ppump_*.fits',
                                       testtype='TRAP',
                                       imgtype='PPUMP',
                                       description='Trap file:')[0]

mask_files = eotestUtils.glob_mask_files()
# Omit rolloff defects mask since a trap in the rolloff edge region can
# affect the entire column.
mask_files = [item for item in mask_files if item.find('rolloff_defects') == -1]
print("Using mask files:")
for mask_file in mask_files:
    print("  " + mask_file)

gains = eotestUtils.getSensorGains(jobname='fe55_offline')

task = sensorTest.TrapTask()
task.run(sensor_id, trap_file, mask_files, gains)
