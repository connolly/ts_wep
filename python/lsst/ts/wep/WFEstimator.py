import os, sys, unittest
import numpy as np

from cwfs.Instrument import Instrument
from cwfs.Algorithm import Algorithm
from cwfs.CompensationImageDecorator import CompensationImageDecorator

from lsst.ts.wep.Utility import getModulePath

class WFEstimator(object):

    def __init__(self, instruFolderPath, algoFolderPath):
        """

        Initialize the WFEstimator class.

        Arguments:
            instruFolderPath {[str]} -- Path to instrument directory.
            algoFolderPath {[str]} -- Path to algorithm directory.
        """

        self.algo = Algorithm(algoFolderPath)
        self.inst = Instrument(instruFolderPath)
        self.ImgIntra = CompensationImageDecorator()
        self.ImgExtra = CompensationImageDecorator()
        self.opticalModel = None

        self.sizeInPix = None

    def reset(self):
        """
        
        Reset the calculation for the new input images with the same algorithm settings.
        """
        self.algo.reset()

    def config(self, solver="exp", instName="lsst", opticalModel="offAxis", defocalDisInMm=None, 
                sizeInPix=120, debugLevel=0):
        """
        
        Configure the TIE solver.
        
        Keyword Arguments:
            solver {[str]} -- Algorithm to solve the Poisson's equation in the transport of 
                            intensity equation (TIE). It can be "fft" or "exp" here. 
                            (default: {"exp"})
            instName {[str]} -- Instrument name. It is "lsst" in the baseline. (default: {"lsst"})
            opticalModel {[str]} -- Optical model. It can be "paraxial", "onAxis", or "offAxis". 
                                    (default: {"offAxis"})
            defocalDisInMm {[float]} -- Defocal distance in mm. (default: {None})
            sizeInPix {[int]} -- Wavefront image pixel size. (default: {120}) 
            debugLevel {[int]} -- Show the information under the running. If the value is higher, 
                                    the information shows more. It can be 0, 1, 2, or 3. 
                                    (default: {0})

        Raises:
            ValueError -- Wrong instrument name.
            ValueError -- No intra-focal image.
            ValueError -- Wrong Poisson solver name.
            ValueError -- Wrong optical model.
        """

        # Check the inputs and assign the parameters used in the TIE
        # Need to change the way to hold the instance of Instrument and Algorithm

        # Update the isnstrument name
        if (defocalDisInMm is not None):
            instName = instName + str(int(10*defocalDisInMm))

        if instName not in ("lsst", "lsst05", "lsst10", "lsst15", "lsst20", "lsst25", "comcam10", 
                            "comcam15", "comcam20"):
            raise ValueError("Instrument can not be '%s'." % instName)

        # Set the available wavefront image size (n x n)
        self.sizeInPix = int(sizeInPix)

        # Configurate the instrument
        self.inst.config(instName, self.sizeInPix)

        if solver not in ("exp", "fft"):
            raise ValueError("Poisson solver can not be '%s'." % solver)
        else:
            self.algo.config(solver, self.inst, debugLevel=debugLevel)

        if opticalModel not in ("paraxial", "onAxis", "offAxis"):
            raise ValueError("Optical model can not be '%s'." % opticalModel)
        else:
            self.opticalModel = opticalModel

    def setImg(self, fieldXY, image=None, imageFile=None, defocalType=None):
        """

        Set the wavefront image.

        Arguments:
            fieldXY {[float]} -- Position of donut on the focal plane in degree for intra- 
                                 and extra-focal images.

        Keyword Arguments:
            image {[float]} -- Array of image. (default: {None})
            imageFile {[str]} -- Path of image file. (default: {None})
            defocalType {[str]} -- Type of image. It should be "intra" or "extra". 
                                    (default: {None})

        Raises:
            ValueError -- Wrong defocal type.
        """

        # Check the defocal type
        if defocalType not in (self.ImgIntra.INTRA, self.ImgIntra.EXTRA):
            raise ValueError("Defocal type can not be '%s'." % defocalType)

        # Read the image and assign the type
        if (defocalType == self.ImgIntra.INTRA):
            self.ImgIntra.setImg(fieldXY, image=image, imageFile=imageFile, atype=defocalType)
        elif (defocalType == self.ImgIntra.EXTRA):
            self.ImgExtra.setImg(fieldXY, image=image, imageFile=imageFile, atype=defocalType)

    def calWfsErr(self, tol=1e-3, showZer=False, showPlot=False):
        """

        Calculate the wavefront error.

        Keyword Arguments:
            tol {number} -- Tolerance of difference of coefficients of Zk polynomials compared 
                            with the previours iteration. (default: {1e-3})
            showZer {bool} -- Decide to show the annular Zernike polynomails or not. 
                                (default: {False})
            showPlot {bool} -- Decide to show the plot or not. (default: {False})

        Returns:
            [float] -- Coefficients of Zernike polynomials (z4 - z22).
        """

        # Check the image size
        for img in (self.ImgIntra,  self.ImgExtra):
            d1, d2 = img.image.shape
            if (d1 != self.sizeInPix) or (d2 != self.sizeInPix):
                raise RuntimeError("Input image shape is (%d, %d), not required (%d, %d)" % 
                                    (d1, d2, self.sizeInPix, self.sizeInPix))

        # Calculate the wavefront error.
        # Run cwfs
        self.algo.runIt(self.inst, self.ImgIntra, self.ImgExtra, self.opticalModel, tol=tol)

        # Show the Zernikes Zn (n>=4)
        if (showZer):
            self.algo.outZer4Up(showPlot=showPlot)

        return self.algo.zer4UpNm

    def outParam(self, filename=None):
        """

        Put the information of images, instrument, and algorithm on terminal or file.

        Keyword Arguments:
            filename {[str]} -- Name of output file. (default: {None})
        """

        # Write the parameters into a file if needed.
        if (filename is not None):
            fout = open(filename, "w")
        else:
            fout = sys.stdout

        # Write the information of image and optical model
        if (self.ImgIntra.name is not None):
            fout.write("Intra image: \t %s\n" % self.ImgIntra.name)

        if (self.ImgIntra.fieldX is not None):
            fout.write("Intra image field in deg =(%6.3f, %6.3f)\n" % (self.ImgIntra.fieldX, 
                                                                        self.ImgIntra.fieldY))

        if (self.ImgExtra.name is not None):
            fout.write("Extra image: \t %s\n" % self.ImgExtra.name)

        if (self.ImgExtra.fieldX is not None):
            fout.write("Extra image field in deg =(%6.3f, %6.3f)\n" % (self.ImgExtra.fieldX, 
                                                                        self.ImgExtra.fieldY))

        if (self.opticalModel is not None):
            fout.write("Using optical model:\t %s\n" % self.opticalModel)

        # Read the instrument file
        if (self.inst.filename is not None):
            self.__readConfigFile(fout, self.inst, "instrument")

        # Read the algorithm file
        if (self.algo.filename is not None):
            self.__readConfigFile(fout, self.algo, "algorithm")

        # Close the file
        if (filename is not None):
            fout.close()

    def __readConfigFile(self, fout, config, configName):
        """
        
        Read the configuration file
        
        Arguments:
            fout {[file]} -- File instance.
            config {[metadata]} -- Instance of configuration. It is Instrument or Algorithm 
                                   here.
            configName {[str]} -- Name of configuration.
        """

        # Create a new line
        fout.write("\n")
        
        # Open the file
        fconfig = open(config.filename)
        fout.write("---" + configName + " file: --- %s ----------\n" % config.filename)
        
        # Read the file information
        iscomment = False
        for line in fconfig:
            line = line.strip()
            if (line.startswith("###")):
                iscomment = ~iscomment
            if (not(line.startswith("#")) and (not iscomment) and len(line) > 0):
                fout.write(line + "\n")

        # Close the file
        fconfig.close()

class WFEsitmatorTest(unittest.TestCase):
    """
    Test functions in WFEstimator.
    """

    def setUp(self):

        # Get the path of module
        self.modulePath = getModulePath()

        # Define the instrument folder
        instruFolderPath = os.path.join(self.modulePath, "algoData", "cwfs", "instruData")

        # Define the algorithm folder
        algoFolderPath = os.path.join(self.modulePath, "algoData", "cwfs", "algo")

        # Decalre the WFEsitmator
        self.wfsEst = WFEstimator(instruFolderPath, algoFolderPath)

    def testFunc(self):

        # Define the image folder and image names
        # Image data -- Don't know the final image format.
        # It is noted that image.readFile inuts is based on the txt file.
        imageFolderPath = os.path.join(self.modulePath, "test", "testImages", "LSST_NE_SN25")
        intra_image_name = "z11_0.25_intra.txt"
        extra_image_name = "z11_0.25_extra.txt"

        # Path to image files
        intraImgFile = os.path.join(imageFolderPath, intra_image_name)
        extraImgFile = os.path.join(imageFolderPath, extra_image_name)

        # Field XY position
        fieldXY = [1.185, 1.185]

        # Setup the images
        self.wfsEst.setImg(fieldXY, imageFile=intraImgFile, defocalType="intra")
        self.wfsEst.setImg(fieldXY, imageFile=extraImgFile, defocalType="extra")

        # Test the images are set.
        self.assertEqual(self.wfsEst.ImgIntra.atype, self.wfsEst.ImgIntra.INTRA)
        self.assertEqual(self.wfsEst.ImgExtra.atype, self.wfsEst.ImgExtra.EXTRA)

        # Setup the configuration

        # Try to catch the error 
        try:
            self.wfsEst.config(solver="exp", defocalDisInMm=3, debugLevel=0)
        except ValueError:
            print("Catch the wrong instrument.")

        # If the configuration is reset, the images are needed to be set again.
        self.wfsEst.config(solver="exp", instName="lsst", sizeInPix=120, 
                            opticalModel="offAxis", debugLevel=0)

        # Test the setting of algorithm and instrument
        self.assertEqual(self.wfsEst.inst.instName, "lsst")
        self.assertEqual(self.wfsEst.algo.algoName, "exp")

        # Evaluate the wavefront error
        wfsError = [2.593, 14.102, -8.470, 3.676, 1.467, -9.724, 8.207, 
                    -192.839, 0.978, 1.568, 4.197, -0.391, 1.551, 1.235, 
                    -1.699, 2.140, -0.296, -2.113, 1.188]
        zer4UpNm = self.wfsEst.calWfsErr()
        self.assertAlmostEqual(np.sum(np.abs(zer4UpNm-np.array(wfsError))), 0, places=1)

        # Reset the wavefront images
        self.wfsEst.setImg(fieldXY, imageFile=intraImgFile, defocalType="intra")
        self.wfsEst.setImg(fieldXY, imageFile=extraImgFile, defocalType="extra")

        # Change the algorithm to fft
        self.wfsEst.config(solver="fft")
        self.assertEqual(self.wfsEst.algo.algoName, "fft")

        # Evaluate the wavefront error
        wfsError = [12.484, 10.358, -6.674, -0.043, -1.768, -15.593, 12.511, 
                    -192.382, 0.195, 4.074, 9.577, -1.930, 3.538, 3.420, 
                    -3.610, 3.547, -0.679, -2.943, 1.101] 
        zer4UpNm = self.wfsEst.calWfsErr()
        self.assertAlmostEqual(np.sum(np.abs(zer4UpNm-np.array(wfsError))), 0, places=1)

        # Test to output the parameters
        filename = "outputParameter"
        self.wfsEst.outParam(filename=filename)
        self.assertTrue(os.path.isfile(filename))
        os.remove(filename)

        # Test to reset the data
        self.wfsEst.reset()
        self.assertEqual(np.sum(self.wfsEst.algo.zer4UpNm), 0)

if __name__ == "__main__":

    # Do the unit test
    unittest.main()

