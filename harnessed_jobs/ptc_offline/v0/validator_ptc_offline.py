#!/usr/bin/env python
import sys
import lsst.eotest.sensor as sensorTest
import lcatr.schema
import siteUtils
import eotestUtils

if siteUtils.getCcdVendor() in ('e2v', 'E2V'):
    # Effectively do nothing since e2v does not provide pairs of flats.
    lcatr.schema.write_file([])
    lcatr.schema.validate_file()
    sys.exit(0)

sensor_id = siteUtils.getUnitId()
ptc_results = '%s_ptc.fits' % sensor_id
eotestUtils.addHeaderData(ptc_results, LSST_NUM=sensor_id, TESTTYPE='FLAT',
                          DATE=eotestUtils.utc_now_isoformat(),
                          CCD_MANU=siteUtils.getCcdVendor().upper())

results = [lcatr.schema.fileref.make(ptc_results)]

results_file = '%s_eotest_results.fits' % sensor_id
data = sensorTest.EOTestResults(results_file)
amps = data['AMP']
ptc_gains = data['PTC_GAIN']
ptc_gain_errors = data['PTC_GAIN_ERROR']
for amp, gain, gain_error in zip(amps, ptc_gains, ptc_gain_errors):
    results.append(lcatr.schema.valid(lcatr.schema.get('ptc_offline'),
                                      amp=amp, ptc_gain=gain,
                                      ptc_gain_error=gain_error))

results.extend(siteUtils.jobInfo())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
