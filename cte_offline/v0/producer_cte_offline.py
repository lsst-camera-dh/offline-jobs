#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import siteUtils

sensor_id = siteUtils.getUnitId()
sflat_files = siteUtils.datacatalog_glob('*_sflat_500_*.fits',
                                         testtype='SFLAT_500',
                                         imgtype='FLAT',
                                         description='Superflat files:')

task = sensorTest.CteTask()
task.run(sensor_id, sflat_files)
