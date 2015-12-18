#!/usr/bin/env python
import numpy as np
import pyfits
import lcatr.schema
import siteUtils

sensor_id = siteUtils.getUnitId()

results_file = '%s_eotest_results.fits' % sensor_id
prnu_results = pyfits.open(results_file)['PRNU_RESULTS'].data

results = []
for wl, stdev, mean in zip(prnu_results['WAVELENGTH'], 
                           prnu_results['STDEV'], prnu_results['MEAN']):
    results.append(lcatr.schema.valid(lcatr.schema.get('prnu'),
                                      wavelength=int(np.round(wl)), 
                                      pixel_stdev=stdev, pixel_mean=mean))
results.append(siteUtils.packageVersions())

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
