import os
import numpy as np
from lsst.ts.wep.Utility import getConfigDir, \
    CamType, abbrevDetectorName, readPhoSimSettingData
from lsst.ts.wep.cwfs.Instrument import Instrument
from lsst.ts.wep.cwfs.CompensableImage import CompensableImage


def createTemplateImage(defocalState, sensorName, pix2arcsec,
                        templateType, donutImgSize, configDir=None):

    """
    Create/grab donut template.

    Parameters
    ----------
    defocalState: str
        'extra' or 'intra'

    sensorName : str
        Abbreviated sensor name.

    pix2arcsec: float
        Pixel Scale in arcsec

    templateType: str
        Available template options are:
            - phosim
                - Use template derived from Phosim simulations
            - model
                - Use the donut model from CompensableImage class
            - isolatedDonutFromImage
                - Use an isolated donut previously found in an image
                  and saved with filenames as follows:
                  "{defocalState}_template-{sensorName}.txt"
                - Note does not actually find the templates for you

    donutImgSize: int
        Size of donut postage stamp in pixels

    configDir: None or str
        If None will default to ts_wep/policy/deblend/data to look
        for templates when using 'phosim' or 'isolatedDonutFromImage'
    """

    # If configDir is not specified set defaults for phosim or isolatedDonut
    if configDir is None:
        configDir = getConfigDir()
        if templateType != 'model':
            configDir = os.path.join(configDir,
                                     'deblend', 'data', templateType)

    if templateType == 'phosim':
        if defocalState == 'extra':
            template_filename = os.path.join(configDir,
                                             'extra_template-%s.txt' %
                                             sensorName)
        elif defocalState == 'intra':
            template_filename = os.path.join(configDir,
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
        if defocalState == 'extra':
            template_filename = os.path.join(configDir,
                                             'extra_template-%s.txt' %
                                             sensorName)
        elif defocalState == 'intra':
            template_filename = os.path.join(configDir,
                                             'intra_template-%s.txt' %
                                             sensorName)
        template_array = np.genfromtxt(template_filename)
        template_array[template_array < 0] = 0.

    return template_array
