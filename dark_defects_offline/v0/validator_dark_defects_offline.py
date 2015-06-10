#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import lcatr.schema
import siteUtils

sensor_id = siteUtils.getUnitId()

mask_file = '%s_dark_pixel_mask.fits' % sensor_id
results = [lcatr.schema.fileref.make(mask_file)]

eotest_results = '%s_eotest_results.fits' % sensor_id
data = sensorTest.EOTestResults(eotest_results)
amps = data['AMP']
npixels = data['NUM_DARK_PIXELS']
ncolumns = data['NUM_DARK_COLUMNS']
for amp, npix, ncol in zip(amps, npixels, ncolumns):
    results.append(lcatr.schema.valid(lcatr.schema.get('dark_defects'),
                                      amp=amp,
                                      dark_pixels=npix,
                                      dark_columns=ncol))
results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
