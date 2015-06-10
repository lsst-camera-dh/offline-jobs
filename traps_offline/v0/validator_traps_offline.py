#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import lcatr.schema
import siteUtils

sensor_id = siteUtils.getUnitId()

trap_file = '%s_traps.fits' % sensor_id
results = [lcatr.schema.fileref.make(trap_file)]

results_file = '%s_eotest_results.fits' % sensor_id
data = sensorTest.EOTestResults(results_file)
amps = data['AMP']
num_traps = data['NUM_TRAPS']

for amp, ntrap in zip(amps, num_traps):
    results.append(lcatr.schema.valid(lcatr.schema.get('traps'),
                                      amp=amp, num_traps=ntrap)), 

results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
