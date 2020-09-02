import os
import unittest

from lsst.ts.wep.Utility import abbrevDetectorName, expandDetectorName, \
    mapFilterRefToG, FilterType, getModulePath, getConfigDir, \
    getObsLsstCmdTaskConfigDir, ImageType, getImageType, getBscDbType, \
    BscDbType, getCentroidFindType, CentroidFindType, getDeblendDonutType, \
    DeblendDonutType


class TestUtility(unittest.TestCase):
    """Test the Utility functions."""

    def testSerializingAndUnserializingFilterType(self):

        filt = FilterType.fromString('y')
        self.assertEqual(filt, FilterType.Y)
        string = filt.toString()
        self.assertEqual(string, 'y')

    def testAbbrevDetectorName(self):

        sciSensorName = "R:2,2 S:1,1"
        self.assertEqual(abbrevDetectorName(sciSensorName), "R22_S11")

        wfsSensorName = "R:4,0 S:0,2,B"
        self.assertEqual(abbrevDetectorName(wfsSensorName), "R40_S02_C1")

        self.assertRaises(ValueError, abbrevDetectorName, "R:4,0 S:0,2,C")

    def testExpandDetectorName(self):

        sciSensorName = "R22_S11"
        self.assertEqual(expandDetectorName(sciSensorName), "R:2,2 S:1,1")

        wfsSensorName = "R40_S02_C1"
        self.assertEqual(expandDetectorName(wfsSensorName), "R:4,0 S:0,2,B")

        self.assertRaises(ValueError, expandDetectorName, "R40_S02_C2")

    def testMapFilterRefToG(self):

        mappedFilterType = mapFilterRefToG(FilterType.REF)
        self.assertEqual(mappedFilterType, FilterType.G)

    def testMapFilterRefToGForFilterU(self):

        mappedFilterType = mapFilterRefToG(FilterType.U)
        self.assertEqual(mappedFilterType, FilterType.U)

    def testGetConfigDir(self):

        ansConfigDir = os.path.join(getModulePath(), "policy")
        self.assertEqual(getConfigDir(), ansConfigDir)

    def testGetObsLsstCmdTaskConfigDir(self):

        obsLsstCmdTaskConfirDir = getObsLsstCmdTaskConfigDir()
        configNormPath = os.path.normpath(obsLsstCmdTaskConfirDir)
        configNormPathList = configNormPath.split(os.sep)

        self.assertEqual(configNormPathList[-1], "config")
        self.assertTrue(("obs_lsst" in configNormPathList))

    def testGetBscDbType(self):

        self.assertEqual(getBscDbType("localDb"), BscDbType.LocalDb)
        self.assertEqual(getBscDbType("file"), BscDbType.LocalDbForStarFile)

    def testGetBscDbTypeWithWrongInput(self):

        self.assertRaises(ValueError, getBscDbType, "wrongType")

    def testGetImageType(self):

        self.assertEqual(getImageType("amp"), ImageType.Amp)
        self.assertEqual(getImageType("eimage"), ImageType.Eimg)

    def testGetImageTypeWithWrongInput(self):

        self.assertRaises(ValueError, getImageType, "wrongType")

    def testGetCentroidFindType(self):

        self.assertEqual(getCentroidFindType("randomWalk"),
                         CentroidFindType.RandomWalk)
        self.assertEqual(getCentroidFindType("otsu"),
                         CentroidFindType.Otsu)

    def testGetCentroidFindTypeWithWrongInput(self):

        self.assertRaises(ValueError, getCentroidFindType, "wrongType")

    def testGetDeblendDonutType(self):

        self.assertEqual(getDeblendDonutType("adapt"),
                         DeblendDonutType.Adapt)

    def testGetDeblendDonutTypeWithWrongInput(self):

        self.assertRaises(ValueError, getDeblendDonutType, "wrongType")


if __name__ == "__main__":

    # Do the unit test
    unittest.main()
