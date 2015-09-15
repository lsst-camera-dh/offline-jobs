#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import lcatr.schema
import siteUtils

sensor_id = siteUtils.getUnitId()
results_file = '%s_eotest_results.fits' % sensor_id
data = sensorTest.EOTestResults(results_file)
amps = data['AMP']
cti_high_serial = data['CTI_HIGH_SERIAL']
cti_high_parallel = data['CTI_HIGH_PARALLEL']
cti_low_serial = data['CTI_LOW_SERIAL']
cti_low_parallel = data['CTI_LOW_PARALLEL']
results = []
for amp, scti_h, pcti_h, scti_l, pcti_l in zip(amps,
                                               cti_high_serial, cti_high_parallel,
                                               cti_low_serial, cti_low_parallel):
    results.append(lcatr.schema.valid(lcatr.schema.get('cte'),
                                      amp=amp, cti_high_serial=scti_h,
                                      cti_high_parallel=pcti_h,
                                      cti_low_serial=scti_l,
                                      cti_low_parallel=pcti_l))
results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
