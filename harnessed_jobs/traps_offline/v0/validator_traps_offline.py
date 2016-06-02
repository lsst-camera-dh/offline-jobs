#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import lcatr.schema
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()

trap_file = '%s_traps.fits' % sensor_id
eotestUtils.addHeaderData(trap_file, LSST_NUM=sensor_id, TESTTYPE='TRAP',
                          DATE=eotestUtils.utc_now_isoformat(),
                          CCD_MANU=siteUtils.getCcdVendor().upper())
results = [lcatr.schema.fileref.make(trap_file)]

mask_file = '%s_traps_mask.fits' % sensor_id
results.append(lcatr.schema.fileref.make(mask_file))

results_file = '%s_eotest_results.fits' % sensor_id
data = sensorTest.EOTestResults(results_file)
amps = data['AMP']
num_traps = data['NUM_TRAPS']

for amp, ntrap in zip(amps, num_traps):
    results.append(lcatr.schema.valid(lcatr.schema.get('traps'),
                                      amp=amp, num_traps=ntrap))

results.extend(siteUtils.jobInfo())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
