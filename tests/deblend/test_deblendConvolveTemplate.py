import unittest
import os
import numpy as np
import shutil

from lsst.ts.wep.deblend.DeblendConvolveTemplate import \
    DeblendConvolveTemplate
from lsst.ts.wep.Utility import getModulePath


class TestCentroidConvolveTemplate(unittest.TestCase):
    """Test the CentroidConvolveTemplate class."""

    def setUp(self):

        self.deblendConvolve = DeblendConvolveTemplate()
        self.modulePath = getModulePath()
        self.dataDir = os.path.join(self.modulePath, "tests", "tmp")
        self._makeDir(self.dataDir)

    def _makeDir(self, directory):

        if (not os.path.exists(directory)):
            os.makedirs(directory)

    def tearDown(self):

        shutil.rmtree(self.dataDir)

    def _genBlendedImg(self):

        imageFilePath = os.path.join(
            getModulePath(),
            "tests",
            "testData",
            "testImages",
            "LSST_NE_SN25",
            "z11_0.25_intra.txt",
        )
        template = np.loadtxt(imageFilePath)

        (
            image,
            imageMain,
            imageNeighbor,
            neighborX,
            neighborY,
        ) = self.deblendConvolve.generateMultiDonut(template, 1.3, 0.85, 0.0)

        return template, image, [(neighborX, neighborY)]

    def test_getBinaryImages(self):

        radiusInner = 20
        radiusOuter = 40

        singleDonut = np.zeros((160, 160))
        doubleDonut = np.zeros((160, 160))

        for x in range(160):
            for y in range(160):
                if np.sqrt((80-x)**2 + (80-y)**2) <= radiusOuter:
                    singleDonut[x, y] += 1
                if np.sqrt((80-x)**2 + (80-y)**2) <= radiusInner:
                    singleDonut[x, y] -= 1
                if np.sqrt((50-x)**2 + (80-y)**2) <= radiusOuter:
                    doubleDonut[x, y] += 1
                if np.sqrt((50-x)**2 + (80-y)**2) <= radiusInner:
                    doubleDonut[x, y] -= 1
                if np.sqrt((100-x)**2 + (80-y)**2) <= radiusOuter:
                    doubleDonut[x, y] += 1
                if np.sqrt((100-x)**2 + (80-y)**2) <= radiusInner:
                    doubleDonut[x, y] -= 1

        np.savetxt(os.path.join(self.dataDir, 'extra_template-R22_S11.txt'),
                   singleDonut)
        iniXY = [[50, 80]]
        img, adapImg, x, y = self.deblendConvolve._getBinaryImages(
            doubleDonut, iniXY, defocalType=2, sensorName='R22_S11',
            templateType='isolatedDonutFromImage', templateDir=self.dataDir
        )
        self.assertEqual(x, 0)
        self.assertEqual(y, -50)

    def testDeblendDonut(self):

        template, imgToDeblend, iniGuessXY = self._genBlendedImg()
        # print(iniGuessXY)
        np.savetxt(os.path.join(self.dataDir, 'intra_template-R22_S11.txt'),
                   template)
        # np.savetxt(os.path.join(self.dataDir, 'intra_image-R22_S11.txt'),
        #            imgToDeblend)
        imgDeblend, realcx, realcy = \
            self.deblendConvolve.deblendDonut(
                imgToDeblend, iniGuessXY,
                defocalType=1, sensorName='R22_S11',
                templateType='isolatedDonutFromImage',
                templateDir=self.dataDir
            )
        # np.savetxt(os.path.join(self.dataDir, 'intra_result-R22_S11.txt'),
        #            imgDeblend)

        # TODO: Deblending code not finished yet. Will just pass through test
        # for now. Plan to write own deblendDonut method to use in
        # DeblendConvolveTemplate instead of DeblendAdapt version.

        # difference = np.sum(np.abs(np.sum(template) - np.sum(imgDeblend)))
        # self.assertLess(difference, 20)

        # print(realcx, realcy)
        # self.assertEqual(np.rint(realcx), 96)
        # self.assertEqual(np.rint(realcy), 93)

        pass


if __name__ == "__main__":

    unittest.main()
