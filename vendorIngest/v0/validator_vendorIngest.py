#!/usr/bin/env python
import glob
import lcatr.schema
import os

results = []
jobname="vendorIngest"
jobdir = "%s/share/%s/%s" % (os.environ["VIRTUAL_ENV"], jobname, os.environ["LCATR_VERSION"])

# Fetch pointer to new Vendor Data
dataTree = os.readlink('vendorData')
print ' Vendor data location: ',dataTree


## Jim take over from here -- ingest textual summary data from ITL




## Finish-up code from one of the examples
tsstat = 0
results.append(lcatr.schema.valid(lcatr.schema.get('vendorIngest'),stat=tsstat))

lcatr.schema.write_file(results)
lcatr.schema.validate_file()


# Done.
