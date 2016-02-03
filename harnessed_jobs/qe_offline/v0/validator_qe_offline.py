#!/usr/bin/env python
import glob
from collections import OrderedDict
import numpy as np
import pyfits
import lcatr.schema
import siteUtils
import eotestUtils

results = [eotestUtils.eotestCalibrations()]
results.extend(siteUtils.jobInfo())

sensor_id = siteUtils.getUnitId()
qe_data = pyfits.open('%s_QE.fits' % sensor_id)['QE_BANDS'].data
QE = OrderedDict((band, []) for band in qe_data.field('BAND'))
for amp in range(1, 17):
    values = qe_data.field('AMP%02i' % amp)
    for band, value in zip(QE, values):
        QE[band].append(value)

for band in QE:
    results.append(lcatr.schema.valid(lcatr.schema.get('qe_analysis'),
                                      band=band, QE=np.mean(QE[band])))

qe_files = glob.glob('*QE*.*')
for item in qe_files:
    if item.endswith('.fits'):
        eotestUtils.addHeaderData(item, LSST_NUM=sensor_id, TESTTYPE='LAMBDA',
                                  DATE=eotestUtils.utc_now_isoformat(),
                                  CCD_MANU=siteUtils.getCcdVendor().upper())
results.extend([lcatr.schema.fileref.make(item) for item in qe_files])

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
