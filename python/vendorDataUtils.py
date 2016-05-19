import os
import siteUtils
from DataCatalog import DataCatalog

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
    server = os.path.basename(os.environ['LCATR_LIMS_URL'])
    return os.path.join(folder_root[server], '*', sensor_id, 'vendorIngest')

def get_ITL_system_noise(gains, folder):
    """
    Try to retrieve the ITL system noise from the Data Catalog for the
    current device.
    """
    sensor_id = siteUtils.getUnitId()
    dc = DataCatalog(folder=folder, site=siteUtils.getSiteName())
    query = ' && '.join(('LSST_NUM=="%(sensor_id)s"' % locals(),
                         'TEST_CATEGORY=="EO"',
                         'DATA_PRODUCT=="SYSTEM_NOISE"',
                         'DATA_SOURCE=="VENDOR"'))
    datasets = dc.find_datasets(query)
    if len(datasets) == 1:
        system_noise_file = [x for x in datasets.full_paths()][0]
        with open(system_noise_file) as input_:
            system_noise = {}
            for line in sysnoise:
                if line.startswith('#'):
                    continue
    elif len(datasets) > 1:
        raise RuntimeError("More than one vendor system noise file found"
                           + " for " + sensor_id)
    else:
        # No files found, so print a warning and use the
        # recommended default values that Mike Lesser sent by
        # email.
        print("No ITL vendor system noise data found, so use default"
              + " values recommended by ITL.")
        system_noise = dict((item+1, value) for item, value in
                            enumerate((1.48, 1.62, 1.64, 1.50,
                                       1.49, 1.56, 1.40, 1.71,
                                       1.63, 1.43, 1.61, 1.45,
                                       1.50, 1.64, 1.47, 1.55)))

    # Convert from ADU to e- and return.
    return dict([(amp, gains[amp]*system_noise[amp]) for amp in gains])

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
            folder = vendorDataCatalog_folder()
    if siteUtils.getCcdVendor() == 'ITL':
        return get_ITL_system_noise(gains, folder)
    else:
        # e2v should be handled here, but they don't provide system
        # noise, so fall through to the default return value.
        pass
    return None
