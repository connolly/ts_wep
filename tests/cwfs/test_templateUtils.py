import unittest
import os
import numpy as np

from lsst.ts.wep.cwfs.TemplateUtils import createTemplateImage
from lsst.ts.wep.Utility import getConfigDir


class TestTemplateUtils(unittest.TestCase):
    """Test the Template Utility functions."""

    def setUp(self):

        pass

    def testCreateTemplateImage(self):

        sensorName = 'R22_S11'
        pix2arcsec = 0.2
        donutImgSize = 160

        # Test Model Template Generation
        templateModelExtra = createTemplateImage('extra', sensorName,
                                                 pix2arcsec,
                                                 'model', donutImgSize)
        self.assertTrue(np.shape(templateModelExtra),
                        [donutImgSize, donutImgSize])
        templateModelIntra = createTemplateImage('intra', sensorName,
                                                 pix2arcsec,
                                                 'model', donutImgSize)
        self.assertTrue(np.shape(templateModelIntra),
                        [donutImgSize, donutImgSize])

        # Test Phosim Templates
        templatePhosimExtra = createTemplateImage('extra', sensorName,
                                                  pix2arcsec,
                                                  'phosim', donutImgSize)
        self.assertTrue(np.shape(templatePhosimExtra),
                        [donutImgSize, donutImgSize])
        templatePhosimIntra = createTemplateImage('intra', sensorName,
                                                  pix2arcsec,
                                                  'phosim', donutImgSize)
        self.assertTrue(np.shape(templatePhosimIntra),
                        [donutImgSize, donutImgSize])

        # Test Isolated Donut from Image Templates
        configDir = os.path.join(getConfigDir(), 'deblend', 'data', 'phosim')
        templateIsolatedExtra = createTemplateImage('extra', sensorName,
                                                    pix2arcsec,
                                                    'isolatedDonutFromImage',
                                                    donutImgSize,
                                                    configDir=configDir)
        self.assertTrue(np.shape(templateIsolatedExtra),
                        [donutImgSize, donutImgSize])
        templateIsolatedIntra = createTemplateImage('intra', sensorName,
                                                    pix2arcsec,
                                                    'isolatedDonutFromImage',
                                                    donutImgSize,
                                                    configDir=configDir)
        self.assertTrue(np.shape(templateIsolatedIntra),
                        [donutImgSize, donutImgSize])


if __name__ == "__main__":

    unittest.main()
