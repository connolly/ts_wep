import os
import warnings

from lsst.ts.wep.Utility import getModulePath, getConfigDir, BscDbType, \
    FilterType, abbrevDectectorName, getBscDbType, getImageType, \
    getCentroidFindType, ImageType, DefocalType
from lsst.ts.wep.CamDataCollector import CamDataCollector
from lsst.ts.wep.CamIsrWrapper import CamIsrWrapper
from lsst.ts.wep.SourceProcessor import SourceProcessor
from lsst.ts.wep.SourceSelector import SourceSelector
from lsst.ts.wep.WfEstimator import WfEstimator
from lsst.ts.wep.WepController import WepController
from lsst.ts.wep.ctrlIntf.SensorWavefrontData import SensorWavefrontData
from lsst.ts.wep.ParamReader import ParamReader
from lsst.ts.wep.ctrlIntf.MapSensorNameAndId import MapSensorNameAndId


class WEPCalculation(object):
    """Base class for converting the wavefront images into wavefront errors.

    There will be different implementations of this for different
    types of CCDs (normal, full array mode, comcam, cmos, shwfs).
    """

    def __init__(self, astWcsSol, camType, isrDir,
                 settingFileName="default.yaml"):
        """Construct an WEP calculation object.

        Parameters
        ----------
        astWcsSol : AstWcsSol
            AST world coordinate system (WCS) solution.
        camType : enum 'CamType'
            Camera type.
        isrDir : str
            Instrument signature remocal (ISR) directory. This directory will
            have the input and output that the data butler needs.
        settingFileName : str, optional
            Setting file name. (the default is "default.yaml".)
        """

        super().__init__()

        # This attribute is just a stakeholder here since there is no detail of
        # AST WCS solution yet
        self.astWcsSol = astWcsSol

        # ISR directory that the data butler uses
        self.isrDir = isrDir

        # Boresight infomation
        self.raInDeg = 0.0
        self.decInDeg = 0.0

        # Sky rotation angle
        self.rotSkyPos = 0.0

        # Sky information file for the temporary use
        self.skyFile = ""

        # Default setting file
        settingFilePath = os.path.join(getConfigDir(), settingFileName)
        self.settingFile = ParamReader(filePath=settingFilePath)

        # Configure the WEP controller
        self.wepCntlr = self._configWepController(camType, settingFileName)

    def _configWepController(self, camType, settingFileName):
        """Configure the WEP controller.

        WEP: wavefront estimation pipeline.

        Parameters
        ----------
        camType : enum 'CamType'
            Camera type.
        settingFileName : str
            Setting file name.

        Returns
        -------
        WepController
            Configured WEP controller.
        """

        dataCollector = CamDataCollector(self.isrDir)
        isrWrapper = CamIsrWrapper(self.isrDir)

        bscDbType = self._getBscDbType()
        sourSelc = self._configSourceSelector(camType, bscDbType,
                                              settingFileName)

        sourProc = SourceProcessor(settingFileName=settingFileName)
        wfsEsti = self._configWfEstimator(camType)

        wepCntlr = WepController(dataCollector, isrWrapper, sourSelc,
                                 sourProc, wfsEsti)

        return wepCntlr

    def _getBscDbType(self):
        """Get the bright star catalog (BSC) database type.

        Returns
        -------
        enum 'BscDbType'
            BSC database type.
        """

        bscDb = self.settingFile.getSetting("bscDbType")

        return getBscDbType(bscDb)

    def _configSourceSelector(self, camType, bscDbType, settingFileName):
        """Configue the source selector.

        Parameters
        ----------
        camType : enum 'CamType'
            Camera type.
        bscDbType : enum 'BscDbType'
            Bright star catalog (BSC) database type.
        settingFileName : str
            Setting file name.

        Returns
        -------
        SourceSelector
            Configured source selector.
        """

        sourSelc = SourceSelector(camType, bscDbType,
                                  settingFileName=settingFileName)
        sourSelc.setFilter(FilterType.REF)

        return sourSelc

    def _configWfEstimator(self, camType):
        """Configure the wavefront estimator.

        Returns
        -------
        WfEstimator
            Configured wavefront estimator.
        """

        configDir = getConfigDir()
        instDir = os.path.join(configDir, "cwfs", "instData")
        algoDir = os.path.join(configDir, "cwfs", "algo")
        wfsEsti = WfEstimator(instDir, algoDir)

        solver = self.settingFile.getSetting("poissonSolver")
        opticalModel = self.settingFile.getSetting("opticalModel")
        defocalDistInMm = self.settingFile.getSetting("defocalDistInMm")
        donutImgSizeInPixel = self.settingFile.getSetting("donutImgSizeInPixel")

        centroidFind = self.settingFile.getSetting("centroidFindAlgo")
        centroidFindType = getCentroidFindType(centroidFind)

        wfsEsti.config(solver=solver, camType=camType,
                       opticalModel=opticalModel,
                       defocalDisInMm=defocalDistInMm,
                       sizeInPix=donutImgSizeInPixel,
                       centroidFindType=centroidFindType)

        return wfsEsti

    def getSettingFile(self):
        """Get the setting file.

        Returns
        -------
        ParamReader
            Setting file.
        """

        return self.settingFile

    def getWepCntlr(self):
        """Get the configured WEP controller.

        Returns
        -------
        WepController
            Configured WEP controller.
        """

        return self.wepCntlr

    def getIsrDir(self):
        """Get the instrument signature removal (ISR) directory.

        This directory will have the input and output that the data butler
        needs.

        Returns
        -------
        str
            ISR directory.
        """

        return self.isrDir

    def setSkyFile(self, skyFile):
        """Set the sky information file.

        This is a temporary function to set the star file generated by
        ts_tcs_wep_phosim module to do the query. This function will be removed
        after we begin to integrate the bright star catalog database.

        Parameters
        ----------
        skyFile : str
            Sky information file.
        """

        self.skyFile = skyFile

    def getSkyFile(self):
        """Get the sky information file.

        Returns
        -------
        str
            Sky information file.
        """

        return self.skyFile

    def setWcsData(self, wcsData):
        """Set the WCS data.

        Parameters
        ----------
        wcsData : WcsData
            WCS data used in the WCS solution.
        """

        self.astWcsSol.setWcsData(wcsData)

    def setFilter(self, filterType):
        """Set the current filter.

        Parameters
        ----------
        filterType : enum 'FilterType'
            The new filter configuration to use for WEP data processing.
        """

        sourSelc = self.wepCntlr.getSourSelc()
        sourSelc.setFilter(filterType)

    def getFilter(self):
        """Get the current filter.

        Returns
        -------
        enum 'FilterType'
            The current filter configuration to use for WEP data processing.
        """

        sourSelc = self.wepCntlr.getSourSelc()
        return sourSelc.getFilter()

    def setBoresight(self, raInDeg, decInDeg):
        """Set the boresight (ra, dec) in degree from the pointing component.

        The cooridinate system of pointing component is the international
        cannabinoid research society (ICRS).

        Parameters
        ----------
        raInDeg : float
            Right ascension in degree. The value should be in (0, 360).
        decInDeg : float
            Declination in degree. The value should be in (-90, 90).
        """

        self.raInDeg = raInDeg
        self.decInDeg = decInDeg

    def getBoresight(self):
        """Get the boresight (ra, dec) defined in the international
        cannabinoid research society (ICRS).

        Returns
        -------
        raInDeg : float
            Right ascension in degree. The value should be in (0, 360).
        decInDeg : float
            Declination in degree. The value should be in (-90, 90).
        """

        return self.raInDeg, self.decInDeg

    def setRotAng(self, rotAngInDeg):
        """Set the camera rotation angle in degree from the camera rotator
        control system.

        Parameters
        ----------
        rotAngInDeg : float
            The camera rotation angle in degree (-90 to 90).
        """

        # In the WCS solution provided by SIMS team, the input angle is sky
        # rotation angle. We do not know its relationship with the camera
        # rotation angle yet.

        self.rotSkyPos = rotAngInDeg

    def getRotAng(self):
        """Get the camera rotation angle in degree defined in the camera
        rotator control system.

        Returns
        -------
        float
            The camera rotation angle in degree.
        """

        # In the WCS solution provided by SIMS team, the input angle is sky
        # rotation angle. We do not know its relationship with the camera
        # rotation angle yet.

        return self.rotSkyPos

    def calculateWavefrontErrors(self, rawExpData, extraRawExpData=None,postageImg=False,
                                postageImgDir=None,lowMagnitude=None, highMagnitude=None,
                                sensorNameToIdFileName='sensorNameToId.yaml'):
        """Calculate the wavefront errors.

        Parameters
        ----------
        rawExpData : RawExpData
            Raw exposure data for the corner wavefront sensor. If the input of
            extraRawExpData is not None, this input will be the intra-focal raw
            exposure data.
        extraRawExpData : RawExpData, optional
            This is the extra-focal raw exposure data if not None. (the default
            is None.
        postageImg : True/False - whether to save postage stamp images of donuts
        postageImgDir : a directory where to save them
        lowMagnitude, highMagnitude : magnitude limits for stars used to calculate
            wavefront errors. If none, the limits are read from ts/wep/bsc/Filter.py
            file. This can be used to explore the dependence of WFS calculation
            on star magnitude in an input star catalog.


        Returns
        -------
        list[SensorWavefrontData]
            List of SensorWavefrontData object.

        Raises
        ------
        ValueError
            Corner WFS is not supported yet.
        ValueError
            Only single visit is allowed at this time.
        """

        if (extraRawExpData is None):
            #raise ValueError("Corner WFS is not supported yet.")
            print('Calculating wavefront error for corner WFS ')

        if (len(rawExpData.getVisit()) != 1):
            raise ValueError("Only single visit is allowed at this time.")

        # When evaluating the eimage, the calibration products are not needed.
        # Therefore, need to make sure the camera mapper file exists.
        self._genCamMapperIfNeed()

        # Ingest the exposure data and do the ISR
        self._ingestImg(rawExpData)
        if (extraRawExpData is not None):
            self._ingestImg(extraRawExpData)

        # Only the amplifier image needs to do the ISR
        imgType = self._getImageType()
        if (imgType == ImageType.Amp):
            self._doIsr(isrConfigfileName="isr_config.py")

        # Set the butler inputs path to get the images
        butlerRootPath = self._getButlerRootPath()
        self.wepCntlr.setPostIsrCcdInputs(butlerRootPath)

        # Get visit list
        intraObsIdList = rawExpData.getVisit()

        # Get the target stars map neighboring stars
        neighborStarMap = self._getTargetStar(intraObsIdList,
                                              DefocalType.Intra,
                                              lowMagnitude=lowMagnitude,
                                              highMagnitude=highMagnitude)

        # Calculate the wavefront error
        intraObsId = intraObsIdList[0]
        if (extraRawExpData is None):
            obsIdList = [intraObsId]
        else:
            extraObsIdList = extraRawExpData.getVisit()
            extraObsId = extraObsIdList[0]
            obsIdList = [intraObsId, extraObsId]

        donutMap = self._calcWfErr(neighborStarMap, obsIdList,
                                   postageImg, postageImgDir)

        listOfWfErr = self._populateListOfSensorWavefrontData(donutMap,sensorNameToIdFileName)

        return listOfWfErr

    def _genCamMapperIfNeed(self):
        """Generate the camera mapper file if it is needed.

        The mapper file is used by the data butler.

        Raises
        ------
        ValueError
            Mapper is not supported yet.
        """

        mapperFile = os.path.join(self.isrDir, "_mapper")
        if (not os.path.exists(mapperFile)):

            dataCollector = self.wepCntlr.getDataCollector()

            camMapper = self.settingFile.getSetting("camMapper")
            if (camMapper == "phosim"):
                dataCollector.genPhoSimMapper()
            else:
                raise ValueError("Mapper (%s) is not supported yet." % camMapper)

    def _ingestImg(self, rawExpData):
        """Ingest the images.

        Parameters
        ----------
        rawExpData : RawExpData
            Raw exposure data.
        """

        dataCollector = self.wepCntlr.getDataCollector()

        rawExpDirList = rawExpData.getRawExpDir()
        for rawExpDir in rawExpDirList:

            imgType = self._getImageType()
            if (imgType == ImageType.Amp):
                rawImgFiles = os.path.join(rawExpDir, "*_a_*.fits*")
                dataCollector.ingestImages(rawImgFiles)
            elif (imgType == ImageType.Eimg):
                rawImgFiles = os.path.join(rawExpDir, "*_e_*.fits*")
                dataCollector.ingestEimages(rawImgFiles)

    def _getImageType(self):
        """Get the image type defined in the configuration file.

        Returns
        -------
        enum 'ImageType'
            ImageType enum.
        """

        imgType = self.settingFile.getSetting("imageType")

        return getImageType(imgType)

    def _doIsr(self, isrConfigfileName, rerunName=None):
        """Do the instrument signature removal (ISR).

        Parameters
        ----------
        isrConfigfileName : str
            ISR configuration file name.
        """

        isrWrapper = self.wepCntlr.getIsrWrapper()
        isrWrapper.config(doFlat=True, doOverscan=True, fileName=isrConfigfileName)
        if rerunName is None:
            rerunName = self._getIsrRerunName()
        isrWrapper.doISR(self.isrDir, rerunName=rerunName)

    def _getIsrRerunName(self):
        """Get the instrument signature removal (ISR) rerun name.

        Returns
        -------
        str
            ISR rerun name.
        """

        return self.settingFile.getSetting("rerunName")

    def _getButlerRootPath(self):
        """Get the butler root path based on the image type.

        Returns
        -------
        str
            Butler root path.
        """

        imgType = self._getImageType()
        if (imgType == ImageType.Amp):
            rerunName = self._getIsrRerunName()
            return os.path.join(self.isrDir, "rerun", rerunName)
        elif (imgType == ImageType.Eimg):
            return self.isrDir

    def _getTargetStar(self, visitList, defocalState, lowMagnitude=None, highMagnitude=None):
        """Get the target stars

        Returns
        -------
        dict
            Information of neighboring stars and candidate stars with the name
            of sensor as a dictionary.

        Raises
        ------
        ValueError
            WEPCalculation does not support this BSC yet.
        """

        # Connect the database
        sourSelc = self.wepCntlr.getSourSelc()
        bscDbType = self._getBscDbType()
        if bscDbType in (BscDbType.LocalDb, BscDbType.LocalDbForStarFile,
                         BscDbType.LocalDbFromImage, BscDbType.LocalDbFromRefCat):
            dbRelativePath = self.settingFile.getSetting("defaultBscPath")
            dbAdress = os.path.join(getModulePath(), dbRelativePath)
            sourSelc.connect(dbAdress)
        else:
            raise ValueError("WEPCalculation does not support %s yet." % bscDbType)

        # Do the query
        sourSelc.setObsMetaData(self.raInDeg, self.decInDeg, self.rotSkyPos)

        camDimOffset = self.settingFile.getSetting("camDimOffset")
        if (bscDbType == BscDbType.LocalDb):
            neighborStarMap = sourSelc.getTargetStar(offset=camDimOffset,
                lowMagnitude=lowMagnitude, highMagnitude=highMagnitude)[0]
        elif (bscDbType == BscDbType.LocalDbForStarFile):
            skyFile = self._assignSkyFile()
            neighborStarMap = sourSelc.getTargetStarByFile(
                skyFile, offset=camDimOffset)[0]
        elif (bscDbType == BscDbType.LocalDbFromImage):
            neighborStarMap = sourSelc.getTargetStarFromImage(
                self._getButlerRootPath(), visitList, defocalState,
                offset=camDimOffset)[0]
        elif (bscDbType == BscDbType.LocalDbFromRefCat):
            neighborStarMap = sourSelc.getTargetStarFromRefCat(
                self._getButlerRootPath(), visitList, defocalState,
                offset=camDimOffset)[0]

        # Disconnect the database
        sourSelc.disconnect()

        return neighborStarMap

    def _assignSkyFile(self):
        """Assign the sky file.

        If the skyFile attribute value is "", the default one from the
        configuration file will be used.

        Returns
        -------
        str
            Path of sky file.
        """

        isSkyFileExist = os.path.exists(self.skyFile)
        if isSkyFileExist:
            skyFile = self.skyFile
        else:
            warnings.warn("No sky file assigned. Use the default one.",
                          category=UserWarning)

            skyFileRelativePath = self.settingFile.getSetting(
                "defaultSkyFilePath")
            skyFile = os.path.join(getModulePath(), skyFileRelativePath)

        return skyFile

    def _calcWfErr(self, neighborStarMap, obsIdList,postageImg=False,
        postageImgDir=None, ):
        """Calculate the wavefront error.

        Only consider one intra-focal and one extra-focal images at this
        moment

        Parameters
        ----------
        neighborStarMap : dict
            Information of neighboring stars and candidate stars with the name
            of sensor as a dictionary.
        obsIdList : list[int]
            Observation Id list in [intraObsId, extraObsId]. If the input is
            [intraObsId], this means the corner WFS.

        postageImg : True/False - whether to save postage stamp images of donuts
        postageImgDir : a directory where to save them

        Returns
        -------
        dict
            Donut image map with the calculated wavefront error. The dictionary
            key is the sensor name. The dictionary item is the donut image
            (type: DonutImage).
        """

        sensorNameList = list(neighborStarMap)

        if len(obsIdList) == 2 : # ComCam case
            print('_calcWfErr has a pair of intra/extra focal obsIds')
            imgType = self._getImageType()
            if (imgType == ImageType.Amp):
                wfsImgMap = self.wepCntlr.getPostIsrImgMapByPistonDefocal(
                    sensorNameList, obsIdList)
            elif (imgType == ImageType.Eimg):
                wfsImgMap = self.wepCntlr.getEimgMapByPistonDefocal(
                  sensorNameList, obsIdList)

        elif len(obsIdList) == 1 : #corner WFS case
            print('_calcWfErr has a single intra-focal obsId: the corner WFS case')
            wfsImgMap = self.wepCntlr.getPostIsrImgMapOnCornerWfs(
                  sensorNameList, obsIdList[0])

        doDeblending = self.settingFile.getSetting("doDeblending")
        donutMap = self.wepCntlr.getDonutMap(
            neighborStarMap, wfsImgMap, self.getFilter(),
            doDeblending=doDeblending, postageImg=postageImg,
            postageImgDir=postageImgDir)

        donutMap = self.wepCntlr.calcWfErr(donutMap,postageImgDir)

        return donutMap

    def _populateListOfSensorWavefrontData(self, donutMap,sensorNameToIdFileName='sensorNameToId.yaml'):
        """Populate the list of sensor wavefront data.

        Parameters
        ----------
        donutMap : dict
            Donut image map with the calculated wavefront error. The dictionary
            key is the sensor name. The dictionary item is the donut image
            (type: DonutImage).

        Returns
        -------
        list[SensorWavefrontData]
            List of SensorWavefrontData object.
        """

        mapSensorNameAndId = MapSensorNameAndId(sensorNameToIdFileName)
        listOfWfErr = []
        for sensor, donutList in donutMap.items():

            sensorWavefrontData = SensorWavefrontData()

            # Set the sensor Id
            abbrevSensor = abbrevDectectorName(sensor)
            sensorIdList = mapSensorNameAndId.mapSensorNameToId(abbrevSensor)
            sensorId = sensorIdList[0]
            sensorWavefrontData.setSensorId(sensorId)

            sensorWavefrontData.setListOfDonut(donutList)

            # Set the average zk in um
            avgErrInNm = self.wepCntlr.calcAvgWfErrOnSglCcd(donutList)
            avgErrInUm = avgErrInNm * 1e-3
            sensorWavefrontData.setAnnularZernikePoly(avgErrInUm)

            listOfWfErr.append(sensorWavefrontData)

        return listOfWfErr

    def ingestCalibs(self, calibsDir):
        """Ingest the calibration products.

        Parameters
        ----------
        calibsDir : str
            Calibration products directory.
        """

        self._genCamMapperIfNeed()

        dataCollector = self.wepCntlr.getDataCollector()

        calibFiles = os.path.join(calibsDir, "*")
        dataCollector.ingestCalibs(calibFiles)


if __name__ == "__main__":
    pass
