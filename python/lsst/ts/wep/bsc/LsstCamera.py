from lsst.obs.lsstSim import LsstSimMapper

from lsst.ts.wep.bsc.CameraData import CameraData


class LsstCamera(CameraData):

    def __init__(self):
        super(LsstCamera, self).__init__(self.LSST, LsstSimMapper().camera)

    def getWavefrontSensor(self, obs):
        """
        
        Get the corners of LSST curvature wavefront sensors in (ra, dec) based on the camera_mapper
        list below.
        
        Arguments:
            obs {[metadata]} -- Instantiation of ObservationMetaData that describes the pointing
                                of the telescope.
        
        Returns:
            [list] -- (ra, dec) of four corners of each sensor with the name of sensor as a list
        """

        # Camera object
        camera_mapper = self.getWfsCCdList()
        ra_dec_out = self.getDetectorRaDec(camera_mapper, obs)

        return ra_dec_out

    def getScineceSensor(self, obs):
        """
        
        Get the corners of LSST science sensors in (ra, dec) based on the camera_mapper list below.
        
        Arguments:
            obs {[metadata]} -- Instantiation of ObservationMetaData that describes the pointing
                                of the telescope.
        
        Returns:
            [list] -- (ra, dec) of four corners of each sensor with the name of sensor as a list
        """

        # Camera object
        camera_mapper = self.getSciCcdList()
        ra_dec_out = self.getDetectorRaDec(camera_mapper, obs)

        return ra_dec_out


if __name__ == "__main__":
    pass
