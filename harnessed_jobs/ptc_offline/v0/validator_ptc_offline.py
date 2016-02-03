#!/usr/bin/env python
import lcatr.schema
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
ptc_results = '%s_ptc.fits' % sensor_id
eotestUtils.addHeaderData(ptc_results, LSST_NUM=sensor_id, TESTTYPE='FLAT',
                          DATE=eotestUtils.utc_now_isoformat(),
                          CCD_MANU=siteUtils.getCcdVendor().upper())

results = [lcatr.schema.fileref.make(ptc_results)]
results.extend(siteUtils.jobInfo())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
