import numpy as np

from scipy.ndimage.morphology import binary_closing
from scipy.ndimage.interpolation import shift
from scipy.spatial.distance import cdist

from lsst.ts.wep.Utility import CentroidFindType
from lsst.ts.wep.cwfs.CentroidFindFactory import CentroidFindFactory
from lsst.ts.wep.deblend.DeblendAdapt import DeblendAdapt
from lsst.ts.wep.cwfs.TemplateUtils import createTemplateImage


class DeblendConvolveTemplate(DeblendAdapt):

    def __init__(self):
        """DeblendDefault child class to do the deblending by the
        template convolution method."""
        super(DeblendConvolveTemplate, self).__init__()

        self._centroidFind = CentroidFindFactory.createCentroidFind(
            CentroidFindType.ConvolveTemplate)

    def _getBinaryImages(self, imgToDeblend, iniGuessXY, defocalState=1,
                         sensorName=None, iniFieldXY=[(0., 0.)],
                         templateType='model', donutImgSize=160, **kwargs):
        """Deblend the donut image.

        Parameters
        ----------
        imgToDeblend : numpy.ndarray
            Image to deblend.
        iniGuessXY : list[tuple]
            The list contains the initial guess of (x, y) positions of
            neighboring stars as [star 1, star 2, etc.].

        Returns
        -------
        numpy.ndarray
            Deblended donut image.
        float
            Position x of donut in pixel.
        float
            Position y of donut in pixel.

        Raises
        ------
        ValueError
            Only support to deblend single neighboring star.
        """

        # Check the number of neighboring star
        if sensorName is None:
            raise ValueError("Need to specify sensor.")

        # Get template and appropriate binary images
        templateImg = createTemplateImage(defocalState, sensorName,
                                          iniFieldXY, templateType,
                                          donutImgSize)
        templateImgBinary = self._getImgBinaryAdapt(templateImg)
        templateImgBinary = binary_closing(templateImgBinary)
        templatecx, templatecy, templateR = \
            self._centroidFind.getCenterAndRfromImgBinary(templateImgBinary)
        adapImgBinary = self._getImgBinaryAdapt(imgToDeblend)

        # Get centroid values
        n_donuts = len(iniGuessXY) + 1
        cx_list, cy_list = self._centroidFind.getCenterFromTemplateConv(
            adapImgBinary, templateImgBinary, n_donuts
        )

        # Order the centroids to figure out which is neighbor star
        centroid_dist = cdist(np.array(iniGuessXY),
                              np.array([cx_list, cy_list]).T)
        iniGuess_dist_order = np.argsort(centroid_dist[0])

        # Update coords of neighbor star and bright star with centroid pos
        realcx = cx_list[iniGuess_dist_order[1]]
        realcy = cy_list[iniGuess_dist_order[1]]

        imgBinary = np.zeros(np.shape(adapImgBinary))
        imgBinary[:np.shape(templateImgBinary)[0],
                  :np.shape(templateImgBinary)[1]] += templateImgBinary

        xBin = int(realcx - templatecx)
        yBin = int(realcy - templatecy)

        imgBinary = shift(imgBinary, [xBin, yBin])
        imgBinary[imgBinary < 0] = 0

        # Calculate the shifts of x and y
        # Only support to deblend single neighboring star at this moment
        starXyNbr = [cx_list[iniGuess_dist_order[0]],
                     cy_list[iniGuess_dist_order[0]]]
        y0 = int(starXyNbr[0] - realcx)
        x0 = int(starXyNbr[1] - realcy)

        return imgBinary, adapImgBinary, x0, y0