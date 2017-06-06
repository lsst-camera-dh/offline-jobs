#!/usr/bin/env python
"vendorIngest harnessed job validator script."
from __future__ import absolute_import, print_function
import os
import sys
import glob
import re
import fnmatch
import shutil
import subprocess
import datetime
from collections import OrderedDict
import ConfigParser
import numpy as np
import lcatr.schema
import siteUtils
import vendorDataUtils
from ItlFitsTranslator import ItlFitsTranslator
from e2vFitsTranslator import e2vFitsTranslator

__all__ = ['ItlResults', 'ITL_metrology_files', 'extract_ITL_metrology_date',
           'e2vResults', 'e2v_metrology_files']

def validate(schema, **kwds):
    "More compact call to lcatr.schema.valid"
    return lcatr.schema.valid(lcatr.schema.get(schema), **kwds)

class VendorResults(object):
    """
    Base class to process vendor results.
    """
    qe_band_passes = dict([('u', (321, 391)),
                           ('g', (402, 552)),
                           ('r', (552, 691)),
                           ('i', (691, 818)),
                           ('z', (818, 922)),
                           ('y', (930, 1070))])

    def __init__(self):
        "Constructor."
        self._amps = range(1, 17)

    def run_all(self):
        "Run all of the methods for each test type."
        results = []
        failures = OrderedDict()
        analyses = ('fe55_analysis', 'read_noise', 'bright_defects',
                    'dark_defects', 'traps', 'dark_current', 'cte',
                    'prnu', 'flat_pairs', 'ptc', 'qe_analysis', 'metrology')
        for analysis in analyses:
            try:
                exec('my_results = self.%s()' % analysis)
                results.extend(my_results)
            except Exception as eobj:
                failures[analysis] = eobj
        if failures:
            print("\nFailed to extract vendor results for the following:")
            for analysis, eobj in failures.items():
                print("%s: %s, %s" % (analysis, type(eobj), eobj))
            print("")
        sys.stdout.flush()
        return results

class ItlResults(VendorResults):
    "Class to process the ITL results."
    file_end_mapping = {'fe55_analysis' : 'fe55.txt',
                        'bright_defects' : 'brightdefects.txt',
                        'dark_defects' : 'darkdefects.txt',
                        'dark_current' : 'dark.txt',
                        'read_noise' : 'fe55.txt',
                        'cte_low' : 'eper1.txt',
                        'cte_high' : 'eper2.txt',
                        'traps' : 'traps.txt',
                        'flat_pairs' : 'linearity.txt',
                        'prnu' : 'prnu.txt',
                        'qe_analysis' : 'qe.txt',
                        'metrology' : 'metrology.txt'}
    def __init__(self, rootdir, verbose=True):
        """
        Constructor.
        rootdir = Top level directory containing all of the results files.
        """
        super(ItlResults, self).__init__()
        command = 'find %s/ -name \*.txt -print' % rootdir
        text_files = subprocess.check_output(command, shell=True).split()
        if verbose:
            print("Found ITL results files:")
            for item in text_files:
                print("  ", item)
        self.inverse_mapping = dict([(os.path.basename(path), path) for path
                                     in text_files])
        self._configs = {}

    def __getitem__(self, key):
        "Provide a dict-like interface to each .ini style subsection."
        if not self._configs.has_key(key):
            self._configs[key] = ConfigParser.ConfigParser()
            file_ending = self.file_end_mapping[key]
            for item in self.inverse_mapping.values():
                if item.endswith(file_ending):
                    target = os.path.basename(item)
                    break
            self._configs[key].read(self.inverse_mapping[target])
            # Set the number of amplifiers for this txt file based on
            # the [Info] section.
            info = dict(self._configs[key].items('Info'))
            try:
                self._amps = range(1, int(info['numchans']) + 1)
            except KeyError:
                pass
        return self._configs[key]

    def fe55_analysis(self):
        "Process the Fe55 analysis results."
        job = 'fe55_analysis'
        gains = dict(self[job].items('SystemGain'))
        results = []
        for amp in self._amps:
            ext = '%02i' % (amp - 1)
            amp_catalog = dict(self[job].items('Events Channel %s' % ext))
            results.append(validate(job, amp=amp,
                                    gain=gains['gain_%s' % ext],
                                    gain_error=0,
                                    psf_sigma=amp_catalog['meansigma']))
        return results

    def read_noise(self):
        "Process the read noise results."
        job = 'read_noise'
        noise = dict(self[job].items('ReadNoise'))
        results = []
        system_noise_data = {}
        for amp in self._amps:
            ext = '%02i' % (amp - 1)
            read_noise = float(noise['readnoise_%s' % ext])
            try:
                system_noise = float(noise['systemnoisecorrection_%s' % ext])
                system_noise_data[amp] = system_noise
            except KeyError:
                system_noise = 0.
            total_noise = np.sqrt(read_noise**2 + system_noise**2)
            results.append(validate(job, amp=amp,
                                    read_noise=read_noise,
                                    system_noise=system_noise,
                                    total_noise=total_noise))
        if system_noise_data:
            outfile = '%s_system_noise.txt' % siteUtils.getUnitId()
            with open(outfile, 'w') as output:
                output.write('# Amp    system noise (ADU rms)\n')
                for amp, system_noise in system_noise_data.items():
                    output.write('  %i        %f\n' % (amp, system_noise))
        return results

    def bright_defects(self):
        "Process the bright defects results."
        job = 'bright_defects'
        defects = dict(self[job].items('BrightRejection'))
        print("""
        For the bright defects results, ITL only provides the total
        number of rejected pixels, so set all of these to be
        bright_pixels in amp 1 and set everything else to zero.
        """)
        total_rejected = int(defects['brightrejectedpixels'])
        results = [validate(job, amp=1, bright_pixels=total_rejected,
                            bright_columns=0)]
        for amp in self._amps:
            if amp == 1:
                continue
            results.append(validate(job, amp=amp,
                                    bright_pixels=0, bright_columns=0))
        return results

    def dark_defects(self):
        "Process the dark defects results."
        job = 'dark_defects'
        defects = dict(self[job].items('DarkRejection'))
        print("""
        For the dark defects results, ITL only provides the total
        number of rejected pixels, so set all of these to be
        dark_pixels in amp 1 and set everything else to zero.
        """)
        total_rejected = int(defects['darkrejectedpixels'])
        results = [validate(job, amp=1, dark_pixels=total_rejected,
                            dark_columns=0)]
        for amp in self._amps:
            if amp == 1:
                continue
            results.append(validate(job, amp=amp,
                                    dark_pixels=0, dark_columns=0))
        return results

    def traps(self):
        "Process the traps results."
        job = 'traps'
        results = []
        for amp in self._amps:
            results.append(validate(job, amp=amp, num_traps=-1))
        return results

    def dark_current(self):
        "Process the dark current results."
        job = 'dark_current'
        dc = dict(self[job].items('DarkSignal'))
        print("""
        For the dark current results, ITL only provides CCD-wide
        numbers for the current at any given percentile, so set all
        amps to have this same value.
        """)
        # Need to loop through DarkFrac# entries to find the 95th
        # percentile value.
        index = None
        for key in dc:
            if key.startswith('darkfrac') and float(dc[key]) == 95.:
                index = key[len('darkfrac'):]
        if index is not None:
            dc_value = float(dc['darkrate'+index])
        else:
            dc_value = -1.  # ugly sentinel value
        results = []
        for amp in self._amps:
            results.append(validate(job, amp=amp, dark_current_95CL=dc_value))
        return results

    def cte(self):
        "Process the CTE results."
        job = 'cte_low'
        scte_low = dict(self[job].items('HCTE'))
        pcte_low = dict(self[job].items('VCTE'))
        job = 'cte_high'
        scte_high = dict(self[job].items('HCTE'))
        pcte_high = dict(self[job].items('VCTE'))
        results = []
        for amp in self._amps:
            ext = '%02i' % (amp - 1)
            results.append(validate('cte_vendorIngest', amp=amp,
                                    cti_low_serial=1.-float(scte_low['hcte_%s' % ext]),
                                    cti_low_parallel=1.-float(pcte_low['vcte_%s' % ext]),
                                    cti_high_serial=1.-float(scte_high['hcte_%s' % ext]),
                                    cti_high_parallel=1.-float(pcte_high['vcte_%s' % ext])))
        return results

    def prnu(self):
        "Process the PRNU results."
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
        "Process the flat pairs results."
        job = 'flat_pairs'
        residuals = dict(self[job].items('Residuals'))
        max_frac_devs = dict((amp, 0) for amp in self._amps)
        full_wells = dict((amp, 0) for amp in self._amps)
        for key, value in residuals.items():
            if key.startswith('residuals'):
                devs = [float(x.strip())/100. for x in value.split()]
                for amp, dev in zip(self._amps, devs):
                    if np.abs(dev) > max_frac_devs[amp]:
                        max_frac_devs[amp] = np.abs(dev)
        results = []
        for amp in self._amps:
            results.append(validate(job, amp=amp,
                                    full_well=full_wells[amp],
                                    max_frac_dev=max_frac_devs[amp]))
        return results

    def ptc(self):
        "Process the PTC results."
        return []

    def _qe_values(self, job='qe_analysis'):
        "Process the QE results."
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
        qe_values = {}
        for band in qe_results:
            # Multiply average QE values by 100. to convert them to
            # percentages.
            qe_values[band] = QE=100.*np.average(qe_results[band])
        return qe_values

    def qe_analysis(self):
        "Process the QE results."
        job = 'qe_analysis'
        qe_values = self._qe_values(job=job)
        results = []
        for band in qe_values:
            results.append(validate(job, band=band, QE=qe_values[band]))
        return results

    def _metrology_test_results(self, job='metrology'):
        "Process the metrology results."
        test_results = {}
        # Process [Mounting] section.
        try:
            test_results['mounting_grade'] \
                = dict(self[job].items('Mounting'))['grade']
        except KeyError:
            test_results['mounting_grade'] = 'N/A'
        # Process [Height] section.
        kwds = dict(self[job].items('Height'))
        try:
            test_results['height_grade'] = kwds['grade']
        except KeyError:
            test_results['height_grade'] = 'N/A'
        # Extract quantiles for contained fraction calculation.
        zvalues, quantiles = [], []
        for key, value in kwds.items():
            if key.startswith('zquan'):
                zvalues.append(float(value))
                quantiles.append(float(key.split('_')[1]))
        zvalues.sort()
        quantiles.sort()
        znom = float(kwds['znom'])
        test_results['frac_outside'] \
            = 1. - self.contained_fraction(zvalues, quantiles, znom)
        # Process [Flatness] section.
        kwds.update(dict(self[job].items('Flatness')))
        try:
            test_results['flatness_grade'] = kwds['grade']
        except KeyError:
            test_results['flatness_grade'] = 'N/A'
        # Fill in all of the schema values.
        schema = lcatr.schema.get('metrology_vendorIngest')
        sentinel_value = '-999'
        for key in schema.keys():
            if key in test_results or key in ('schema_name', 'schema_version'):
                continue
            test_results[key] = kwds.get(key, sentinel_value)
        return test_results

    @staticmethod
    def contained_fraction(zvalues, quantiles, znom, zbounds=(-0.009, 0.009)):
        """
        Compute the contained fraction within an interval given
        quantiles as a function of z.

        Parameters
        ----------
        zvalues : sequence of floats
            The abscissa values of the distribution.
        quantiles : sequence of floats
            The quantiles values corresponding to the zvalues.
        znom : float
            Reference value of the desired interval.
        zbounds : (float, float), optional
            Values of interval bounds referenced to znom.
            Default: (-0.009, 0.009)

        Returns
        -------
        float : The inferred fraction of the distribution lying outside
            the specified interval.
        """
        quant_low = np.interp(znom + zbounds[0], zvalues, quantiles)
        quant_high = np.interp(znom + zbounds[1], zvalues, quantiles)
        return (quant_high - quant_low)/100.

    def metrology(self):
        "Process the metrology results."
        test_results = self._metrology_test_results(job='metrology')
        results = [validate('metrology_vendorIngest', **test_results)]
        return results

class e2vResults(VendorResults):
    "Class to process e2v CCD results."
    def __init__(self, rootdir):
        """
        Constructor.
        rootdir = Top level directory containing all of the results files.
        """
        super(e2vResults, self).__init__()
        self.rootdir = rootdir.replace(' ', '\ ')

    def _csv_data(self, *args, **kwds):
        "Method to extract per amp data from csv file."
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
        "Process Fe55 results."
        job = 'fe55_analysis'
        gains = {}
        psf_sigmas = {}
        for amp, tokens in self._csv_data('\*Gain\*X-Ray\*_Summary\*.csv'):
            gains[amp] = float(tokens[0])
        for amp, tokens in self._csv_data('\*PSF\*_Summary\*.csv'):
            psf_sigmas[amp] = float(tokens[0])
        results = []
        for amp in self._amps:
            results.append(validate(job, amp=amp, gain=gains[amp],
                                    gain_error=0,
                                    psf_sigma=psf_sigmas[amp]))
        return results

    def read_noise(self):
        "Process the read noise results."
        job = 'read_noise'
        results = []
        system_noise_data = {}
        for amp, tokens in self._csv_data('\*Noise\*Multiple\*Samples\*Summary\*.csv'):
            read_noise = float(tokens[1])
            total_noise = float(tokens[3])
            system_noise = np.sqrt(total_noise**2 - read_noise**2)
            system_noise_data[amp] = system_noise
            results.append(validate(job, amp=amp, read_noise=read_noise,
                                    system_noise=system_noise,
                                    total_noise=total_noise))
        # Extract the system noise from the e2v x-ray image FITS file
        # and write to a text file for persisting by the eTraveler.
        xray_files = glob.glob(os.path.join(self.rootdir, '*_xray_xray_*.fits'))
        system_noise = vendorDataUtils.e2v_system_noise(xray_files[0])
        outfile = '%s_system_noise.txt' % siteUtils.getUnitId()
        with open(outfile, 'w') as output:
            output.write('# Amp    system noise (ADU rms)\n')
            for amp, value in system_noise.items():
                output.write('%i               %.6f\n' % (amp, value))
        return results

    def bright_defects(self):
        "Process the bright defects results."
        job = 'bright_defects'
        results = []
        for amp, tokens in self._csv_data('\*Darkness_Summary\*.csv'):
            bright_pixels = int(tokens[1])
            bright_columns = int(tokens[3])
            results.append(validate(job, amp=amp, bright_pixels=bright_pixels,
                                    bright_columns=bright_columns))
        return results

    def dark_defects(self):
        "Process the dark defects results."
        job = 'dark_defects'
        results = []
        for amp, tokens in self._csv_data('\*PRDefs_Summary\*.csv'):
            dark_pixels = int(tokens[-2])
            dark_columns = int(tokens[-3])
            results.append(validate(job, amp=amp, dark_pixels=dark_pixels,
                                    dark_columns=dark_columns))
        return results

    def traps(self):
        "Process the traps results."
        job = 'traps'
        results = []
        for amp, tokens in self._csv_data('\*TrapsPP_Summary\*.csv'):
            num_traps = int(tokens[0])
            results.append(validate(job, amp=amp, num_traps=num_traps))
        return results

    def dark_current(self):
        "Process the dark current results."
        job = 'dark_current'
        results = []
        for amp, tokens in self._csv_data('\*Darkness_Summary\*.csv'):
            dark_current = float(tokens[0])
            results.append(validate(job, amp=amp,
                                    dark_current_95CL=dark_current))
        return results

    def cte(self):
        "Process the CTE results."
        job = 'cte_vendorIngest'
        results = []
        scti_low, pcti_low, scti_high, pcti_high = {}, {}, {}, {}
        for amp, tokens in self._csv_data('\*CTE\*Optical\*Low_Summary\*.csv'):
            pcti_low[amp] = 1. - float(tokens[0])
            scti_low[amp] = 1. - float(tokens[1])
        for amp, tokens in self._csv_data('\*CTE\*Optical\*High_Summary\*.csv'):
            pcti_high[amp] = 1. - float(tokens[0])
            scti_high[amp] = 1. - float(tokens[1])
        for amp in self._amps:
            results.append(validate(job, amp=amp,
                                    cti_low_serial=scti_low[amp],
                                    cti_low_parallel=pcti_low[amp],
                                    cti_high_serial=scti_high[amp],
                                    cti_high_parallel=pcti_high[amp]))
        return results

    def prnu(self):
        "Process the PRNU results."
        job = 'prnu'
        results = []
        for wl, tokens in self._csv_data('\*PRNU_Summary\*.csv',
                                         label='Wavelength'):
            prnu_percent = float(tokens[0])
            results.append(validate(job, wavelength=wl,
                                    pixel_stdev=prnu_percent, pixel_mean=100))
        return results

    def flat_pairs(self):
        "Process the flat pairs results."
        job = 'flat_pairs'
        results = []
        for amp, tokens in self._csv_data('\*FWC\*Multiple\*Image\*Summary\*.csv'):
            full_well = float(tokens[0])
            # convert e2v number from percentages to fractions.
            max_frac_dev = float(tokens[1])/100.
            results.append(validate(job, amp=amp,
                                    full_well=full_well,
                                    max_frac_dev=max_frac_dev))
        return results

    def ptc(self):
        "Process the PTC results."
        return []

    def qe_analysis(self):
        "Process the QE results."
        job = 'qe_analysis'
        subpath = '\*QE_Summary\*.csv'
        command = 'find %s/ -name %s -print' % (self.rootdir, subpath)
        find_results = subprocess.check_output(command, shell=True)
        csv_file = find_results.split('\n')[0]
        qe_results = dict((band, []) for band in self.qe_band_passes)
        for line in open(csv_file):
            tokens = line.split(',')
            if tokens[0] == 'Amp':
                wls = []
                for item in tokens[1:]:
                    try:
                        wls.append(float(item.strip()))
                    except:
                        wls.append(None)
            else:
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
        "Process the metrology results."
        results = {}
        command = ('find %s/ -name \*Mechanical_Shim_Test_Sheet.xls -print'
                   % self.rootdir)
        xls_file = subprocess.check_output(command, shell=True).split('\n')[0]
        e2v_values = vendorDataUtils.get_e2v_xls_values(xls_file)
        results['zmean'] = e2v_values.get('Mean Height', -999)
        results['deviation_from_znom'] = \
            e2v_values.get('Deviation from Znom', -999)
        for key in 'mounting_grade height_grade flatness_grade'.split():
            results[key] = 'N/A'
        schema = lcatr.schema.get('metrology_vendorIngest')
        sentinel_value = '-999'
        for key in schema.keys():
            if key in results or key in ('schema_name', 'schema_version'):
                continue
            results[key] = sentinel_value
        return [validate('metrology_vendorIngest', **results)]

def extract_ITL_metrology_date(txtfile):
    """
    Extract the date from the first line of an ITL metrology scan file.
    """
    months = dict([(datetime.date(2017, m, 1).strftime('%B'), m)
                   for m in range(1, 13)])
    with open(txtfile) as fileobj:
        line = fileobj.readline().strip('\n')
    tokens = re.sub('[:, ]', ' ', line).split()[-8:]
    hours = int(tokens[0])
    if hours == 12 and tokens[3] == 'AM':
        hours = 0
    elif hours == 12 and tokens[3] == 'PM':
        hours = 12
    elif tokens[3] == 'PM':
        hours += 12
    minutes = int(tokens[1])
    seconds = int(tokens[2])
    month = months[tokens[5]]
    day = int(tokens[6])
    year = int(tokens[7])
    obs_date = datetime.datetime(year, month, day, hours, minutes, seconds)
    return obs_date.strftime('%Y-%m-%dT%H:%M:%S')

def ITL_metrology_files(rootdir, expected_num=1):
    """
    Find the ITL metrology scan files assuming they have filenames of
    the form '*Z_Inspect*.txt' or the '*.txt' extension and the first
    non-blank line starts with the word "Program".  If the number of
    files found does not match the expected number, a RuntimeError
    will be raised.
    """
    command = 'find %s -name \*.txt -print | grep metrology' % rootdir
    try:
        txt_files = subprocess.check_output(command, shell=True).split()
    except subprocess.CalledProcessError as eobj:
        print("No metrology files found:")
        print(eobj)
        return []
    met_files = [txt_file for txt_file in txt_files
                 if fnmatch.fnmatch(txt_file, '*ID*SN*Z_Inspect*.txt')]
    if not met_files:
        for txt_file in txt_files:
            # Look for the word "Program" as the first non-blank line
            # of a .txt file.
            with open(txt_file, 'r') as candidate:
                for line in candidate:
                    if len(line.split()) == 0:
                        # skip white-space only lines
                        continue
                    if line.startswith('Program'):
                        met_files.append(txt_file)
                    break
    if len(met_files) != expected_num:
        raise RuntimeError(("Found %i metrology scan files," % len(met_files))
                           + (" expected %i." % expected_num))
    return met_files

def e2v_metrology_files(rootdir, expected_num=1):
    """
    Find the e2v metrology scan files assuming the filenames end with
    'CT100*.csv'.  If the number of files found does not match the
    expected number, a RuntimeError will be raised.
    """
    command = 'find %s -name \*CT100\*.csv -print' % rootdir
    try:
        met_files = subprocess.check_output(command, shell=True).split()
    except subprocess.CalledProcessError as eobj:
        print("Exception raised while running 'find' for metrology data:")
        print(eobj)
        met_files = []
    if len(met_files) == 0:
        print("No metrology files found.")
        return []
    if len(met_files) != expected_num:
        raise RuntimeError(("Found %i metrology scan files," % len(met_files))
                           + ("expected %i." % expected_num))
    return met_files

def filerefs_for_metrology_files(met_files, lsstnum):
    """
    Return a list of lcatr.schema.filerefs for the input list of
    metrology scan files, adding the metadata required to find them in
    the Data Catalog.
    """
    results = []
    for infile in met_files:
        outfile = os.path.basename(infile)
        shutil.copy(infile, outfile)
        metadata = dict(DATA_PRODUCT='MET_SCAN',
                        LSST_NUM=lsstnum,
                        TEST_CATEGORY='MET')
        results.append(lcatr.schema.fileref.make(outfile, metadata=metadata))
    return results

if __name__ == '__main__':
    results = siteUtils.packageVersions()

    lsstnum = siteUtils.getUnitId()

    vendorDataDir = os.readlink('vendorData')
    print('Vendor data location:', vendorDataDir)

    if siteUtils.getCcdVendor() == 'ITL':
        vendor = ItlResults(vendorDataDir)
        translator = ItlFitsTranslator(lsstnum, vendorDataDir, '.')
        met_files = ITL_metrology_files(vendorDataDir, expected_num=1)
        MET_date = extract_ITL_metrology_date(met_files[0])
    else:
        vendor = e2vResults(vendorDataDir)
        translator = e2vFitsTranslator(lsstnum, vendorDataDir, '.')
        met_files = e2v_metrology_files(vendorDataDir, expected_num=1)
        MET_date = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')

    results.extend(vendor.run_all())

    translator.run_all()
    results.extend([lcatr.schema.fileref.make(x) for x in translator.outfiles])
    if met_files:
        results.extend(filerefs_for_metrology_files(met_files, lsstnum))
    system_noise_file = '%s_system_noise.txt' % siteUtils.getUnitId()
    if os.path.isfile(system_noise_file):
        metadata = dict(LSST_NUM=siteUtils.getUnitId(),
                        TEST_CATEGORY='EO',
                        DATA_PRODUCT='SYSTEM_NOISE',
                        DATA_SOURCE='VENDOR')
        results.append(lcatr.schema.fileref.make(system_noise_file,
                                                 metadata=metadata))

    results.append(validate('vendor_test_dates',
                            EO_date=translator.date_obs,
                            MET_date=MET_date))

    lcatr.schema.write_file(results)
    lcatr.schema.validate_file()
