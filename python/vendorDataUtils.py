import os
import siteUtils

def getSystemNoise(gains):
    """
    Return the system noise for each amplifier channel in units of
    rms e- per pixel.
    """
    if siteUtils.getCcdVendor() == 'ITL':
        # ITL reports a system noise of 1.65 DN per channel.
        return dict([(amp, 1.65*gains[amp]) for amp in gains])

    # Return None by default.
    return None
