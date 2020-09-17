import numpy as np
import pandas as pd

from copy import deepcopy
from lsst.ts.wep.SourceProcessor import SourceProcessor

from lsst.afw.image import ImageF
from skimage.filters import threshold_otsu, threshold_triangle, threshold_local
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import cdist
from numpy.fft import fft2, ifft2
from scipy.signal import fftconvolve, correlate2d, correlate


class DonutDetector():

    def __init__(self, template):

        """
        Parameters
        ----------
        raft: str
            Raft of the exposure

        detector: str
            Detector of the exposure

        defocal_type: str
            Defocal mode of the exposure: 'intra' or 'extra'
        """

        self.template = template

    def thresholdExpFAndTemp(self, exposure, image_threshold=None):

        """
        Create a binary image from the exposure using the triangle
        thresholding method from scikit-learn. Also create a binary
        image for the template using the Otsu threshold.

        Parameters
        ----------
        exposure: LSST ExposureF instance
            Exposure with defocal donuts

        image_threshold: Float or None
            If None the threshold will be detected from the image. If
            specified then the binary image will be created using the
            specified threshold level.

        Returns
        -------
        binary_exp: LSST ExposureF instance
            A copy of the original exposure but with the image array now a
            binary image

        binary_template: numpy array
            A copy of the template with a binary image of the template

        image_threshold: float
            Pixel count threshold used to create binary image.
        """

        binary_exp = deepcopy(exposure)
        binary_exp.image.array[binary_exp.image.array < 0.] = 0.
        if image_threshold is None:
            # TODO: Finalize thresholding
            # image_thresh = threshold_otsu(exposure.image.array)
            image_thresh = threshold_triangle(exposure.image.array)
            # TODO: Set local window size based upon donut size.
            # image_thresh = threshold_local(exposure.image.array, 161.)
        else:
            image_thresh = image_threshold
        binary_exp.image.array[binary_exp.image.array <= image_thresh] = 0.
        binary_exp.image.array[binary_exp.image.array > image_thresh] = 1.

        # If the donuts are sparse in an image the local threshold will find
        # noise peaks. This should cut those out. And with dense fields
        # the goal isn't to get every single one but to get the bright ones
        exp_median = np.median(exposure.image.array.flatten())
        binary_exp.image.array[np.where(exposure.image.array < exp_median)] = 0.

        binary_template = deepcopy(self.template)
        template_thresh = threshold_otsu(binary_template)
        binary_template[binary_template <= template_thresh] = 0.
        binary_template[binary_template > template_thresh] = 1.

        return binary_exp, binary_template, image_thresh

    def detectDonuts(self, exposure, blend_radius, image_threshold=None):

        """
        Detect and categorize donut sources as blended/unblended

        Parameters
        -------
        exposure: LSST ExposureF instance
            The same input exposure

        blend_radius: Float
            Minimum distance in pixels two donut centers need to
            be apart in order to be tagged as unblended

        image_threshold: Float or None
            Can specify the image threshold to use in the method
            self.thresholdExpFAndTemp when creating the binary image
            to use in the correlation step.

        Returns
        -------
        image_donuts_df: pandas dataframe
            Dataframe identifying donut positions and if they
            are blended with other donuts. If blended also identfies
            which donuts are blended with which.
        """

        binary_exp, binary_template, image_thresh = \
            self.thresholdExpFAndTemp(exposure, image_threshold)

        binary_template_image = ImageF(np.shape(self.template)[0],
                                       np.shape(self.template)[1])
        binary_template_image.array[:] = binary_template
        new_exp = self.correlateExposureWithImage(
            binary_exp, binary_template_image
        )

        # Set detection floor at 50% of max signal. Since we are using
        # binary images all signals should be around the same strength
        ranked_correlate = np.argsort(new_exp.image.array.flatten())[::-1]
        cutoff = len(np.where(new_exp.image.array.flatten() >
                              0.5*np.max(new_exp.image.array))[0])
        ranked_correlate = ranked_correlate[:cutoff]
        nx, ny = np.unravel_index(ranked_correlate,
                                  np.shape(new_exp.image.array))

        # Use DBSCAN to find clusters of points
        db_cluster = DBSCAN(eps=2.).fit(np.array([ny, nx]).T)

        db_cluster_centers = []
        for i in np.unique(db_cluster.labels_):
            ny_cluster = ny[np.where(db_cluster.labels_ == i)]
            nx_cluster = nx[np.where(db_cluster.labels_ == i)]
            db_cluster_centers.append([np.mean(ny_cluster),
                                       np.mean(nx_cluster)])
        db_cluster_centers = np.array(db_cluster_centers)

        image_donuts_df = pd.DataFrame(db_cluster_centers,
                                       columns=['x_center', 'y_center'])
        image_donuts_df = self.labelUnblended(image_donuts_df, blend_radius,
                                              'x_center', 'y_center')

        return image_donuts_df, image_thresh

    def labelUnblended(self, image_donuts_df, blend_radius,
                       x_col_name, y_col_name):

        """
        Label donuts as blended/unblended
        """

        # Find distances between each pair of objects
        db_cluster_centers = [image_donuts_df[x_col_name].values,
                              image_donuts_df[y_col_name].values]
        db_cluster_centers = np.array(db_cluster_centers).T
        dist_matrix = cdist(db_cluster_centers, db_cluster_centers)
        # Don't need repeats of each pair
        dist_matrix_upper = np.triu(dist_matrix)

        blended_pairs = np.array(np.where(
            (dist_matrix_upper > 0.) &
            (dist_matrix_upper < blend_radius))).T
        blended_cluster_centers = np.unique(blended_pairs.flatten())

        image_donuts_df['blended'] = False
        image_donuts_df.loc[blended_cluster_centers, 'blended'] = True
        image_donuts_df['blended_with'] = None
        for i, j in blended_pairs:
            if image_donuts_df.loc[i, 'blended_with'] is None:
                image_donuts_df.at[i, 'blended_with'] = []
            if image_donuts_df.loc[j, 'blended_with'] is None:
                image_donuts_df.at[j, 'blended_with'] = []
            image_donuts_df.loc[i, 'blended_with'].append(j)
            image_donuts_df.loc[j, 'blended_with'].append(i)

        image_donuts_df['num_blended_neighbors'] = 0
        for i in range(len(image_donuts_df)):
            if image_donuts_df['blended_with'].iloc[i] is None:
                continue

            image_donuts_df.at[i, 'num_blended_neighbors'] = \
                len(image_donuts_df['blended_with'].loc[i])

        return image_donuts_df

    def rankUnblendedByFlux(self, donuts_df, exposure):

        """
        Prioritize unbleneded objects based upon magnitude.

        Parameters
        ----------
        donuts_df: pandas dataframe
            Output from `detectDonuts`

        exposure: LSST ExposureF instance
            Exposure with defocal donuts

        Returns
        -------
        unblended_df: pandas dataframe
            Dataframe of the unblended donuts ordered by
            relative brightness.
        """

        template_imageF = ImageF(np.shape(self.template)[0],
                                 np.shape(self.template)[1])
        template_imageF.array[:] = self.template
        rank_exp = self.correlateExposureWithImage(
            exposure, template_imageF
        )

        unblended_df = donuts_df.query('blended == False').copy()

        unblended_flux = []
        for x_coord, y_coord in zip(unblended_df['x_center'].values,
                                    unblended_df['y_center'].values):
            unblended_flux.append(rank_exp.image.array[np.int(y_coord),
                                                       np.int(x_coord)])
        unblended_df['flux'] = unblended_flux
        unblended_df = unblended_df.sort_values('flux', ascending=False)

        return unblended_df

    def correlateExposureWithImage(self, exposure, kernelImage):
        '''Convolve image and variance planes in an exposure with an image using FFT
            Does not convolve mask. Returns new exposure'''

        newExposure = exposure.clone()

        image = self.correlateImageWithImage(newExposure.getImage(), kernelImage)
        variance = self.correlateImageWithImage(newExposure.getVariance(), kernelImage)

        newExposure.image = image
        newExposure.variance = variance
        return newExposure

    def convolveExposureWithImage(self, exposure, kernelImage):
        '''Convolve image and variance planes in an exposure with an image using FFT
            Does not convolve mask. Returns new exposure'''

        newExposure = exposure.clone()

        image = self.convolveImageWithImage(newExposure.getImage(), kernelImage)
        variance = self.convolveImageWithImage(newExposure.getVariance(), kernelImage)

        newExposure.image = image
        newExposure.variance = variance
        return newExposure

    def convolveImageWithImage(self, image, kernelImage):
        '''Convolvean image with a kernel
            Returns an image'''

        array = fftconvolve(image.getArray(), kernelImage.getArray(), mode='same')

        newImage = ImageF(array.shape[1], array.shape[0])
        newImage.array[:] = array
        return newImage

    def correlateImageWithImage(self, image, kernelImage, fft=False):
        '''Correlate an image with a kernel
            Option to use an FFT or direct (slow)
            Returns an image'''

        if fft:
            array = np.roll(ifft2(fft2(kernelImage.getArray()).conj()*fft2(image.getArray())).real,
                            (image.getArray().shape[0] - 1)//2, axis=(0,1))
        else:
            array = correlate(image.getArray(), kernelImage.getArray(), mode='same', method='fft')

        newImage = ImageF(array.shape[1], array.shape[0])
        newImage.array[:] = array
        return newImage
