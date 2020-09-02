import numpy as np
from lsst.ts.wep.ctrlIntf.AstWcsSol import AstWcsSol
from lsst.ts.wep.Utility import abbrevDetectorName, parseAbbrevDetectorName
from lsst.daf.persistence import Butler
from lsst import geom

class PhosimWcsSol(AstWcsSol):
    """World coordinate system (WCS) solution provided in Phosim headers."""

    def setIsrDir(self, isrDir):

        self.isrDir = isrDir

    def setWcsDataFromIsrDir(self, filterType, ccdList, visitNum):

        self.butler = Butler(self.isrDir)
        wcsData = {}

        for detector in ccdList:
            abbrevName = abbrevDetectorName(detector)
            raft, sensor = parseAbbrevDetectorName(abbrevName)

            data_id = {'visit': visitNum, 'filter': filterType.toString(),
                       'raftName': raft, 'detectorName': sensor}
            print(data_id)

            exp = self.butler.get('postISRCCD', **data_id)
            w = exp.getWcs()
            wcsData[detector] = w

        self.wcsData = wcsData

    def setObsMetaData(self, ra, dec, rotSkyPos, mjd=59580.0):
        """Set the observation meta data.

        Parameters
        ----------
        ra : float
            Pointing ra in degree.
        dec : float
            Pointing decl in degree.
        rotSkyPos : float
            The orientation of the telescope in degrees.
        mjd : float
            Camera MJD. (the default is 59580.0.)
        """

        pass

    def raDecFromPixelCoords(self, xPix, yPix, chipName, epoch=2000.0,
                             includeDistortion=True):
        """Convert pixel coordinates into RA, Dec.

        WARNING: This method does not account for apparent motion due to
        parallax. This method is only useful for mapping positions on a
        theoretical focal plane to positions on the celestial sphere.

        Parameters
        ----------
        xPix : float or numpy.ndarray
            xPix is the x pixel coordinate.
        yPix : float or numpy.ndarray
            yPix is the y pixel coordinate.
        chipName : str or numpy.ndarray
            chipName is the name of the chip(s) on which the pixel coordinates
            are defined.  This can be an array (in which case there should be
            one chip name for each (xPix, yPix) coordinate pair), or a single
            value (in which case, all of the (xPix, yPix) points will be
            reckoned on that chip).
        epoch : float, optional
            epoch is the mean epoch in years of the celestial coordinate
            system. (the default is 2000.0.)
        includeDistortion : bool, optional
            If True (default), then this method will expect the true pixel
            coordinates with optical distortion included.  If False, this
            method will expect TAN_PIXEL coordinates, which are the pixel
            coordinates with estimated optical distortion removed. See the
            documentation in afw.cameraGeom for more details. (the default is
            True.)

        Returns
        -------
        numpy.ndarray
            A 2-D numpy array in which the first row is the RA coordinate and
            the second row is the Dec coordinate (both in degrees; in the
            International Celestial Reference System).
        """

        if isinstance(chipName, np.ndarray):
            chipNameList = chipName.tolist()
        else:
            chipNameList = chipName

        if type(xPix) is float:
            xPix = [xPix]
        if type(yPix) is float:
            yPix = [yPix]

        assert len(xPix) == len(yPix), "xPix and yPix must be same length"

        raDecList = []

        if type(chipNameList) == str:
            for xp, yp in zip(xPix, yPix):
                raDecSpherePt = self.wcsData[chipNameList].pixelToSky(geom.Point2D(xp, yp))
                raDecPt = [raDecSpherePt.getRa().asDegrees(), raDecSpherePt.getDec().asDegrees()]
                raDecList.append(raDecPt)
            raDec = np.array(raDecList).T

        elif type(chipNameList) == list:

            assertMsg = "If chipName is not a str it must be list or array of same length as xPix and yPix"
            assert len(chipNameList) == len(xPix), assertMsg

            for xp, yp, chipId in zip(xPix, yPix, chipNameList):
                raDecSpherePt = self.wcsData[chipId].pixelToSky(geom.Point2D(xp, yp))
                raDecPt = [raDecSpherePt.getRa().asDegrees(), raDecSpherePt.getDec().asDegrees()]
                raDecList.append(raDecPt)
            raDec = np.array(raDecList).T

        return raDec

    def pixelCoordsFromRaDec(self, ra, dec, chipName, epoch=2000.0,
                             includeDistortion=True):
        """Get the pixel positions (or nan if not on a chip) for objects based
        on their RA, and Dec (in degrees).

        Parameters
        ----------
        ra : float or numpy.ndarray
            ra is in degrees in the International Celestial Reference System.
        dec : float or numpy.ndarray
            dec is in degrees in the International Celestial Reference System.
        chipName : numpy.ndarray, str
            chipName designates the names of the chips on which the pixel
            coordinates will be reckoned. If an array, there must be as many
            chipNames as there are (RA, Dec) pairs. If a single value, all of
            the pixel coordinates will be reckoned on the same chip. If None,
            this method will calculate which chip each(RA, Dec) pair actually
            falls on, and return pixel coordinates for each (RA, Dec) pair on
            the appropriate chip. (the default is None.)
        epoch : float, optional
            epoch is the mean epoch in years of the celestial coordinate
            system. (the default is 2000.0.)
        includeDistortion : bool, optional
            If True (default), then this method will expect the true pixel
            coordinates with optical distortion included.  If False, this
            method will expect TAN_PIXEL coordinates, which are the pixel
            coordinates with estimated optical distortion removed. See the
            documentation in afw.cameraGeom for more details. (the default is
            True.)

        Returns
        -------
        numpy.ndarray
            A 2-D numpy array in which the first row is the x pixel coordinate
            and the second row is the y pixel coordinate.
        """

        if isinstance(chipName, np.ndarray):
            chipNameList = chipName.tolist()
        else:
            chipNameList = chipName

        if type(ra) is float:
            ra = [ra]
        if type(dec) is float:
            dec = [dec]

        assert len(ra) == len(dec), "ra and dec must be same length"

        pixelList = []

        if type(chipNameList) == str:
            for raVal, decVal in zip(ra, dec):
                pixelPt = self.wcsData[chipNameList].skyToPixel(
                    geom.SpherePoint(raVal, decVal, geom.degrees)
                    )
                pixelList.append(pixelPt)
            pixelCoords = np.array(pixelList).T

        elif type(chipNameList) == list:
            for raVal, decVal, chipId in zip(ra, dec, chipNameList):
                pixelPt = self.wcsData[chipId].skyToPixel(
                    geom.SpherePoint(raVal, decVal, geom.degrees)
                    )
                pixelList.append(pixelPt)
            pixelCoords = np.array(pixelList).T

        return pixelCoords


if __name__ == "__main__":
    pass
