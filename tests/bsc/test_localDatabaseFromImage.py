import os
import shutil
import numpy as np
import pandas as pd
import unittest

from lsst.ts.wep.bsc.LocalDatabaseFromImage import LocalDatabaseFromImage
from lsst.ts.wep.bsc.CamFactory import CamFactory
from lsst.ts.wep.Utility import getModulePath, FilterType, CamType
from lsst.ts.wep.ParamReader import ParamReader


class TestLocalDatabaseFromImage(unittest.TestCase):
    """Test the local database from image class."""

    def setUp(self):

        self.modulePath = getModulePath()

        self.dataDir = os.path.join(self.modulePath, "tests", "tmp")
        self._makeDir(self.dataDir)

        self.repoDir = os.path.join(self.modulePath, "tests", "testData",
                                    "testRepo", "rerun", "run1")

        self.filterType = FilterType.G
        self.camera = CamFactory.createCam(CamType.ComCam)
        self.camera.setObsMetaData(0., 0., 0.)
        self.db = LocalDatabaseFromImage()

        dbAddress = os.path.join(self.modulePath, "tests", "testData",
                                 "bsc.db3")
        self.db.connect(dbAddress)

    def _makeDir(self, directory):

        if (not os.path.exists(directory)):
            os.makedirs(directory)

    def tearDown(self):

        self.db.deleteTable(self.filterType)
        self.db.disconnect()

        shutil.rmtree(self.dataDir)

    def _createTable(self):
        self.db.createTable(self.filterType)

    def _createParamFile(self):

        self.paramFileName = os.path.join(self.dataDir, 'default.yaml')
        paramDict = {'expWcs': 'True', 'centroidTemplateType': 'model',
                     'donutImgSizeInPixel': 160, 'minUnblendedDistance': 160,
                     'doDeblending': False, 'maxSensorStars': 'null',
                     'pixelToArcsec': 0.2}
        with open(self.paramFileName, 'w') as f:
            for key in paramDict.keys():
                f.write('{}: {}\n'.format(key, paramDict[key]))

    def testIdentifyDonuts(self):

        # Using expWcs
        visitId = 9005000
        defocalSetting = 'extra'
        pix2arcsec = 0.2
        templateModel = 'model'
        donutImgSize = 160
        deblendRadius = 160
        doDeblending = False
        useExpWcs = True
        donut_df = self.db.identifyDonuts(self.repoDir, [visitId],
                                          defocalSetting,
                                          self.camera, pix2arcsec,
                                          templateModel,
                                          donutImgSize, deblendRadius,
                                          doDeblending, useExpWcs)

        self.assertTrue(len(donut_df), 2)
        np.testing.assert_array_equal(donut_df.blended.values, [False]*2)

        # Without using expWcs
        useExpWcs = False
        donut_df_2 = self.db.identifyDonuts(self.repoDir, [visitId],
                                            defocalSetting,
                                            self.camera, pix2arcsec,
                                            templateModel,
                                            donutImgSize, deblendRadius,
                                            doDeblending, useExpWcs)

        self.assertTrue(len(donut_df_2), 2)
        np.testing.assert_array_equal(donut_df_2.blended.values, [False]*2)

        # With deblending turned on
        doDeblending = True
        donut_df_3 = self.db.identifyDonuts(self.repoDir, [visitId],
                                            defocalSetting,
                                            self.camera, pix2arcsec,
                                            templateModel,
                                            donutImgSize, deblendRadius,
                                            doDeblending, useExpWcs)

        self.assertTrue(len(donut_df_3), 4)
        self.assertTrue(len(donut_df_3.query('blended == False')), 2)
        self.assertTrue(len(donut_df_3.query('blended == True')), 2)

        # With maxSensorStars set
        doDeblending = False
        donut_df_4 = self.db.identifyDonuts(self.repoDir, [visitId],
                                            defocalSetting,
                                            self.camera, pix2arcsec,
                                            templateModel,
                                            donutImgSize, deblendRadius,
                                            doDeblending, useExpWcs,
                                            maxSensorStars=1)

        self.assertTrue(len(donut_df_4), 1)

    def testWriteSkyFile(self):

        test_df = pd.DataFrame([[1, 0.0, 0.0, 15]],
                               columns=['id', 'ra', 'dec', 'mag'])
        self.db.writeSkyFile(test_df, os.path.join(self.dataDir, 'test.csv'))
        test_out = np.loadtxt(os.path.join(self.dataDir, 'test.csv'))
        np.testing.assert_array_equal(test_df.iloc[0].values[1:], test_out[1:])

    def testInsertDataFromImage(self):

        self._createTable()
        self._createParamFile()
        skyFileName = os.path.join(self.dataDir, 'skyFile.txt')
        instFileReader = ParamReader(self.paramFileName)
        self.db.insertDataFromImage(self.repoDir, instFileReader,
                                    [9005000], 'extra', self.filterType,
                                    self.camera, fileOut=skyFileName)
        idAll = self.db.getAllId(self.filterType)
        self.assertTrue(len(idAll), 2)


if __name__ == "__main__":

    # Do the unit test
    unittest.main()
