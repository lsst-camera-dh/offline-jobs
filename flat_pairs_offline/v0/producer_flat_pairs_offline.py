#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()

ccd_vendor = siteUtils.getCcdVendor()

flat_files = siteUtils.datacatalog_glob('*_flat*flat?_*.fits',
                                        testtype='FLAT',
                                        imgtype='FLAT',
                                        description='Flat files:')
mask_files = eotestUtils.glob_mask_files()
gains = eotestUtils.getSensorGains(jobname='fe55_offline')

task = sensorTest.FlatPairTask()
task.run(sensor_id, flat_files, mask_files, gains)

if ccd_vendor == 'ITL':
    #
    # Perform linearity analysis using special dataset from ITL
    try:
        flat_files = siteUtils.datacatalog_glob('*_linearity_flat*.fits',
                                                testtype='LINEARITY',
                                                imgtype='FLAT',
                                                description='ITL linearity files:')
        task = sensorTest.LinearityTask()
        task.run(sensor_id, flat_files, mask_files, gains)
    except:
        # Unconditionally skip this if there are no special linearity
        # files, e.g., if analyzing TS3 data or ITL datasets
        # pre-dating the special dataset.
        pass
