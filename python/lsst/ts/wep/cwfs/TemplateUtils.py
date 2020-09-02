import os
import numpy as np
from lsst.ts.wep.Utility import DefocalType, getConfigDir, \
    CamType, abbrevDetectorName, readPhoSimSettingData
from lsst.ts.wep.cwfs.Instrument import Instrument
from lsst.ts.wep.cwfs.CompensableImage import CompensableImage


def createTemplateImage(defocalState, sensorName, pix2arcsec,
                        templateType, donutImgSize):

    """
    Create/grab donut template.

    Parameters
    ----------
    sensorName : str
        Abbreviated sensor name.
    """

    configDir = getConfigDir()

    if templateType == 'phosim':
        if defocalState == DefocalType.Extra:
            template_filename = os.path.join(configDir, 'deblend',
                                             'data',
                                             'extra_template-%s.txt' %
                                             sensorName)
        elif defocalState == DefocalType.Intra:
            template_filename = os.path.join(configDir, 'deblend',
                                             'data',
                                             'intra_template-%s.txt' %
                                             sensorName)
        template_array = np.genfromtxt(template_filename)
        template_array[template_array < 50] = 0.

    elif templateType == 'model':
        focalPlaneLayout = readPhoSimSettingData(configDir, 'focalplanelayout.txt', "fieldCenter")

        pixelSizeInUm = float(focalPlaneLayout[sensorName][2])
        sizeXinPixel = int(focalPlaneLayout[sensorName][3])
        sizeYinPixel = int(focalPlaneLayout[sensorName][4])

        sensor_x_micron, sensor_y_micron = np.array(focalPlaneLayout[sensorName][:2], dtype=float)
        # Correction for wavefront sensors
        # (from _shiftCenterWfs in SourceProcessor.py)
        if sensorName in ("R44_S00_C0", "R00_S22_C1"):
            # Shift center to +x direction
            sensor_x_micron = sensor_x_micron + sizeXinPixel / 2 * pixelSizeInUm
        elif sensorName in ("R44_S00_C1", "R00_S22_C0"):
            # Shift center to -x direction
            sensor_x_micron = sensor_x_micron - sizeXinPixel / 2 * pixelSizeInUm
        elif sensorName in ("R04_S20_C1", "R40_S02_C0"):
            # Shift center to -y direction
            sensor_y_micron = sensor_y_micron - sizeXinPixel / 2 * pixelSizeInUm
        elif sensorName in ("R04_S20_C0", "R40_S02_C1"):
            # Shift center to +y direction
            sensor_y_micron = sensor_y_micron + sizeXinPixel / 2 * pixelSizeInUm

        sensor_x_pixel = float(sensor_x_micron)/pixelSizeInUm
        sensor_y_pixel = float(sensor_y_micron)/pixelSizeInUm

        sensor_x_deg = sensor_x_pixel*pix2arcsec / 3600
        sensor_y_deg = sensor_y_pixel*pix2arcsec / 3600

        # Load Instrument parameters
        instDir = os.path.join(configDir, "cwfs", "instData")
        dimOfDonutOnSensor = donutImgSize
        inst = Instrument(instDir)
        inst.config(CamType.LsstCam, dimOfDonutOnSensor)

        # Create image for mask
        img = CompensableImage()
        img.defocalType = defocalState

        # define position of donut at center of current sensor in degrees
        boundaryT = 0
        maskScalingFactorLocal = 1
        img.fieldX, img.fieldY = sensor_x_deg, sensor_y_deg
        img.makeMask(inst, "offAxis", boundaryT, maskScalingFactorLocal)

        template_array = img.cMask

    elif templateType == 'isolatedDonutFromImage':
        if defocalState == DefocalType.Extra:
            template_filename = os.path.join(configDir, 'deblend',
                                             'data', 'isolatedDonutTemplate',
                                             'extra_template-%s.dat' %
                                             sensorName)
        elif defocalState == DefocalType.Intra:
            template_filename = os.path.join(configDir, 'deblend',
                                             'data', 'isolatedDonutTemplate',
                                             'intra_template-%s.dat' %
                                             sensorName)
        template_array = np.genfromtxt(template_filename)
        template_array[template_array < 0] = 0.

    return template_array
