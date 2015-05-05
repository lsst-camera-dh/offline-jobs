#!/usr/bin/env python
import os
import subprocess
import ConfigParser
import lcatr.schema

def validate(schema, **kwds):
    return lcatr.schema.valid(lcatr.schema.get(schema), **kwds)

class ItlResults(object):
    file_mapping = {'fe55_analysis' : 'fe55.txt',
                    'bright_defects' : 'brightdefects.txt',
                    'dark_defects' : 'darkdefects.txt',
                    'dark_current' : 'dark.txt',
                    'read_noise' : 'gain.txt',
                    'cte' : 'eper1.txt',
                    'traps' : 'traps.txt',
                    'flat_pairs' : 'linearity.txt',
                    'prnu' : 'prnu.txt',
                    'qe_analysis' : 'qe.txt'}
    def __init__(self, rootdir):
        command = 'find %(rootdir)s -name \*.txt -print' % locals()
        text_files = subprocess.check_output(command, shell=True).split()
        self.inverse_mapping = dict([(os.path.basename(path), path) for path
                                     in text_files])
        self._configs = {}
    def __getitem__(self, key):
        if not self._configs.has_key(key):
            self._configs[key] = ConfigParser.ConfigParser()
            target = self.file_mapping[key]
            self._configs[key].read(self.inverse_mapping[target])
        return self._configs[key]

dataTree = os.readlink('vendorData')
print 'Vendor data location:', dataTree

vendor = ItlResults(dataTree)

amps = range(1, 17)

results = []

for amp in amps:
    ext = '%02i' % (amp - 1)

    job = 'fe55_analysis'
    gains = dict(vendor[job].items('SystemGain'))
    amp_catalog = dict(vendor[job].items('Events Channel %s' % ext))
    results.append(validate(job, amp=amp,
                            gain=gains['gain_%s' % ext],
                            psf_sigma=amp_catalog['meansigma']))
    
    job = 'bright_defects'
    job = 'dark_defects'
    job = 'dark_current'

    job = 'read_noise'
    noise = dict(vendor[job].items('Noise'))
    results.append(validate(job, amp=amp,
                            read_noise=noise['noise_%s' % ext]))

    job = 'cte'
    scte = dict(vendor[job].items('HCTE'))
    pcte = dict(vendor[job].items('VCTE'))
    results.append(validate('cte', amp=amp,
                            cti_serial=1.-float(scte['hcte_%s' % ext]),
                            cti_parallel=1.-float(pcte['vcte_%s' % ext])))

    job = 'traps'
    job = 'linearity'

job = 'qe_analysis'

job = 'prnu'
prnu = dict(vendor[job].items('PRNU'))
for value in prnu.values():
    tokens = value.split()
    if tokens[0].startswith('Wavelength'):
        continue
    wavelength = int(tokens[0])
    prnu_percent = float(tokens[1])
    results.append(validate('vendorIngest', wavelength=wavelength,
                            prnu_percent=prnu_percent))

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
