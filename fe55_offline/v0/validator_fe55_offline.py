#!/usr/bin/env python
import glob
import lsst.eotest.sensor as sensorTest
import lcatr.schema
import siteUtils

sensor_id = siteUtils.getUnitId()

# The output files from producer script.
gain_file = '%(sensor_id)s_eotest_results.fits' % locals()
psf_results = glob.glob('%(sensor_id)s_psf_results*.fits' % locals())[0]
rolloff_mask = '%(sensor_id)s_rolloff_defects_mask.fits' % locals()

results = []

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

results.append(siteUtils.packageVersions())

results.extend([lcatr.schema.fileref.make(x) for x in 
                (psf_results, gain_file, rolloff_mask)])

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
