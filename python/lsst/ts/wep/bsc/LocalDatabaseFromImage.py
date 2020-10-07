import lsst.daf.persistence as dafPersist
from lsst.ts.wep.bsc.DonutDetector import DonutDetector
from lsst.ts.wep.bsc.LocalDatabaseForStarFile import LocalDatabaseForStarFile
from lsst.ts.wep.cwfs.TemplateUtils import createTemplateImage
from lsst.ts.wep.Utility import abbrevDetectorName, parseAbbrevDetectorName


class LocalDatabaseFromImage(LocalDatabaseForStarFile):

    PRE_TABLE_NAME = "StarTable"

    def insertDataFromImage(self, butlerRootPath, settingFileInst,
                            visitList, defocalState,
                            filterType, camera,
                            skiprows=1, fileOut='foundDonuts.txt'):

        expWcs = settingFileInst.getSetting("expWcs")
        centroidTemplateType = settingFileInst.getSetting("centroidTemplateType")
        donutImgSize = settingFileInst.getSetting("donutImgSizeInPixel")
        overlapDistance = settingFileInst.getSetting("minUnblendedDistance")
        doDeblending = settingFileInst.getSetting("doDeblending")
        maxSensorStars = settingFileInst.getSetting("maxSensorStars")
        pix2arcsec = settingFileInst.getSetting("pixelToArcsec")
        skyDf = self.identifyDonuts(butlerRootPath, visitList, filterType,
                                    defocalState, camera, pix2arcsec,
                                    centroidTemplateType, donutImgSize,
                                    overlapDistance, doDeblending,
                                    expWcs, maxSensorStars)
        self.writeSkyFile(skyDf, fileOut)
        self.insertDataByFile(fileOut, filterType, skiprows=1)

        return

    def identifyDonuts(self, butlerRootPath, visitList, filterType,
                       defocalState, camera, pix2arcsec,
                       templateType, donutImgSize, overlapDistance,
                       doDeblending, expWcs, maxSensorStars=None):

        butler = dafPersist.Butler(butlerRootPath)
        sensorList = butler.queryMetadata('postISRCCD', 'detectorName')
        visitOn = visitList[0]
        full_results_df = None
        # detector has 'R:0,0 S:2,2,A' format
        for detector in camera.getWfsCcdList():

            # abbrevName has R00_S22_C0 format
            abbrevName = abbrevDetectorName(detector)
            raft, sensor = parseAbbrevDetectorName(abbrevName)

            if sensor not in sensorList:
                continue

            data_id = {'visit': visitOn, 'filter': filterType.toString(),
                       'raftName': raft, 'detectorName': sensor}
            print(data_id)

            # TODO: Rename this to reflect this is postISR not raw image.
            raw = butler.get('postISRCCD', **data_id)
            template = createTemplateImage(defocalState,
                                           abbrevName, pix2arcsec,
                                           templateType, donutImgSize)
            donut_detect = DonutDetector(template)
            donut_df, image_thresh = donut_detect.detectDonuts(raw,
                                                               overlapDistance)

            # Update WCS if using exposure WCS for source selection
            # if expWcs is True:
            #     camera._wcs.wcsData[detector] = raw.getWcs()

            if doDeblending is False:
                sensor_results_df = donut_detect.rankUnblendedByFlux(donut_df,
                                                                     raw)
                sensor_results_df = sensor_results_df.reset_index(drop=True)
            else:
                sensor_results_df = donut_df

            if maxSensorStars is not None:
                sensor_results_df = sensor_results_df.iloc[:maxSensorStars]

            # Make coordinate change appropriate to sourProc.dmXY2CamXY
            # FIXME: This is a temporary workaround
            # Transpose because wepcntl. _transImgDmCoorToCamCoor
            if expWcs is False:
                # Transpose because wepcntl. _transImgDmCoorToCamCoor
                dimY, dimX = list(raw.getDimensions())
                pixelCamX = sensor_results_df['x_center'].values
                pixelCamY = dimX - sensor_results_df['y_center'].values
                sensor_results_df['x_center'] = pixelCamX
                sensor_results_df['y_center'] = pixelCamY

            ra, dec = camera._wcs.raDecFromPixelCoords(
                sensor_results_df['x_center'].values,
                sensor_results_df['y_center'].values,
                # pixelCamX, pixelCamY,
                detector, epoch=2000.0, includeDistortion=True
            )

            sensor_results_df['ra'] = ra
            sensor_results_df['dec'] = dec
            sensor_results_df['raft'] = raft
            sensor_results_df['sensor'] = sensor

            if full_results_df is None:
                full_results_df = sensor_results_df.copy(deep=True)
            else:
                full_results_df = full_results_df.append(
                    sensor_results_df)

        full_results_df = full_results_df.reset_index(drop=True)

        # FIXME: Actually estimate magnitude
        full_results_df['mag'] = 15.

        # TODO: Comment out when not debugging
        # full_results_df.to_csv('image_donut_df.csv')

        return full_results_df

    def writeSkyFile(self, unblendedDf, fileOut):

        with open(fileOut, 'w') as file:
            file.write("# Id\t Ra\t\t Decl\t\t Mag\n")
            unblendedDf.to_csv(file, columns=['ra', 'dec', 'mag'],
                               header=False, sep='\t', float_format='%3.6f')

        return
