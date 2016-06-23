#!/usr/bin/env python
import os
import shutil
from collections import OrderedDict

# This is needed so that matplotlib can write to .matplotlib
os.environ['MPLCONFIGDIR'] = os.curdir
import matplotlib
# For batch-processing, use the AGG backend to avoid needing an X11
# connection.
matplotlib.use('Agg')

import json
import astropy.io.fits as fits
import matplotlib.pyplot as plt
import lsst.eotest.sensor as sensorTest
import lsst.eotest.image_utils as imutils
from lcatr.harness.helpers import dependency_glob
import siteUtils
import eotestUtils

def processName_dependencyGlob(*args, **kwds):
    if kwds.has_key('jobname'):
        kwds['jobname'] = siteUtils.getProcessName(kwds['jobname'])
    return dependency_glob(*args, **kwds)

class JsonRepackager(object):
    _key_map = dict((('gain', 'GAIN'),
                     ('gain_error', 'GAIN_ERROR'),
                     ('psf_sigma', 'PSF_SIGMA'),
                     ('read_noise', 'READ_NOISE'),
                     ('system_noise', 'SYSTEM_NOISE'),
                     ('total_noise', 'TOTAL_NOISE'),
                     ('bright_pixels', 'NUM_BRIGHT_PIXELS'),
                     ('bright_columns', 'NUM_BRIGHT_COLUMNS'),
                     ('dark_pixels', 'NUM_DARK_PIXELS'),
                     ('dark_columns', 'NUM_DARK_COLUMNS'),
                     ('dark_current_95CL', 'DARK_CURRENT_95'),
                     ('num_traps', 'NUM_TRAPS'),
                     ('cti_low_serial', 'CTI_LOW_SERIAL'),
                     ('cti_low_serial_error', 'CTI_LOW_SERIAL_ERROR'),
                     ('cti_low_parallel', 'CTI_LOW_PARALLEL'),
                     ('cti_low_parallel_error', 'CTI_LOW_PARALLEL_ERROR'),
                     ('cti_high_serial', 'CTI_HIGH_SERIAL'),
                     ('cti_high_serial_error', 'CTI_HIGH_SERIAL_ERROR'),
                     ('cti_high_parallel', 'CTI_HIGH_PARALLEL'),
                     ('cti_high_parallel_error', 'CTI_HIGH_PARALLEL_ERROR'),
                     ('full_well', 'FULL_WELL'),
                     ('max_frac_dev', 'MAX_FRAC_DEV'),
                     ('ptc_gain', 'PTC_GAIN'),
                     ('ptc_gain_error', 'PTC_GAIN_ERROR'),
                     ))
    def __init__(self, outfile='eotest_results.fits', namps=16):
        """
        Repackage per amp information in the json-formatted
        summary.lims files from each analysis task into the
        EOTestResults-formatted output.
        """
        self.eotest_results = sensorTest.EOTestResults(outfile, namps=namps)
    def process_file(self, infile):
        foo = json.loads(open(infile).read())
        for result in foo:
            if result.has_key('amp'):
                amp = result['amp']
                for key, value in result.items():
                    if key.find('schema') == 0 or key == 'amp':
                        continue
                    self.eotest_results.add_seg_result(amp, self._key_map[key],
                                                       value)
    def write(self, outfile=None, clobber=True):
        self.eotest_results.write(outfile=outfile, clobber=clobber)
    def process_files(self, summary_files):
        for item in summary_files:
            print "processing", item
            self.process_file(item)

def append_prnu(results_file, prnu_file):
    """
    Copy the PRNU_RESULTS extension from the prnu job to the final
    results file.
    """
    results = fits.open(results_file)
    prnu = fits.open(prnu_file)
    results.append(prnu['PRNU_RESULTS'])
    results.writeto(results_file, clobber=True)

sensor_id = siteUtils.getUnitId()
results_file = '%s_eotest_results.fits' % sensor_id

# Wavelength scan files, which are used in the flat field plots and
# for determining the maximum number of active pixels for the image
# quality statistics
wl_files = siteUtils.datacatalog_glob('*_lambda_*.fits',
                                      testtype='LAMBDA',
                                      imgtype='FLAT',
                                      description='Lambda files:')

total_num, rolloff_mask = sensorTest.pixel_counts(wl_files[0])
all_amps = imutils.allAmps(wl_files[0])

# Aggregate information from summary.lims files into
# a final EOTestResults output file.
repackager = JsonRepackager(namps=len(all_amps))
repackager.eotest_results.add_ccd_result('TOTAL_NUM_PIXELS', total_num)
repackager.eotest_results.add_ccd_result('ROLLOFF_MASK_PIXELS', rolloff_mask)
summary_files = processName_dependencyGlob('summary.lims')
repackager.process_files(summary_files)
repackager.write(results_file)

append_prnu(results_file, processName_dependencyGlob(results_file,
                                                     jobname='prnu_offline')[0])

qe_file = processName_dependencyGlob('*%s_QE.fits' % sensor_id,
                                     jobname='qe_offline')[0]
shutil.copy(qe_file, ".")

try:
    xtalk_file = processName_dependencyGlob('*%s_xtalk_matrix.fits' % sensor_id,
                                            jobname='crosstalk_offline')[0]
except IndexError:
    xtalk_file = None

plots = sensorTest.EOTestPlots(sensor_id, results_file=results_file,
                               xtalk_file=xtalk_file)
plots.specs.add_job_ids(summary_files)

# Fe55 flux distribution fits
fe55_file = processName_dependencyGlob('%s_psf_results*.fits' % sensor_id,
                                       jobname='fe55_offline')[0]
plots.fe55_dists(fe55_file=fe55_file)
plt.savefig('%s_fe55_dists.png' % sensor_id)

# PSF distributions from Fe55 fits
plots.psf_dists(fe55_file=fe55_file)
plt.savefig('%s_psf_dists.png' % sensor_id)

# Photon Transfer Curves
ptc_file = processName_dependencyGlob('%s_ptc.fits' % sensor_id,
                                      jobname='ptc_offline')[0]
plots.ptcs(ptc_file=ptc_file)
plt.savefig('%s_ptcs.png' % sensor_id)

detresp_file = processName_dependencyGlob('%s_det_response.fits' % sensor_id,
                                          jobname='flat_pairs_offline')[0]
# Full well plots
plots.full_well(ptc_file=ptc_file, detresp_file=detresp_file)
plt.savefig('%s_full_well.png' % sensor_id)

# Linearity plots
if siteUtils.getCcdVendor() == 'ITL':
    # Use special linearity dataset for ITL data
    try:
        detresp_file = processName_dependencyGlob('%s_det_response_linearity.fits' % sensor_id,
                                                  jobname='flat_pairs_offline')[0]
    except:
        pass

plots.linearity(detresp_file=detresp_file)
plt.savefig('%s_linearity.png' % sensor_id)

plots.linearity_resids(detresp_file=detresp_file)
plt.savefig('%s_linearity_resids.png' % sensor_id)

# System Gain per segment
plots.gains()
plt.savefig('%s_gains.png' % sensor_id)

# Read Noise per segment
plots.noise()
plt.savefig('%s_noise.png' % sensor_id)

# Fe55 zoom
fe55_zoom = processName_dependencyGlob('%s_fe55_zoom.png' % sensor_id,
                                       jobname='fe55_offline')[0]
print "fe55_zoom: ", fe55_zoom
shutil.copy(fe55_zoom, '.')

# Coadded bias frame
bias_files = processName_dependencyGlob('%s_mean_bias_*.fits' % sensor_id,
                                        jobname='fe55_offline')
if bias_files:
    sensorTest.plot_flat(bias_files[0], title='%s, mean bias frame' % sensor_id)
    plt.savefig('%s_mean_bias.png' % sensor_id)

# Mosaicked image of medianed dark for bright_defects job.
dark_bd_file = processName_dependencyGlob('%s_median_dark_bp.fits' % sensor_id,
                                          jobname='bright_defects_offline')[0]
sensorTest.plot_flat(dark_bd_file,
                     title='%s, medianed dark for bright defects analysis' % sensor_id)
plt.savefig('%s_medianed_dark.png' % sensor_id)

# Superflat for dark defects job
sflat_dd_file = processName_dependencyGlob('%s_median_sflat.fits' % sensor_id,
                                           jobname='dark_defects_offline')[0]
sensorTest.plot_flat(sflat_dd_file,
                     title='%s, superflat for dark defects analysis' % sensor_id)
plt.savefig('%s_superflat_dark_defects.png' % sensor_id)

# Superflats for high and low flux levels
superflat_files = sorted(processName_dependencyGlob('%s_superflat_*.fits' % sensor_id, jobname='cte_offline'))
print "superflat_files:\n", superflat_files
for sflat_file in superflat_files:
    flux_level = 'low'
    if sflat_file.find('high') != -1:
        flux_level = 'high'
    sensorTest.plot_flat(sflat_file,
                         title='%(sensor_id)s, CTE supeflat, %(flux_level)s flux ' % locals())
    outfile = os.path.basename(sflat_file).replace('.fits', '.png')
    print outfile
    plt.savefig(outfile)

    # Profiles of serial CTE in overscan region
    mask_files = eotestUtils.glob_mask_files()
    mask_files = [item for item in mask_files if item.find('rolloff') == -1]
    plots.cte_profiles(flux_level, sflat_file, mask_files, serial=True)
    outfile = '%(sensor_id)s_serial_oscan_%(flux_level)s.png' % locals()
    plt.savefig(outfile)

    # Profiles of parallel CTE in overscan region
    mask_files = eotestUtils.glob_mask_files()
    mask_files = [item for item in mask_files if item.find('rolloff') == -1]
    plots.cte_profiles(flux_level, sflat_file, mask_files, serial=False)
    outfile = '%(sensor_id)s_parallel_oscan_%(flux_level)s.png' % locals()
    plt.savefig(outfile)

# Quantum Efficiency
plots.qe(qe_file=qe_file)
plt.savefig('%s_qe.png' % sensor_id)

# Crosstalk matrix
if xtalk_file is not None:
    plots.crosstalk_matrix(xtalk_file=xtalk_file)
    plt.savefig('%s_crosstalk_matrix.png' % sensor_id)

# Flat fields at wavelengths nearest the centers of the standard bands
wl_file_path = os.path.split(wl_files[0])[0]
plots.flat_fields(wl_file_path)
plt.savefig('%s_flat_fields.png' % sensor_id)

# Software versions
software_versions = OrderedDict()
summary_lims_file = processName_dependencyGlob('summary.lims',
                                               jobname='fe55_offline')[0]
foo = json.loads(open(summary_lims_file).read())
for result in foo:
    if result['schema_name'] == 'package_versions':
        for key, value in result.items():
            if key == 'schema_version':
                continue
            if key.endswith('_version'):
                software_versions[key] = value

# Create the test report pdf.
report = sensorTest.EOTestReport(plots, wl_file_path,
                                 software_versions=software_versions)
report.make_pdf()
