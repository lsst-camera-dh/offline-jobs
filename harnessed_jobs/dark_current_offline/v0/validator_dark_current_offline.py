#!/usr/bin/env python
import glob
import lsst.eotest.sensor as sensorTest
import lcatr.schema
import siteUtils

sensor_id = siteUtils.getUnitId()

results_file = '%s_eotest_results.fits' % sensor_id
data = sensorTest.EOTestResults(results_file)

results = []
amps = data['AMP']
dc95s = data['DARK_CURRENT_95']
for amp, dc95 in zip(amps, dc95s):
    results.append(lcatr.schema.valid(lcatr.schema.get('dark_current'),
                                      amp=amp, dark_current_95CL=dc95))

results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
