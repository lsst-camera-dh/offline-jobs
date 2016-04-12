#!/usr/bin/env python
import glob
import lcatr.schema
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()

md = siteUtils.DataCatalogMetadata(CCD_MANU=siteUtils.getCcdVendor(),
                                   LSST_NUM=sensor_id,
                                   PRODUCER='SR-EOT-02',
                                   ORIGIN='SLAC',
                                   TEST_CATEGORY='EO')

results_file = '%s_eotest_results.fits' % sensor_id
eotestUtils.addHeaderData(results_file, LSST_NUM=sensor_id,
                          DATE=eotestUtils.utc_now_isoformat(),
                          CCD_MANU=siteUtils.getCcdVendor().upper())
results = [lcatr.schema.fileref.make(results_file,
                                     metadata=md(DATA_PRODUCT='EOTEST_RESULTS'))]

png_files = glob.glob('*.png')
results.extend([lcatr.schema.fileref.make(item,
                                          metadata=md(DATA_PRODUCT=eotestUtils.png_data_product(item, sensor_id)))
                for item in png_files])


test_report = '%s_eotest_report.pdf' % sensor_id
results.append(lcatr.schema.fileref.make(test_report,
                                         metadata=md(DATA_PRODUCT='EOTEST_REPORT')))

results.extend(siteUtils.jobInfo())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
