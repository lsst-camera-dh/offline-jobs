#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()

gains = eotestUtils.getSensorGains(jobname='fe55_offline')
mask_files = eotestUtils.glob_mask_files()
mask_files = [item for item in mask_files if item.find('rolloff_defects') == -1]

sflat_high_files = siteUtils.datacatalog_glob('*_sflat_500_flat_H*.fits',
                                              testtype='SFLAT_500',
                                              imgtype='FLAT',
                                              description='Superflat high files:')
task = sensorTest.CteTask()
task.run(sensor_id, sflat_high_files, flux_level='high', gains=gains)

sflat_low_files = siteUtils.datacatalog_glob('*_sflat_500_flat_L*.fits',
                                             testtype='SFLAT_500',
                                             imgtype='FLAT',
                                             description='Superflat low files:')
task = sensorTest.CteTask()
task.run(sensor_id, sflat_low_files, flux_level='low', gains=gains)
