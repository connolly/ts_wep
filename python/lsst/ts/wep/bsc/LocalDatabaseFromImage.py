import os
import lsst.daf.persistence as dafPersist
from lsst.ts.wep.bsc.DonutDetector import DonutDetector
from lsst.ts.wep.bsc.LocalDatabaseForStarFile import LocalDatabaseForStarFile
from lsst.ts.wep.cwfs.TemplateUtils import createTemplateImage


class LocalDatabaseFromImage(LocalDatabaseForStarFile):

    PRE_TABLE_NAME = "StarTable"

    def insertDataFromImage(self, butlerRootPath, settingFileInst,
                            visitList, defocalState,
                            filterType, camera,
                            skiprows=1, keepFile=True,
                            fileOut='foundDonuts.txt'):

        self.expWcs = settingFileInst.getSetting("expWcs")
        centroidTemplateType = settingFileInst.getSetting("centroidTemplateType")
        donutImgSize = settingFileInst.getSetting("donutImgSizeInPixel")
        overlapDistance = settingFileInst.getSetting("minUnblendedDistance")
        maxSensorStars = settingFileInst.getSetting("maxSensorStars")
        pix2arcsec = settingFileInst.getSetting("pixelToArcsec")
        skyDf = self.identifyDonuts(butlerRootPath, visitList, filterType,
                                    defocalState, camera, pix2arcsec,
                                    centroidTemplateType, donutImgSize,
                                    overlapDistance, maxSensorStars)
        self.writeSkyFile(skyDf, fileOut)
        self.insertDataByFile(fileOut, filterType, skiprows=1)

        return

    def identifyDonuts(self, butlerRootPath, visitList, filterType,
                       defocalState, camera, pix2arcsec,
                       templateType, donutImgSize, overlapDistance,
                       maxSensorStars=None):

        butler = dafPersist.Butler(butlerRootPath)
        sensorList = butler.queryMetadata('postISRCCD', 'detectorName')
        visitOn = visitList[0]
        full_unblended_df = None
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
            donut_df = donut_detect.detectDonuts(raw, overlapDistance)

            ranked_unblended_df = donut_detect.rankUnblendedByFlux(donut_df,
                                                                   raw)
            ranked_unblended_df = ranked_unblended_df.reset_index(drop=True)

            if maxSensorStars is not None:
                ranked_unblended_df = ranked_unblended_df.iloc[:maxSensorStars]

            # Make coordinate change appropriate to sourProc.dmXY2CamXY
            # FIXME: This is a temporary workaround
            # Transpose because wepcntl. _transImgDmCoorToCamCoor
            if self.expWcs is False:
                # Transpose because wepcntl. _transImgDmCoorToCamCoor
                dimY, dimX = list(raw.getDimensions())
                pixelCamX = ranked_ref_cat_df['centroid_x'].values
                pixelCamY = dimX - ranked_ref_cat_df['centroid_y'].values
                ranked_ref_cat_df['x_center'] = pixelCamX
                ranked_ref_cat_df['y_center'] = pixelCamY
            else:
                ranked_ref_cat_df['x_center'] = ranked_ref_cat_df['centroid_x']
                ranked_ref_cat_df['y_center'] = ranked_ref_cat_df['centroid_y']

            ra, dec = camera._wcs.raDecFromPixelCoords(
                ranked_unblended_df['x_center'].values,
                ranked_unblended_df['y_center'].values,
                # pixelCamX, pixelCamY,
                detector, epoch=2000.0, includeDistortion=True
            )

            ranked_unblended_df['ra'] = ra
            ranked_unblended_df['dec'] = dec
            ranked_unblended_df['raft'] = raft
            ranked_unblended_df['sensor'] = sensor

            if full_unblended_df is None:
                full_unblended_df = ranked_unblended_df.copy(deep=True)
            else:
                full_unblended_df = full_unblended_df.append(
                    ranked_unblended_df)

        full_unblended_df = full_unblended_df.reset_index(drop=True)

        # FIXME: Actually estimate magnitude
        full_unblended_df['mag'] = 15.

        # TODO: Comment out when not debugging
        full_unblended_df.to_csv('image_donut_df.csv')

        return full_unblended_df

    def writeSkyFile(self, unblendedDf, fileOut):

        with open(fileOut, 'w') as file:
            file.write("# Id\t Ra\t\t Decl\t\t Mag\n")
            unblendedDf.to_csv(file, columns=['ra', 'dec', 'mag'],
                               header=False, sep='\t', float_format='%3.6f')

        return
