#!/usr/bin/env python
import os
import pylab
import lsst.eotest.image_utils as imutils
import lsst.eotest.sensor as sensorTest
import siteUtils

sensor_id = siteUtils.getUnitId()
fe55_files = siteUtils.datacatalog_glob('*_fe55_fe55_*.fits',
                                        testtype="FE55",
                                        imgtype="FE55",
                                        description='Fe55 files:')

#
# Create a mean bias file from the bias files that should accompany
# the Fe55 exposures.
#
bias_files = siteUtils.datacatalog_glob('*_fe55_bias_*.fits',
                                        testtype='FE55',
                                        imgtype='BIAS',
                                        description='Bias files:')
nf = len(bias_files)
if nf > 0:
    outfile = '%(sensor_id)s_mean_bias_%(nf)i.fits' % locals()
    imutils.fits_mean_file(bias_files, outfile)

#
# Create a png zoom of the upper right corner of segment 1 for an Fe55
# exposure for inclusion in the test report
#
sensorTest.fe55_zoom(fe55_files[0], size=250, amp=1)
pylab.savefig('%(sensor_id)s_fe55_zoom.png' % locals())

# Roll-off defects mask needs an input file to get the vendor
# geometry and will be used for all analyses.
rolloff_mask_file = '%s_rolloff_defects_mask.fits' % sensor_id
sensorTest.rolloff_mask(fe55_files[0], rolloff_mask_file)

task = sensorTest.Fe55Task()
task.config.fit_xy = True
task.run(sensor_id, fe55_files, (rolloff_mask_file,), accuracy_req=0.01)
