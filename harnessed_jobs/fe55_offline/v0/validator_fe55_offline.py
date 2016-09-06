#!/usr/bin/env python
import glob
import lsst.eotest.sensor as sensorTest
import lcatr.schema
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()

# The output files from producer script.
gain_file = '%(sensor_id)s_eotest_results.fits' % locals()
psf_results = glob.glob('%(sensor_id)s_psf_results*.fits' % locals())[0]
rolloff_mask = '%(sensor_id)s_rolloff_defects_mask.fits' % locals()

output_files = gain_file, psf_results, rolloff_mask

# Add/update the metadata to the primary HDU of these files.
for fitsfile in output_files:
    eotestUtils.addHeaderData(fitsfile, LSST_NUM=sensor_id, TESTTYPE='FE55',
                              DATE=eotestUtils.utc_now_isoformat(),
                              CCD_MANU=siteUtils.getCcdVendor().upper())

results = []
#
# Persist the mean bias FITS file, if it exists
#
try:
    bias_mean_file = glob.glob('%(sensor_id)s_mean_bias_*.fits' % locals())[0]
    results.append(lcatr.schema.fileref.make(bias_mean_file))
except IndexError:
    pass
#
# Common metadata for persisted non-FITS files.
#
md = siteUtils.DataCatalogMetadata(CCD_MANU=siteUtils.getCcdVendor(),
                                   LSST_NUM=sensor_id,
                                   producer='SR-EOT-02',
                                   TESTTYPE='FE55',
                                   TEST_CATEGORY='EO')
#
# Persist various png files.
#
png_files = glob.glob('%(sensor_id)s_fe55*.png' % locals())
png_filerefs = []
for png_file in png_files:
    dp = png_file[len(sensor_id) + 1:-len('.png')]
    png_filerefs.append(lcatr.schema.fileref.make(png_file,
                                                  metadata=md(DATA_PRODUCT=dp)))
results.extend(png_filerefs)

data = sensorTest.EOTestResults(gain_file)
amps = data['AMP']
gain_data = data['GAIN']
gain_errors = data['GAIN_ERROR']
sigmas = data['PSF_SIGMA']
for amp, gain_value, gain_error, sigma in zip(amps, gain_data, gain_errors,
                                              sigmas):
    results.append(lcatr.schema.valid(lcatr.schema.get('fe55_analysis'),
                                      amp=amp, gain=gain_value,
                                      gain_error=gain_error,
                                      psf_sigma=sigma))

results.extend(siteUtils.jobInfo())

results.extend([lcatr.schema.fileref.make(x) for x in output_files])

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
