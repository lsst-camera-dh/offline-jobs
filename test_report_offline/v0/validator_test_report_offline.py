#!/usr/bin/env python
import glob
import lcatr.schema
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
results_file = '%s_eotest_results.fits' % sensor_id
eotestUtils.addHeaderData(results_file, LSST_NUM=sensor_id,
                          DATE=eotestUtils.utc_now_isoformat(),
                          CCD_MANU=siteUtils.getCcdVendor().upper())
results = [lcatr.schema.fileref.make(results_file)]

png_files = glob.glob('*.png')
results.extend([lcatr.schema.fileref.make(item) for item in png_files])

test_report = '%s_eotest_report.pdf' % sensor_id
results.append(lcatr.schema.fileref.make(test_report))

results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
