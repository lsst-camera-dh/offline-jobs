#!/usr/bin/env python
import os
import subprocess
from collections import OrderedDict
import numpy as np
import ConfigParser
import lcatr.schema
import siteUtils
from vendorFitsTranslators import ItlFitsTranslator, e2vFitsTranslator

def validate(schema, **kwds):
    return lcatr.schema.valid(lcatr.schema.get(schema), **kwds)

class VendorResults(object):
    amps = range(1, 17)
    qe_band_passes = dict([('u', (321, 391)),
                           ('g', (402, 552)),
                           ('r', (552, 691)),
                           ('i', (691, 818)),
                           ('z', (818, 922)),
                           ('y', (930, 1070))])
    def __init__(self):
        pass
    def run_all(self):
        results = []
        results.extend(self.fe55_analysis())
        results.extend(self.read_noise())
        results.extend(self.bright_defects())
        results.extend(self.dark_defects())
        results.extend(self.traps())
        results.extend(self.dark_current())
        results.extend(self.cte())
        results.extend(self.prnu())
        results.extend(self.flat_pairs())
        results.extend(self.ptc())
        results.extend(self.qe_analysis())
        return results

class ItlResults(VendorResults):
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
        super(ItlResults, self).__init__()
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
    def fe55_analysis(self):
        job = 'fe55_analysis'
        gains = dict(self[job].items('SystemGain'))
        results = []
        for amp in self.amps:
            ext = '%02i' % (amp - 1)
            amp_catalog = dict(self[job].items('Events Channel %s' % ext))
            results.append(validate(job, amp=amp,
                                    gain=gains['gain_%s' % ext],
                                    psf_sigma=amp_catalog['meansigma']))
        return results
    def read_noise(self):
        job = 'read_noise'
        noise = dict(self[job].items('Noise'))
        results = []
        for amp in self.amps:
            ext = '%02i' % (amp - 1)
            read_noise = float(noise['noise_%s' % ext])
            system_noise = 0
            total_noise = np.sqrt(read_noise**2 + system_noise**2)
            results.append(validate(job, amp=amp,
                                    read_noise=read_noise,
                                    system_noise=system_noise,
                                    total_noise=total_noise))
        return results
    def bright_defects(self):
        job = 'bright_defects'
        results = []
        for amp in self.amps:
            results.append(validate(job, amp=amp,
                                    bright_pixels=0, bright_columns=0))
        return results
    def dark_defects(self):
        job = 'dark_defects'
        results = []
        for amp in self.amps:
            results.append(validate(job, amp=amp,
                                    dark_pixels=0, dark_columns=0))
        return results
    def traps(self):
        job = 'traps'
        results = []
        for amp in self.amps:
            results.append(validate(job, amp=amp, num_traps=0))
        return results
    def dark_current(self):
        job = 'dark_current'
        results = []
        for amp in self.amps:
            results.append(validate(job, amp=amp, dark_current_95CL=0))
        return results
    def cte(self):
        job = 'cte'
        scte = dict(self[job].items('HCTE'))
        pcte = dict(self[job].items('VCTE'))
        results = []
        for amp in self.amps:
            ext = '%02i' % (amp - 1)
            results.append(validate(job, amp=amp,
                                    cti_serial=1.-float(scte['hcte_%s' % ext]),
                                    cti_parallel=1.-float(pcte['vcte_%s' % ext])))
        return results
    def prnu(self):
        job = 'prnu'
        prnu = dict(self[job].items('PRNU'))
        results = []
        for value in prnu.values():
            tokens = value.split()
            if tokens[0].startswith('Wavelength'):
                continue
            wavelength = int(tokens[0])
            prnu_percent = float(tokens[1])
            results.append(validate(job, wavelength=wavelength,
                                    pixel_stdev=prnu_percent,
                                    pixel_mean=100.))
        return results
    def flat_pairs(self):
        job = 'flat_pairs'
        residuals = dict(self[job].items('Residuals'))
        max_frac_devs = dict((amp, 0) for amp in self.amps)
        full_wells = dict((amp, 0) for amp in self.amps)
        for key, value in residuals.items():
            if key.startswith('residuals'):
                devs = [float(x.strip())/100. for x in value.split()]
                for amp, dev in zip(self.amps, devs):
                    if (np.abs(dev) > max_frac_devs[amp]):
                        max_frac_devs[amp] = np.abs(dev)
        results = []
        for amp in self.amps:
            results.append(validate(job, amp=amp,
                                    full_well=full_wells[amp],
                                    max_frac_dev=max_frac_devs[amp]))
        return results
    def ptc(self):
        return []
    def qe_analysis(self):
        job = 'qe_analysis'
        qe_data = dict(self[job].items('QE'))
        qe_results = dict((band, []) for band in self.qe_band_passes)
        for key, value in qe_data.items():
            if key.startswith('qe'):
                tokens = [float(x.strip()) for x in value.split()]
                wl = tokens[0]
                qe = tokens[1]
                for band, wl_range in self.qe_band_passes.items():
                    if wl >= wl_range[0] and wl <= wl_range[1]:
                        qe_results[band].append(qe)
        results = []
        for band in qe_results:
            results.append(validate(job, band=band,
                                    QE=np.average(qe_results[band])))
        return results

class e2vResults(VendorResults):
    def __init__(self, rootdir):
        self.rootdir = rootdir
    def _csv_data(self, *args, **kwds):
        amp_data = {}
        subpath = os.path.join(*args)
        command = 'find %s/ -name %s -print' % (self.rootdir, subpath)
        results = subprocess.check_output(command, shell=True)
        csv_file = sorted(results.split('\n')[:-1])[0]
        try:
            label = kwds['label']
        except KeyError:
            label = 'Amp'
        for line in open(csv_file, 'r'):
            tokens = line.split(',')
            if tokens[0] == label:
                continue
            amp = int(tokens[0])
            amp_data[amp] = [x.strip() for x in tokens[1:]]
        return amp_data.items()
    def fe55_analysis(self):
        job = 'fe55_analysis'
        gains = {}
        psf_sigmas = {}
        for amp, tokens in self._csv_data('Gain\*X-Ray\*_Summary.csv'):
            gains[amp] = float(tokens[0])
        for amp, tokens in self._csv_data('PSF\*_Summary.csv'):
            psf_sigmas[amp] = float(tokens[0])
        results = []
        for amp in self.amps:
            results.append(validate(job, amp=amp, gain=gains[amp],
                                    psf_sigma=psf_sigmas[amp]))
        return results
    def read_noise(self):
        job = 'read_noise'
        results = []
        for amp, tokens in self._csv_data('Noise\*Multiple\*Samples\*Summary.csv'):
            read_noise = float(tokens[1])
            total_noise = float(tokens[3])
            system_noise = np.sqrt(total_noise**2 - read_noise**2)
            results.append(validate(job, amp=amp, read_noise=read_noise,
                                    system_noise=system_noise,
                                    total_noise=total_noise))
        return results
    def bright_defects(self):
        job = 'bright_defects'
        results = []
        for amp, tokens in self._csv_data('Darkness_Summary.csv'):
            bright_pixels = int(tokens[1])
            bright_columns = int(tokens[3])
            results.append(validate(job, amp=amp, bright_pixels=bright_pixels,
                                    bright_columns=bright_columns))
        return results
    def dark_defects(self):
        job = 'dark_defects'
        results = []
        for amp, tokens in self._csv_data('PRDefs_Summary.csv'):
            dark_pixels = int(tokens[-2])
            dark_columns = int(tokens[-3])
            results.append(validate(job, amp=amp, dark_pixels=dark_pixels,
                                    dark_columns=dark_columns))
        return results
    def traps(self):
        job = 'traps'
        results = []
        for amp, tokens in self._csv_data('TrapsPP_Summary.csv'):
            num_traps = int(tokens[0])
            results.append(validate(job, amp=amp, num_traps=num_traps))
        return results
    def dark_current(self):
        job = 'dark_current'
        results = []
        for amp, tokens in self._csv_data('Darkness_Summary.csv'):
            dark_current = float(tokens[0])
            results.append(validate(job, amp=amp, 
                                    dark_current_95CL=dark_current))
        return results
    def cte(self):
        job = 'cte'
        results = []
        for amp, tokens in self._csv_data('CTE\*Optical\*Summary.csv'):
            cti_parallel = 1. - float(tokens[0])
            cti_serial = 1. - float(tokens[1])
            results.append(validate(job, amp=amp, cti_serial=cti_serial,
                                    cti_parallel=cti_parallel))
        return results
    def prnu(self):
        job = 'prnu'
        results = []
        for wl, tokens in self._csv_data('PRNU_Summary.csv',
                                         label='Wavelength'):
            prnu_percent = float(tokens[0])
            results.append(validate(job, wavelength=wl,
                                    pixel_stdev=prnu_percent, pixel_mean=100))
        return results
    def flat_pairs(self):
        job = 'flat_pairs'
        results = []
        for amp, tokens in self._csv_data('FWC\*Multiple\*Image\*Summary.csv'):
            full_well = float(tokens[0])
            max_frac_dev = float(tokens[1])
            results.append(validate(job, amp=amp,
                                    full_well=full_well,
                                    max_frac_dev=max_frac_dev))
        return results
    def ptc(self):
        return []
    def qe_analysis(self):
        job = 'qe_analysis'
        subpath = 'QE_Summary.csv'
        command = 'find %s/ -name %s -print' % (self.rootdir, subpath)
        find_results = subprocess.check_output(command, shell=True)
        csv_file = find_results.split('\n')[0]
        qe_results = dict((band, []) for band in self.qe_band_passes)
        for line in open(csv_file):
            tokens = line.split(',')
            if tokens[0] == 'Amp':
                wls = [float(x.strip()) for x in tokens[1:]]
            else:
                values = [float(x.strip()) for x in tokens[1:]]
                for wl, value in zip(wls, values):
                    for band, wl_range in self.qe_band_passes.items():
                        if wl >= wl_range[0] and wl <= wl_range[1]:
                            qe_results[band].append(value)
        results = []
        for band in qe_results:
            results.append(validate(job, band=band,
                                    QE=np.average(qe_results[band])))
        return results

if __name__ == '__main__':
    results = [siteUtils.packageVersions()]

    vendorDataDir = os.readlink('vendorData')
    print 'Vendor data location:', vendorDataDir

    if siteUtils.getCcdVendor() == 'ITL':
        vendor = ItlResults(vendorDataDir)
        translator = ItlFitsTranslator(vendorDataDir, '.')
    else:
        vendor = e2vResults(vendorDataDir)
        translator = e2vFitsTranslator(vendorDataDir, '.')

    results.extend(vendor.run_all())

    translator.run_all()
    results.extend([lcatr.schema.fileref.make(x) for x in translator.outfiles])

    lcatr.schema.write_file(results)
    lcatr.schema.validate_file()
