#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import siteUtils

sensor_id = siteUtils.getUnitId()

sflat_high_files = siteUtils.datacatalog_glob('*_sflat_*500_flat_H*.fits',
                                              testtype='SFLAT_500',
                                              imgtype='FLAT',
                                              description='Superflat high files:')
task = sensorTest.CteTask()
task.run(sensor_id, sflat_high_files, flux_level='high')

sflat_low_files = siteUtils.datacatalog_glob('*_sflat_*500_flat_L*.fits',
                                             testtype='SFLAT_500',
                                             imgtype='FLAT',
                                             description='Superflat low files:')
task = sensorTest.CteTask()
task.run(sensor_id, sflat_low_files, flux_level='low')
