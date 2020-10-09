import os
import shutil
import numpy as np
import pandas as pd
import unittest

from lsst.daf.persistence import Butler
from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask
from lsst.ts.wep.bsc.LocalDatabaseFromRefCat import LocalDatabaseFromRefCat
from lsst.ts.wep.bsc.CamFactory import CamFactory
from lsst.ts.wep.Utility import getModulePath, FilterType, CamType
from lsst.ts.wep.ParamReader import ParamReader


class TestLocalDatabaseFromRefCat(unittest.TestCase):
    """Test the local database from reference catalog."""

    def setUp(self):

        self.modulePath = getModulePath()

        self.dataDir = os.path.join(self.modulePath, "tests", "tmp")
        self._makeDir(self.dataDir)

        self.repoDir = os.path.join(self.modulePath, "tests", "testData",
                                    "testRepo", "rerun", "run1")
        self.butler = Butler(self.repoDir)
        self.refCatRepo = os.path.join(self.modulePath, "tests", "testData",
                                       "sampleGaiaPhosim", "gaiaTestRef")
        self.refButler = Butler(self.refCatRepo)

        self.filterType = FilterType.G
        self.camera = CamFactory.createCam(CamType.ComCam)
        self.camera.setObsMetaData(0., 0., 0.)
        self.camera.setWfsCcdList(["R:2,2 S:1,1"])
        self.db = LocalDatabaseFromRefCat()

        dbAddress = os.path.join(self.modulePath, "tests", "testData",
                                 "bsc.db3")
        self.db.connect(dbAddress)

    def _makeDir(self, directory):

        if (not os.path.exists(directory)):
            os.makedirs(directory)

    def _createParamFile(self):

        self.paramFileName = os.path.join(self.dataDir, 'default.yaml')
        paramDict = {'expWcs': 'False', 'centroidTemplateType': 'model',
                     'donutImgSizeInPixel': 160, 'minUnblendedDistance': 160,
                     'doDeblending': False, 'maxSensorStars': 'null',
                     'pixelToArcsec': 0.2, 'blendMagDiff': 2,
                     'refCatDir': self.refCatRepo}
        with open(self.paramFileName, 'w') as f:
            for key in paramDict.keys():
                f.write('{}: {}\n'.format(key, paramDict[key]))

    def tearDown(self):

        self.db.deleteTable(self.filterType)
        self.db.disconnect()

        shutil.rmtree(self.dataDir)

    def _createTable(self):
        self.db.createTable(self.filterType)

    def testMakeSourceCat(self):

        df = pd.DataFrame()
        df['x_center'] = [1000., 1200.]
        df['y_center'] = [1000., 1200.]
        sourceCat = self.db.makeSourceCat(df)

        self.assertTrue(len(sourceCat), 2)

    def testIdentifyDonuts(self):

        # Using expWcs
        visitId = 9006041
        defocalSetting = 'extra'
        pix2arcsec = 0.2
        templateModel = 'model'
        donutImgSize = 160
        deblendRadius = 160
        doDeblending = False
        blendDiffLimit = None
        useExpWcs = False
        refObjLoader = LoadIndexedReferenceObjectsTask(butler=self.refButler)
        donut_df = self.db.identifyDonuts(self.repoDir, [visitId],
                                          self.filterType, defocalSetting,
                                          self.camera, pix2arcsec,
                                          templateModel,
                                          donutImgSize, deblendRadius,
                                          doDeblending, blendDiffLimit,
                                          useExpWcs, refObjLoader)

        self.assertTrue(len(donut_df), 45)

    def testSolveWCS(self):

        exp = self.butler.get('postISRCCD', **{'visit': 9006041, 'filter': 'g',
                                               'raftName': 'R22',
                                               'detectorName': 'S11'})
        refObjLoader = LoadIndexedReferenceObjectsTask(butler=self.refButler)
        srcCatFile = os.path.join(self.modulePath, "tests", "testData",
                                  "sampleGaiaPhosim", 'source_donut_df_S11.csv')
        df = pd.read_csv(srcCatFile)
        srcCat = self.db.makeSourceCat(df)
        results, newWcs = self.db.solveWCS(exp, srcCat, refObjLoader)

        self.assertGreater(len(results.refCat), len(df))
        self.assertIsInstance(newWcs, type(exp.getWcs()))

    def testInsertDataFromRefCat(self):

        self._createTable()
        self._createParamFile()
        skyFileName = os.path.join(self.dataDir, 'skyFile.txt')
        instFileReader = ParamReader(self.paramFileName)
        self.db.insertDataFromRefCat(self.repoDir, instFileReader,
                                     [9006041], 'extra', self.filterType,
                                     self.camera, fileOut=skyFileName)
        idAll = self.db.getAllId(self.filterType)
        self.assertTrue(len(idAll), 45)


if __name__ == "__main__":

    # Do the unit test
    unittest.main()
