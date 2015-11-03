#!/usr/bin/env python
import glob
import lsst.eotest.sensor as sensorTest
import lcatr.schema
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
ccd_vendor = siteUtils.getCcdVendor()

det_resp_data = '%s_det_response.fits' % sensor_id
eotestUtils.addHeaderData(det_resp_data, LSST_NUM=sensor_id, TESTTYPE='FLAT',
                          DATE=eotestUtils.utc_now_isoformat(),
                          CCD_MANU=siteUtils.getCcdVendor().upper())
results = [lcatr.schema.fileref.make(det_resp_data)]

if ccd_vendor == 'ITL':
    # Persist detector response for special linearity dataset from ITL.
    det_resp_data = '%s_det_response_linearity.fits' % sensor_id
    eotestUtils.addHeaderData(det_resp_data, LSST_NUM=sensor_id, TESTTYPE='FLAT',
                              DATE=eotestUtils.utc_now_isoformat(),
                              CCD_MANU=siteUtils.getCcdVendor().upper())
    results = [lcatr.schema.fileref.make(det_resp_data)]

results_file = '%s_eotest_results.fits' % sensor_id
data = sensorTest.EOTestResults(results_file)
amps = data['AMP']
full_well_data = data['FULL_WELL']
max_frac_dev_data = data['MAX_FRAC_DEV']

for amp, full_well, max_frac_dev in zip(amps, full_well_data,
                                        max_frac_dev_data):
    results.append(lcatr.schema.valid(lcatr.schema.get('flat_pairs'),
                                      amp=amp, full_well=full_well,
                                      max_frac_dev=max_frac_dev))
results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
