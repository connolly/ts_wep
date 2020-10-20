import unittest
import os

import lsst.geom
from lsst.ts.wep.ctrlIntf.ButlerWcsSol import ButlerWcsSol
from lsst.ts.wep.Utility import getModulePath
from lsst.afw.image import ExposureF


class TestButlerWcsSol(unittest.TestCase):
    """Test the ButlerWcsSol class."""

    def setUp(self):

        self.modulePath = getModulePath()
        self.repoDir = os.path.join(self.modulePath, "tests", "testData",
                                    "testRepo", "rerun", "run1")

        self.exp = ExposureF(os.path.join(
            self.repoDir, 'postISRCCD', '09005000-g', 'R22',
            'postISRCCD_09005000-g-R22-S11-det094.fits')
        )
        self.detectorList = ['R:2,2 S:1,1']
        self.visitNum = 9005000

    def testSetIsrDir(self):

        testWcsSol = ButlerWcsSol()
        testWcsSol.setIsrDir(self.repoDir)
        self.assertEqual(testWcsSol.isrDir, self.repoDir)

    def testSetWcsDataFromIsrDir(self):

        testWcsSol = ButlerWcsSol()
        testWcsSol.setIsrDir(self.repoDir)
        testWcsSol.setWcsDataFromIsrDir(self.detectorList, self.visitNum)

        self.assertEqual(type(testWcsSol.wcsData), dict)
        self.assertEqual(testWcsSol.wcsData[self.detectorList[0]],
                         self.exp.getWcs())

    def testSetObsMetaData(self):

        testWcsSol = ButlerWcsSol()
        self.assertEqual(testWcsSol.setObsMetaData(0., 0., 0.), None)

    def testRaDecFromPixelCoords(self):

        testWcsSol = ButlerWcsSol()
        testWcsSol.setIsrDir(self.repoDir)
        testWcsSol.setWcsDataFromIsrDir(self.detectorList, self.visitNum)
        raButlerFlt, decButlerFlt = testWcsSol.raDecFromPixelCoords(
            0., 0., self.detectorList[0]
        )
        raButlerList, decButlerList = testWcsSol.raDecFromPixelCoords(
            [0.], [0.], self.detectorList[0]
        )
        raExp, decExp = self.exp.getWcs().pixelToSky(0., 0.)
        self.assertEqual(raButlerFlt, raButlerList)
        self.assertEqual(decButlerFlt, decButlerList)
        self.assertAlmostEqual(raButlerFlt[0], raExp.asDegrees())
        self.assertAlmostEqual(decButlerFlt[0], decExp.asDegrees())

    def testPixelCoordsFromRaDec(self):

        testWcsSol = ButlerWcsSol()
        testWcsSol.setIsrDir(self.repoDir)
        testWcsSol.setWcsDataFromIsrDir(self.detectorList, self.visitNum)
        xPixFlt, yPixFlt = testWcsSol.pixelCoordsFromRaDec(
            0., 0., self.detectorList[0]
        )
        xPixList, yPixList = testWcsSol.pixelCoordsFromRaDec(
            0., 0., self.detectorList[0]
        )
        xPixExp, yPixExp = self.exp.getWcs().skyToPixel(
            lsst.geom.SpherePoint(0., 0., lsst.geom.degrees)
        )
        self.assertEqual(xPixFlt, xPixList)
        self.assertEqual(yPixFlt, yPixList)
        self.assertAlmostEqual(xPixFlt[0], xPixExp)
        self.assertAlmostEqual(yPixFlt[0], yPixExp)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
