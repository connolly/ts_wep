import os

from lsst.ts.wep.bsc.Filter import Filter
from lsst.ts.wep.bsc.CamFactory import CamFactory
from lsst.ts.wep.bsc.DatabaseFactory import DatabaseFactory
from lsst.ts.wep.bsc.LocalDatabaseForStarFile import LocalDatabaseForStarFile
from lsst.ts.wep.bsc.LocalDatabaseFromImage import LocalDatabaseFromImage
from lsst.ts.wep.bsc.LocalDatabaseFromRefCat import LocalDatabaseFromRefCat
from lsst.ts.wep.Utility import mapFilterRefToG, getConfigDir
from lsst.ts.wep.ParamReader import ParamReader
from lsst.ts.wep.ctrlIntf.PhosimWcsSol import PhosimWcsSol


class SourceSelector(object):

    def __init__(self, camType, bscDbType, isrDir, settingFileName="default.yaml"):
        """Initialize the source selector class.

        Parameters
        ----------
        camType : enum 'CamType'
            Camera type.
        bscDbType : enum 'BscDbType'
            Bright star catalog (BSC) database type.
        settingFileName : str, optional
            Setting file name (the default is "default.yaml".)
        """

        settingFilePath = os.path.join(getConfigDir(), settingFileName)
        self.settingFile = ParamReader(filePath=settingFilePath)

        use_exp_wcs = self.settingFile.getSetting("expWcs")
        self.camera = CamFactory.createCam(camType)
        if use_exp_wcs is True:
            exp_wcs = PhosimWcsSol()
            rerunDir = self.settingFile.getSetting("rerunName")
            isrDir = os.path.join(isrDir, 'rerun', rerunDir)
            exp_wcs.setIsrDir(isrDir)
            self.camera._wcs = exp_wcs

        self.db = DatabaseFactory.createDb(bscDbType)
        self.filter = Filter()

        self.maxDistance = 0.0
        self.maxNeighboringStar = 0

        # Configurate the criteria of neighboring stars
        starRadiusInPixel = self.settingFile.getSetting("starRadiusInPixel")
        spacingCoefficient = self.settingFile.getSetting("spacingCoef")
        maxNeighboringStar = self.settingFile.getSetting("maxNumOfNbrStar")
        self.configNbrCriteria(starRadiusInPixel, spacingCoefficient,
                               maxNeighboringStar=maxNeighboringStar)

    def configNbrCriteria(self, starRadiusInPixel, spacingCoefficient,
                          maxNeighboringStar=0):
        """Set the neighboring star criteria to decide the scientific target.

        Parameters
        ----------
        starRadiusInPixel : float, optional
            Diameter of star. For the defocus = 1.5 mm, the star's radius is
            63 pixel.
        spacingCoefficient : float, optional
            Maximum distance in units of radius one donut must be considered
            as a neighbor.
        maxNeighboringStar : int, optional
            Maximum number of neighboring stars. (the default is 0.)
        """

        self.maxDistance = starRadiusInPixel * spacingCoefficient
        self.maxNeighboringStar = int(maxNeighboringStar)

    def connect(self, *args):
        """Connect the database.

        Parameters
        ----------
        *args : str or *list
            Information to connect to the database.
        """

        self.db.connect(*args)

    def disconnect(self):
        """Disconnect the database."""

        self.db.disconnect()

    def setFilter(self, filterType):
        """Set the filter type.

        Parameters
        ----------
        filterType : FilterType
            Filter type.
        """

        self.filter.setFilter(filterType)

    def getFilter(self):
        """Get the filter type.

        Returns
        -------
        FilterType
            Filter type.
        """

        return self.filter.getFilter()

    def setObsMetaData(self, ra, dec, rotSkyPos):
        """Set the observation meta data.

        Parameters
        ----------
        ra : float
            Pointing ra in degree.
        dec : float
            Pointing decl in degree.
        rotSkyPos : float
            The orientation of the telescope in degrees.
        """

        mjd = self.settingFile.getSetting("cameraMJD")
        self.camera.setObsMetaData(ra, dec, rotSkyPos, mjd=mjd)

    def getTargetStar(self, offset=0):
        """Get the target stars by querying the database.

        Parameters
        ----------
        offset : float, optional
            Offset to the dimension of camera. If the detector dimension is 10
            (assume 1-D), the star's position between -offset and 10+offset
            will be seem to be on the detector. (the default is 0.)

        Returns
        -------
        dict
            Information of neighboring stars and candidate stars with the name
            of sensor as a dictionary.
        dict
            Information of stars with the name of sensor as a dictionary.
        dict
            (ra, dec) of four corners of each sensor with the name
            of sensor as a list. The dictionary key is the sensor name.
        """

        # Map the reference filter to the G filter
        filterType = self.getFilter()
        mappedFilterType = mapFilterRefToG(filterType)

        wavefrontSensors = self.camera.getWavefrontSensor()
        lowMagnitude, highMagnitude = self.filter.getMagBoundary()

        # Query the star database
        starMap = dict()
        neighborStarMap = dict()
        for detector, wavefrontSensor in wavefrontSensors.items():

            # Get stars in this wavefront sensor for this observation field
            stars = self.db.query(mappedFilterType, wavefrontSensor[0],
                                  wavefrontSensor[1], wavefrontSensor[2],
                                  wavefrontSensor[3])

            # Set the detector information for the stars
            stars.setDetector(detector)

            # Populate pixel information for stars
            populatedStar = self.camera.populatePixelFromRADecl(stars)


            # Get the stars that are on the detector
            starsOnDet = self.camera.getStarsOnDetector(populatedStar, offset)
            starMap[detector] = starsOnDet

            # Check the candidate of bright stars based on the magnitude
            indexCandidate = starsOnDet.checkCandidateStars(
                mappedFilterType, lowMagnitude, highMagnitude)

            # Determine the neighboring stars based on the distance and
            # allowed number of neighboring stars
            neighborStar = starsOnDet.getNeighboringStar(
                indexCandidate, self.maxDistance, mappedFilterType,
                self.maxNeighboringStar)
            neighborStarMap[detector] = neighborStar

        # Remove the data that has no bright star
        self._rmDataWithoutBrightStar(neighborStarMap, starMap,
                                      wavefrontSensors)

        return neighborStarMap, starMap, wavefrontSensors

    def _rmDataWithoutBrightStar(self, neighborStarMap, starMap,
                                 wavefrontSensors):
        """Remove the data that has no bright stars on the detector.

        The data in inputs will be changed directly.

        Parameters
        ----------
        neighborStarMap : dict
            Information of neighboring stars and candidate stars with the name
            of sensor as a dictionary.
        starMap : dict
            Information of stars with the name of sensor as a dictionary.
        wavefrontSensors : dict
            (ra, dec) of four corners of each sensor with the name
            of sensor as a list. The dictionary key is the sensor name.
        """

        # Collect the sensor list without the bright star
        noStarSensorList = []
        for detector, stars in neighborStarMap.items():
            if (len(stars.getId()) == 0):
                noStarSensorList.append(detector)

        # Remove the data in map
        for detector in noStarSensorList:
            neighborStarMap.pop(detector)
            starMap.pop(detector)
            wavefrontSensors.pop(detector)

    def getTargetStarByFile(self, skyFilePath, visitList, offset=0):
        """Get the target stars by querying the star file.

        This function is only for the test. This shall be removed in the final.

        Parameters
        ----------
        skyFilePath : str
            Sky data file path.
        offset : float, optional
            Offset to the dimension of camera. If the detector dimension is 10
            (assume 1-D), the star's position between -offset and 10+offset
            will be seem to be on the detector. (the default is 0.)

        Returns
        -------
        dict
            Information of neighboring stars and candidate stars with the name
            of sensor as a dictionary.
        dict
            Information of stars with the name of sensor as a dictionary.
        dict
            (ra, dec) of four corners of each sensor with the name
            of sensor as a list. The dictionary key is the sensor name.

        Raises
        ------
        TypeError
            The database type is incorrect.
        """
        if (not type(self.db) == LocalDatabaseForStarFile):
            errorString = "The database type is incorrect."
            errorString += " Received type: {} but expected type: {}".format(
                type(self.db),LocalDatabaseForStarFile)
            raise TypeError(errorString)

        # Map the reference filter to the G filter
        filterType = self.getFilter()
        mappedFilterType = mapFilterRefToG(filterType)

        if type(self.camera._wcs) == PhosimWcsSol:
            self.camera._wcs.setWcsDataFromIsrDir(mappedFilterType,
                                                  self.camera.getWfsCcdList(),
                                                  visitList[0])

        # Write the sky data into the temporary table
        self.db.createTable(mappedFilterType)
        self.db.insertDataByFile(skyFilePath, mappedFilterType, skiprows=1)
        neighborStarMap, starMap, wavefrontSensors = self.getTargetStar(offset=offset)

        # Delete the table
        self.db.deleteTable(mappedFilterType)

        return neighborStarMap, starMap, wavefrontSensors

    def getTargetStarFromImage(self, butlerRootPath, visitList, defocalState,
                               offset=0):

        if (not type(self.db) == LocalDatabaseFromImage):
            errorString = "The database type is incorrect."
            errorString += " Received type: {} but expected type: {}".format(
                type(self.db),
                LocalDatabaseFromImage
                )
            raise TypeError(errorString)

        filterType = self.getFilter()
        mappedFilterType = mapFilterRefToG(filterType)

        if type(self.camera._wcs) == PhosimWcsSol:
            self.camera._wcs.setWcsDataFromIsrDir(mappedFilterType,
                                                  self.camera.getWfsCcdList(),
                                                  visitList[0])

        self.db.createTable(mappedFilterType)

        self.db.insertDataFromImage(butlerRootPath, self.settingFile,
                                    visitList, defocalState,
                                    mappedFilterType,
                                    self.camera, skiprows=1)
        neighborStarMap, starMap, wavefrontSensors = self.getTargetStar(offset=offset)

        # Delete the table
        self.db.deleteTable(mappedFilterType)

        return neighborStarMap, starMap, wavefrontSensors

    def getTargetStarFromRefCat(self, butlerRootPath, visitList, defocalState,
                                offset=0):

        if (not type(self.db) == LocalDatabaseFromRefCat):
            errorString = "The database type is incorrect."
            errorString += " Received type: {} but expected type: {}".format(
                type(self.db),
                LocalDatabaseFromRefCat
                )
            raise TypeError(errorString)

        filterType = self.getFilter()
        mappedFilterType = mapFilterRefToG(filterType)

        if type(self.camera._wcs) == PhosimWcsSol:
            self.camera._wcs.setWcsDataFromIsrDir(mappedFilterType,
                                                  self.camera.getWfsCcdList(),
                                                  visitList[0])

        self.db.createTable(mappedFilterType)

        self.db.insertDataFromRefCat(butlerRootPath, self.settingFile,
                                     visitList, defocalState,
                                     mappedFilterType,
                                     self.camera, skiprows=1)
        neighborStarMap, starMap, wavefrontSensors = self.getTargetStar(offset=offset)

        # Delete the table
        self.db.deleteTable(mappedFilterType)

        return neighborStarMap, starMap, wavefrontSensors


if __name__ == "__main__":
    pass
