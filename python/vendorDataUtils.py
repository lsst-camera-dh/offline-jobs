"""
Utilities for vendor data handling.
"""
from __future__ import absolute_import, print_function
import os
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
