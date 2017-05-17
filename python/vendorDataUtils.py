"""
Utilities for vendor data handling.
"""
from __future__ import absolute_import, print_function
import os
import astropy.io.fits as fits
import xlrd
import siteUtils
from DataCatalog import DataCatalog

default_system_noise = {'ITL': dict((item+1, value) for item, value in
                                    enumerate((1.48, 1.62, 1.64, 1.50,
                                               1.49, 1.56, 1.40, 1.71,
                                               1.63, 1.43, 1.61, 1.45,
                                               1.50, 1.64, 1.47, 1.55))),
                        'E2V': dict((item, 0) for item in range(1, 17))}

def vendor_DataCatalog_folder(sensor_id=None):
    """
    Return the Data Catalog folder path to the vendorIngest data
    assuming the current folder conventions for Prod or Dev eT
    instances.
    """
    if sensor_id is None:
        sensor_id = siteUtils.getUnitId()
    folder_root = dict(Prod='/LSST/mirror/SLAC-prod/prod/',
                       Dev='/LSST/mirror/SLAC-test/test/')
    server = os.path.basename(os.environ['LCATR_LIMS_URL']).rstrip('/')
    return os.path.join(folder_root[server], '*', sensor_id, 'vendorIngest')

def query_for_vendor_system_noise(folder, single_dataset_flag=False):
    """
    Query for the vendor system noise from the Data Catalog for the
    current device.
    """
    sensor_id = siteUtils.getUnitId()
    dc = DataCatalog(folder=folder, site=siteUtils.getSiteName())
    query = ' && '.join(('LSST_NUM=="%(sensor_id)s"' % locals(),
                         'TEST_CATEGORY=="EO"',
                         'DATA_PRODUCT=="SYSTEM_NOISE"',
                         'DATA_SOURCE=="VENDOR"'))
    datasets = dc.find_datasets(query)
    if len(datasets) > 1:
        message = "Multiple vendor system noises file found for " + sensor_id
        for filepath in datasets.full_paths():
            message += "\n  %s\n" % filepath
        print(message)
        if single_dataset_flag:
            raise RuntimeError(message)
    if len(datasets) > 0:
        return [x for x in datasets.full_paths()][0]
    return None

def parse_system_noise_file(system_noise_file):
    "Unpack the system noise from the system noise file."
    system_noise = {}
    with open(system_noise_file) as input_:
        for line in input_:
            if line.startswith('#'):
                continue
            tokens = line.split()
            system_noise[int(tokens[0])] = float(tokens[1])
    return system_noise

def getSystemNoise(gains, folder=None):
    """
    Return the system noise for each amplifier channel in units of rms
    e- per pixel.
    """
    if folder is None:
        try:
            # Use the env var that can be set by the user in lcatr.cfg.
            folder = os.environ['LCATR_DATACATALOG_FOLDER']
        except KeyError:
            # Infer the folder based on the eT server instance.
            folder = vendor_DataCatalog_folder()
    system_noise_file = query_for_vendor_system_noise(folder)
    if system_noise_file is None:
        # set to vendor defaults
        system_noise = default_system_noise[siteUtils.getCcdVendor().upper()]
    else:
        system_noise = parse_system_noise_file(system_noise_file)

    # Convert from ADU to e- and return.
    return dict([(amp, gains[amp]*system_noise[amp]) for amp in gains])

def find_e2v_xls_label(entries, label):
    """
    Find an entry in a row of data from an e2v .xls file based on the
    specified label.

    Parameters
    ----------
    entries : list
        Cell values from a row in an .xls sheet processed by xlrd.
    label : str
        The label of the desired cell, e.g., "Deviation from Znom".


    Returns
    -------
    int : The index of the entry.

    Raises
    ------
    RuntimeError : If no entry for the label has been found.
    """
    for i, entry in enumerate(entries):
        try:
            if entry.lower().find(label.lower()) != -1:
                return i
        except AttributeError:
            pass
    raise RuntimeError("label %s not found", label)

def get_e2v_xls_values(xls_file, labels=('Mean Height', 'Deviation from Znom')):
    """
    Get the values associated with the specified labels from an e2v
    .xls file.  Check every row of every sheet in the workbook.

    Parameters
    ----------
    xls_file : str
        The filename of the e2v .xls file.
    labels : sequence, optional
        List or tuple of labels to look for.
        Default: ('Mean Height', 'Deviation from Znom')

    Returns
    -------
    dict : A dictionary of the found labels and their values.
    """
    workbook = xlrd.open_workbook(xls_file)
    results = {}
    for isheet in range(workbook.nsheets):
        sheet = workbook.sheet_by_index(isheet)
        for irow in range(sheet.nrows):
            # Make a list of entry values, excising empty cells.
            entries = [x.value for x in sheet.row(irow) if x.value != u'']
            for label in labels:
                try:
                    index = find_e2v_xls_label(entries, label)
                    results[label] = entries[index+1]
                except RuntimeError as eobj:
                    pass
    return results

def e2v_system_noise(fits_file):
    """
    Extract the system noise from the ARCHON extension of an e2v
    FITS file.

    Parameters
    ----------
    fits_file : str
        Filename of the FITS file from which to harvest the system noise
        values.  They are assumed to live in the ARCHON extension and have
        keyword names of the form SYS_N#.

    Returns
    -------
    dict : Dictionary of system noise values in DN, keyed by amp.
    """
    system_noise = dict()
    hdus = fits.open(fits_file)
    for amp in range(1, 17):
        keyword = 'SYS_N%d' % amp
        system_noise[amp] = hdus['ARCHON'].header[keyword]
    return system_noise
