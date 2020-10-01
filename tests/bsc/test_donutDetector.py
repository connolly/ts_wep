import os
import shutil
import numpy as np
import pandas as pd
import unittest

import lsst.afw.image as afwImage
from lsst.ts.wep.bsc.DonutDetector import DonutDetector
from lsst.ts.wep.cwfs.TemplateUtils import createTemplateImage
from lsst.ts.wep.Utility import getModulePath, FilterType


class TestDonutDetector(unittest.TestCase):
    """Test the DonutDetector class."""

    def setUp(self):

        self.modulePath = getModulePath()

        self.testDir = os.path.join(self.modulePath, "tests")
        self.dataDir = os.path.join(self.modulePath, "tests", "tmp")
        self._makeDir(self.dataDir)

        self.filterType = FilterType.G
        self.extraTemplate = createTemplateImage('extra', 'R22_S11', 0.2,
                                                 'model', 160)

        self.extraDetector = DonutDetector(self.extraTemplate)

        self.image = afwImage.ImageF(1000, 1000)
        randState = np.random.RandomState(42)
        imageArr = np.zeros((1000, 1000)) + randState.normal(scale=10.,
                                                             size=(1000, 1000))
        imageArr[420:580, 420:580] = self.extraTemplate*100.
        imageArr[720:880, 720:880] = self.extraTemplate*200.
        imageArr[100:260, 100:260] = self.extraTemplate*100.
        imageArr[160:320, 100:260] = self.extraTemplate*100.
        self.image.array[:] = imageArr
        self.extraExp = afwImage.ExposureF(1000, 1000)
        self.extraExp.image = self.image

    def _makeDir(self, directory):

        if (not os.path.exists(directory)):
            os.makedirs(directory)

    def tearDown(self):

        shutil.rmtree(self.dataDir)

    def testThresholdExpFAndTemp(self):

        bExp, bTemplate, thresh = self.extraDetector.thresholdExpFAndTemp(self.extraExp)

        # Test that binary arrays are binary
        self.assertEqual(np.min(bExp.image.array), 0)
        self.assertEqual(np.max(bExp.image.array), 1)
        self.assertEqual(np.min(bTemplate), 0)
        self.assertEqual(np.max(bTemplate), 1)
        # Test that binary template is same size
        np.testing.assert_array_equal(np.shape(self.extraTemplate),
                                      np.shape(bTemplate))
        # Test that threshold is somewhere between min and max of image
        self.assertTrue(np.min(self.extraExp.image.array) < thresh)
        self.assertTrue(np.max(self.extraExp.image.array) > thresh)

        # Test with threshold specified. Results should be same.
        bExp2, bTemplate2, thresh2 = self.extraDetector.thresholdExpFAndTemp(
            self.extraExp,
            image_threshold=thresh
        )
        self.assertEqual(thresh, thresh2)
        np.testing.assert_array_equal(bExp.image.array, bExp2.image.array)
        np.testing.assert_array_equal(bTemplate, bTemplate2)

    def testDetectDonuts(self):

        # Test that we recover the right number of donuts
        imageDonutsDf, image_thresh = self.extraDetector.detectDonuts(
            self.extraExp, 160
        )
        self.assertEqual(len(imageDonutsDf), 4)

        # Sort dataframe for consistent test results
        imageDonutsDf = imageDonutsDf.sort_values(by='y_center')

        # Test recovery of blended donuts
        donut_info = imageDonutsDf.iloc[0]
        self.assertAlmostEqual(donut_info['x_center'], 180, delta=1.0)
        self.assertAlmostEqual(donut_info['y_center'], 180, delta=1.0)
        self.assertEqual(donut_info['blended'], True)
        self.assertEqual(donut_info['blended_with'],
                         imageDonutsDf.iloc[1].name)
        self.assertEqual(donut_info['num_blended_neighbors'], 1)

        donut_info = imageDonutsDf.iloc[1]
        self.assertAlmostEqual(donut_info['x_center'], 180, delta=1.0)
        self.assertAlmostEqual(donut_info['y_center'], 240, delta=1.0)
        self.assertEqual(donut_info['blended'], True)
        self.assertEqual(donut_info['blended_with'],
                         imageDonutsDf.iloc[0].name)
        self.assertEqual(donut_info['num_blended_neighbors'], 1)

        # Test recovery of isolated donuts
        donut_info = imageDonutsDf.iloc[2]
        self.assertAlmostEqual(donut_info['x_center'], 500, delta=1.0)
        self.assertAlmostEqual(donut_info['y_center'], 500, delta=1.0)
        self.assertEqual(donut_info['blended'], False)
        self.assertEqual(donut_info['blended_with'], None)
        self.assertEqual(donut_info['num_blended_neighbors'], 0)

        donut_info = imageDonutsDf.iloc[3]
        self.assertAlmostEqual(donut_info['x_center'], 800, delta=1.0)
        self.assertAlmostEqual(donut_info['y_center'], 800, delta=1.0)
        self.assertEqual(donut_info['blended'], False)
        self.assertEqual(donut_info['blended_with'], None)
        self.assertEqual(donut_info['num_blended_neighbors'], 0)

    def testLabelUnblended(self):

        testDonutDf = pd.DataFrame()
        testDonutDf['x_center'] = [500., 200., 220.]
        testDonutDf['y_center'] = [500., 200., 200.]

        testDonutDf = self.extraDetector.labelUnblended(
            testDonutDf, 10., 'x_center', 'y_center'
        )
        np.testing.assert_array_equal(testDonutDf['blended'],
                                      np.array([False]*3))
        np.testing.assert_array_equal(testDonutDf['blended_with'],
                                      np.array([None]*3))
        np.testing.assert_array_equal(testDonutDf['num_blended_neighbors'],
                                      np.zeros(3))

        testDonutDf_2 = pd.DataFrame()
        testDonutDf_2['x_center'] = [500., 200., 220.]
        testDonutDf_2['y_center'] = [500., 200., 200.]

        testDonutDf_2 = self.extraDetector.labelUnblended(
            testDonutDf_2, 30., 'x_center', 'y_center'
        )
        np.testing.assert_array_equal(testDonutDf_2['blended'],
                                      np.array([False, True, True]))
        np.testing.assert_array_equal(testDonutDf_2['blended_with'],
                                      np.array([None, [2], [1]]))
        np.testing.assert_array_equal(testDonutDf_2['num_blended_neighbors'],
                                      np.array([0, 1, 1]))

    def testRankUnblendedByFlux(self):

        imageDonutsDf, image_thresh = self.extraDetector.detectDonuts(
            self.extraExp, 160
        )

        unblendedDf = self.extraDetector.rankUnblendedByFlux(
            imageDonutsDf, self.extraExp
        )

        self.assertTrue(len(unblendedDf), 2)
        self.assertAlmostEqual(unblendedDf['x_center'].iloc[0],
                               800., delta=1.0)
        self.assertAlmostEqual(unblendedDf['y_center'].iloc[0],
                               800., delta=1.0)
        self.assertAlmostEqual(unblendedDf['x_center'].iloc[1],
                               500., delta=1.0)
        self.assertAlmostEqual(unblendedDf['x_center'].iloc[1],
                               500., delta=1.0)
        self.assertAlmostEqual(unblendedDf['flux'].iloc[0],
                               unblendedDf['flux'].iloc[1]*2, delta=5.0)

    def testCorrelateExposureWithImage(self):

        donutExp = afwImage.ExposureF(1000, 1000)
        donutExp.image = self.image
        corrExp = self.extraDetector.correlateExposureWithImage(donutExp,
                                                                self.image)

        # Peak value should be center of donut after correlation
        self.assertTrue(np.max(corrExp.image.array),
                        corrExp.image.array[500, 500])

    def testCorrelateImageWithImage(self):

        corrImage = self.extraDetector.correlateImageWithImage(self.image,
                                                               self.image)

        # Peak value should be center of the donut after correlation
        self.assertTrue(np.max(corrImage), corrImage[500, 500])


if __name__ == "__main__":

    # Do the unit test
    unittest.main()
