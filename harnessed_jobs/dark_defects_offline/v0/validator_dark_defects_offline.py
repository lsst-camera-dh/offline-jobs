#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import lcatr.schema
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()

mask_file = '%s_dark_pixel_mask.fits' % sensor_id
eotestUtils.addHeaderData(mask_file, LSST_NUM=sensor_id, TESTTYPE='SFLAT_500',
                          DATE=eotestUtils.utc_now_isoformat(),
                          CCD_MANU=siteUtils.getCcdVendor().upper())
results = [lcatr.schema.fileref.make(mask_file)]

superflat = '%s_median_sflat.fits' % sensor_id
eotestUtils.addHeaderData(superflat, DATE=eotestUtils.utc_now_isoformat())
results.append(lcatr.schema.fileref.make(superflat))

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
results.extend(siteUtils.jobInfo())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
