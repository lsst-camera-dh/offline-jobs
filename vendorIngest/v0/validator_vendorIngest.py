#!/usr/bin/env python
import os
import sys
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
        failures = OrderedDict()
        analyses = ('fe55_analysis', 'read_noise', 'bright_defects',
                    'dark_defects', 'traps', 'dark_current', 'cte',
                    'prnu', 'flat_pairs', 'ptc', 'qe_analysis', 'metrology')
        for analysis in analyses:
            try:
                exec('my_results = self.%s()' % analysis)
                results.extend(my_results)
            except Exception, eobj:
                failures[analysis] = eobj
        if failures:
            print
            print "Failed to extract vendor results for the following:"
            for analysis, eobj in failures.items():
                print "%s: %s, %s" % (analysis, type(eobj), eobj)
            print
        sys.stdout.flush()
        return results

class ItlResults(VendorResults):
    file_end_mapping = {'fe55_analysis' : 'fe55.txt',
                        'bright_defects' : 'brightdefects.txt',
                        'dark_defects' : 'darkdefects.txt',
                        'dark_current' : 'dark.txt',
                        'read_noise' : 'gain.txt',
                        'cte_low' : 'eper1.txt',
                        'cte_high' : 'eper2.txt',
                        'traps' : 'traps.txt',
                        'flat_pairs' : 'linearity.txt',
                        'prnu' : 'prnu.txt',
                        'qe_analysis' : 'qe.txt',
                        'metrology' : 'metrology.txt'}
    def __init__(self, rootdir):
        super(ItlResults, self).__init__()
        command = 'find %(rootdir)s/ -name \*.txt -print' % locals()
        text_files = subprocess.check_output(command, shell=True).split()
        print "Found ITL results files:"
        for item in text_files:
            print "  ", item
        self.inverse_mapping = dict([(os.path.basename(path), path) for path
                                     in text_files])
        self._configs = {}
    def __getitem__(self, key):
        if not self._configs.has_key(key):
            self._configs[key] = ConfigParser.ConfigParser()
            file_ending = self.file_end_mapping[key]
            for item in self.inverse_mapping.values():
                if item.endswith(file_ending):
                    target = os.path.basename(item)
                    break
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
                                    gain_error=0,
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
        defects = dict(self[job].items('BrightRejection'))
        print """
        For the bright defects results, ITL only provides the total
        number of rejected pixels, so set all of these to be
        bright_pixels in amp 1 and set everything else to zero.
        """
        total_rejected = int(defects['brightrejectedpixels'])
        results = [validate(job, amp=1, bright_pixels=total_rejected,
                            bright_columns=0)]
        for amp in self.amps:
            if amp == 1:
                continue
            results.append(validate(job, amp=amp,
                                    bright_pixels=0, bright_columns=0))
        return results
    def dark_defects(self):
        job = 'dark_defects'
        defects = dict(self[job].items('DarkRejection'))
        print """
        For the dark defects results, ITL only provides the total
        number of rejected pixels, so set all of these to be
        dark_pixels in amp 1 and set everything else to zero.
        """
        total_rejected = int(defects['darkrejectedpixels'])
        results = [validate(job, amp=1, dark_pixels=total_rejected,
                            dark_columns=0)]
        for amp in self.amps:
            if amp == 1:
                continue
            results.append(validate(job, amp=amp,
                                    dark_pixels=0, dark_columns=0))
        return results
    def traps(self):
        job = 'traps'
        results = []
        for amp in self.amps:
            results.append(validate(job, amp=amp, num_traps=-1))
        return results
    def dark_current(self):
        job = 'dark_current'
        dc = dict(self[job].items('DarkSignal'))
        print """
        For the dark current results, ITL only provides CCD-wide
        numbers for the current at any given percentile, so set all
        amps to have this same value.
        """
        # Need to loop through DarkFrac# entries to find the 95th 
        # percentile value.
        index = None
        for key in dc:
            if key.startswith('darkfrac') and float(dc[key]) == 95.:
                index = key[len('darkfrac'):]
        if index is not None:
            dc_value = float(dc['darkrate'+index])
        else:
            dc_value = -1  # ugly sentinel value
        results = []
        for amp in self.amps:
            results.append(validate(job, amp=amp, dark_current_95CL=dc_value))
        return results
    def cte(self):
        job = 'cte_low'
        scte_low = dict(self[job].items('HCTE'))
        pcte_low = dict(self[job].items('VCTE'))
        job = 'cte_high'
        scte_high = dict(self[job].items('HCTE'))
        pcte_high = dict(self[job].items('VCTE'))
        results = []
        for amp in self.amps:
            ext = '%02i' % (amp - 1)
            results.append(validate('cte_vendorIngest', amp=amp,
                                    cti_low_serial=1.-float(scte_low['hcte_%s' % ext]),
                                    cti_low_parallel=1.-float(pcte_low['vcte_%s' % ext]),
                                    cti_high_serial=1.-float(scte_high['hcte_%s' % ext]),
                                    cti_high_parallel=1.-float(pcte_high['vcte_%s' % ext])))
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
                tokens = [float(x.strip()) for x in value.split()[:2]]
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
    def metrology(self):
        job = 'metrology'
        test_results = {}
        test_results['mounting_grade'] = dict(self[job].items('Mounting'))['grade']
        kwds = dict(self[job].items('Height'))
        test_results['height_grade'] = kwds['grade']
        kwds.update(dict(self[job].items('Flatness')))
        test_results['flatness_grade'] = kwds['grade']
        schema_keys = 'znom zmean zmedian zsdev flatnesshalfband flatnessfullband fsdev fmin fmax'.split()
        # Omit key/value pairs not in the schema.
        for key in schema_keys:
            test_results[key] = kwds[key]
        results = [validate('metrology_vendorIngest', **test_results)]
        return results

class e2vResults(VendorResults):
    def __init__(self, rootdir):
        self.rootdir = rootdir.replace(' ', '\ ')
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
                                    gain_error=0,
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
        scti_low, pcti_low, scti_high, pcti_high = {}, {}, {}, {}
        for amp, tokens in self._csv_data('CTE\*Optical\*Low_Summary.csv'):
            pcti_low[amp] = 1. - float(tokens[0])
            scti_low[amp] = 1. - float(tokens[1])
        for amp, tokens in self._csv_data('CTE\*Optical\*High_Summary.csv'):
            pcti_high[amp] = 1. - float(tokens[0])
            scti_high[amp] = 1. - float(tokens[1])
        for amp in self.amps:
            results.append(validate(job, amp=amp,
                                    cti_low_serial=scti_low[amp],
                                    cti_low_parallel=pcti_low[amp],
                                    cti_high_serial=scti_high[amp],
                                    cti_high_parallel=pcti_high[amp]))
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
#                wls = [float(x.strip()) for x in tokens[1:]]
                wls = []
                for item in tokens[1:]:
                    try:
                        wls.append(float(item.strip()))
                    except:
                        wls.append(None)
            else:
#                values = [float(x.strip()) for x in tokens[1:]]
                values = []
                for item in tokens[1:]:
                    try:
                        values.append(float(item.strip()))
                    except:
                        values.append(None)
                for wl, value in zip(wls, values):
                    for band, wl_range in self.qe_band_passes.items():
                        if (wl is not None and
                            value is not None and
                            wl >= wl_range[0] and 
                            wl <= wl_range[1]):
                            qe_results[band].append(value)
        results = []
        for band in qe_results:
            results.append(validate(job, band=band,
                                    QE=np.average(qe_results[band])))
        return results
    def metrology(self):
        return []

if __name__ == '__main__':
    results = [siteUtils.packageVersions()]

    lsstnum = siteUtils.getUnitId()

    vendorDataDir = os.readlink('vendorData')
    print 'Vendor data location:', vendorDataDir

    if siteUtils.getCcdVendor() == 'ITL':
        vendor = ItlResults(vendorDataDir)
        translator = ItlFitsTranslator(lsstnum, vendorDataDir, '.')
    else:
        vendor = e2vResults(vendorDataDir)
        translator = e2vFitsTranslator(lsstnum, vendorDataDir, '.')

    results.extend(vendor.run_all())

    translator.run_all()
    results.extend([lcatr.schema.fileref.make(x) for x in translator.outfiles])

    lcatr.schema.write_file(results)
    lcatr.schema.validate_file()
