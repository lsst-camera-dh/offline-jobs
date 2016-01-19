#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import lcatr.schema
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()

mask_file = '%s_bright_pixel_mask.fits' % sensor_id
eotestUtils.addHeaderData(mask_file, LSST_NUM=sensor_id, TESTTYPE='DARK',
                          DATE=eotestUtils.utc_now_isoformat(),
                          CCD_MANU=siteUtils.getCcdVendor().upper())
results = [lcatr.schema.fileref.make(mask_file)]

medianed_dark = '%s_median_dark_bp.fits' % sensor_id
eotestUtils.addHeaderData(medianed_dark, DATE=eotestUtils.utc_now_isoformat())
results.append(lcatr.schema.fileref.make(medianed_dark))

eotest_results = '%s_eotest_results.fits' % sensor_id
data = sensorTest.EOTestResults(eotest_results)
amps = data['AMP']
npixels = data['NUM_BRIGHT_PIXELS']
ncolumns = data['NUM_BRIGHT_COLUMNS']
for amp, npix, ncol in zip(amps, npixels, ncolumns):
    results.append(lcatr.schema.valid(lcatr.schema.get('bright_defects'),
                                      amp=amp,
                                      bright_pixels=npix,
                                      bright_columns=ncol))
results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
