#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import lcatr.schema
import siteUtils

sensor_id = siteUtils.getUnitId()
results_file = '%s_eotest_results.fits' % sensor_id
data = sensorTest.EOTestResults(results_file)
amps = data['AMP']
cti_serial_data = data['CTI_SERIAL']
cti_parallel_data = data['CTI_PARALLEL']
results = []
for amp, scti, pcti in zip(amps, cti_serial_data, cti_parallel_data):
    results.append(lcatr.schema.valid(lcatr.schema.get('cte'),
                                      amp=amp, cti_serial=scti,
                                      cti_parallel=pcti))
results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
