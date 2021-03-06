# This file is part of ts_wep.
#
# Developed for the LSST Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import unittest
import numpy as np

from lsst.ts.wep.ctrlIntf.SensorWavefrontError import SensorWavefrontError


class TestSensorWavefrontError(unittest.TestCase):
    """Test the SensorWavefrontError class."""

    def setUp(self):

        self.numOfZk = 19
        self.sensorWavefrontError = SensorWavefrontError(numOfZk=self.numOfZk)

        self.sensorId = 999

    def testGetNumOfZk(self):

        self.assertEqual(self.sensorWavefrontError.getNumOfZk(), self.numOfZk)

    def testGetSensorId(self):

        sensorId = self.sensorWavefrontError.getSensorId()
        self.assertEqual(sensorId, self.sensorId)
        self.assertTrue(isinstance(sensorId, int))

    def testSetSensorId(self):

        sensorId = 2
        self.sensorWavefrontError.setSensorId(sensorId)

        sensorIdInObject = self.sensorWavefrontError.getSensorId()
        self.assertEqual(sensorIdInObject, sensorId)

    def testSetSensorIdWithFloatInputType(self):

        sensorId = 2.0
        self.sensorWavefrontError.setSensorId(sensorId)

        sensorIdInObject = self.sensorWavefrontError.getSensorId()
        self.assertTrue(isinstance(sensorIdInObject, int))
        self.assertEqual(sensorIdInObject, sensorId)

    def testSetSensorIdWithValueLessThanZero(self):

        self.assertRaises(ValueError, self.sensorWavefrontError.setSensorId, -1)

    def testGetAnnularZernikePoly(self):

        annularZernikePoly = self.sensorWavefrontError.getAnnularZernikePoly()

        self.assertEqual(len(annularZernikePoly), self.numOfZk)
        self.assertTrue(isinstance(annularZernikePoly, np.ndarray))

        delta = np.sum(np.abs(annularZernikePoly))
        self.assertEqual(delta, 0)

    def testSetAnnularZernikePoly(self):

        randValue = np.random.rand(self.numOfZk)
        self.sensorWavefrontError.setAnnularZernikePoly(randValue)

        valueInObj = self.sensorWavefrontError.getAnnularZernikePoly()

        delta = np.sum(np.abs(randValue - valueInObj))
        self.assertEqual(delta, 0)

    def testSetAnnularZernikePolyWithListInput(self):

        listValue = [1] * self.numOfZk
        self.sensorWavefrontError.setAnnularZernikePoly(listValue)

        valueInObj = self.sensorWavefrontError.getAnnularZernikePoly()
        self.assertEqual(np.sum(valueInObj), self.numOfZk)

    def testSetAnnularZernikePolyWithWrongLength(self):

        wrongValue = np.ones(self.numOfZk + 1)
        self.assertRaises(
            ValueError, self.sensorWavefrontError.setAnnularZernikePoly, wrongValue
        )


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
