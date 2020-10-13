import lsst.ip.isr.isrTask
assert type(config)==lsst.ip.isr.isrTask.RunIsrConfig, 'config is of type %s.%s instead of lsst.ip.isr.isrTask.RunIsrConfig' % (type(config).__module__, type(config).__name__)
import lsst.ip.isr.masking
import lsst.ip.isr.fringe
import lsst.ip.isr.overscan
import lsst.ip.isr.isrQa
import lsst.pipe.base.config
import lsst.ip.isr.straylight
import lsst.ip.isr.crosstalk
import lsst.ip.isr.assembleCcdTask
import lsst.ip.isr.vignette
# Flag to enable/disable metadata saving for a task, enabled by default.
config.isr.saveMetadata=True

# Dataset type for input data; users will typically leave this alone, but camera-specific ISR tasks will override it
config.isr.datasetType='raw'

# Fallback default filter name for calibrations.
config.isr.fallbackFilterName=None

# Pass observation date when using fallback filter.
config.isr.useFallbackDate=False

# Expect input science images to have a WCS (set False for e.g. spectrographs).
config.isr.expectWcs=True

# FWHM of PSF in arcseconds.
config.isr.fwhm=1.0

# Calculate ISR statistics while processing?
config.isr.qa.saveStats=True

# Mesh size in X for flatness statistics
config.isr.qa.flatness.meshX=256

# Mesh size in Y for flatness statistics
config.isr.qa.flatness.meshY=256

# Clip outliers for flatness statistics?
config.isr.qa.flatness.doClip=True

# Number of sigma deviant a pixel must be to be clipped from flatness statistics.
config.isr.qa.flatness.clipSigma=3.0

# Number of iterations used for outlier clipping in flatness statistics.
config.isr.qa.flatness.nIter=3

# Write overscan subtracted image?
config.isr.qa.doWriteOss=False

# Write overscan subtracted thumbnail?
config.isr.qa.doThumbnailOss=False

# Write image after flat-field correction?
config.isr.qa.doWriteFlattened=False

# Write thumbnail after flat-field correction?
config.isr.qa.doThumbnailFlattened=False

# Thumbnail binning factor.
config.isr.qa.thumbnailBinning=4

# Number of sigma below the background to set the thumbnail minimum.
config.isr.qa.thumbnailStdev=3.0

# Total range in sigma for thumbnail mapping.
config.isr.qa.thumbnailRange=5.0

# Softening parameter for thumbnail mapping.
config.isr.qa.thumbnailQ=20.0

# Width of border around saturated pixels in thumbnail.
config.isr.qa.thumbnailSatBorder=2

# Convert integer raw images to floating point values?
config.isr.doConvertIntToFloat=True

# Mask saturated pixels? NB: this is totally independent of the interpolation option - this is ONLY setting the bits in the mask. To have them interpolated make sure doSaturationInterpolation=True
config.isr.doSaturation=True

# Name of mask plane to use in saturation detection and interpolation
config.isr.saturatedMaskName='SAT'

# The saturation level to use if no Detector is present in the Exposure (ignored if NaN)
config.isr.saturation=float('nan')

# Number of pixels by which to grow the saturation footprints
config.isr.growSaturationFootprintSize=1

# Mask suspect pixels?
config.isr.doSuspect=False

# Name of mask plane to use for suspect pixels
config.isr.suspectMaskName='SUSPECT'

# Number of edge pixels to be flagged as untrustworthy.
config.isr.numEdgeSuspect=0

# Should we set the level of all BAD patches of the chip to the chip's average value?
config.isr.doSetBadRegions=True

# How to estimate the average value for BAD regions.
config.isr.badStatistic='MEANCLIP'

# Do overscan subtraction?
config.isr.doOverscan=True

# The method for fitting the overscan bias level.
config.isr.overscan.fitType='MEDIAN'

# Order of polynomial to fit if overscan fit type is a polynomial, or number of spline knots if overscan fit type is a spline.
config.isr.overscan.order=1

# Rejection threshold (sigma) for collapsing overscan before fit
config.isr.overscan.numSigmaClip=3.0

# Mask planes to reject when measuring overscan
config.isr.overscan.maskPlanes=['SAT']

# Treat overscan as an integer image for purposes of fitType=MEDIAN and fitType=MEDIAN_PER_ROW.
config.isr.overscan.overscanIsInt=True

# Number of columns to skip in overscan, i.e. those closest to amplifier
config.isr.overscanNumLeadingColumnsToSkip=0

# Number of columns to skip in overscan, i.e. those farthest from amplifier
config.isr.overscanNumTrailingColumnsToSkip=0

# Maximum deviation from the median for overscan
config.isr.overscanMaxDev=1000.0

# Fit the overscan in a piecewise-fashion to correct for bias jumps?
config.isr.overscanBiasJump=False

# Header keyword containing information about devices.
config.isr.overscanBiasJumpKeyword='NO_SUCH_KEY'

# List of devices that need piecewise overscan correction.
config.isr.overscanBiasJumpDevices=[]

# Location of bias jump along y-axis.
config.isr.overscanBiasJumpLocation=0

# Assemble amp-level exposures into a ccd-level exposure?
config.isr.doAssembleCcd=True

# trim out non-data regions?
config.isr.assembleCcd.doTrim=True

# FITS headers to remove (in addition to DATASEC, BIASSEC, TRIMSEC and perhaps GAIN)
config.isr.assembleCcd.keysToRemove=[]

# Assemble amp-level calibration exposures into ccd-level exposure?
config.isr.doAssembleIsrExposures=False

# Trim raw data to match calibration bounding boxes?
config.isr.doTrimToMatchCalib=False

# Apply bias frame correction?
config.isr.doBias=False

# Name of the bias data product
config.isr.biasDataProductName='bias'

# Calculate variance?
config.isr.doVariance=True

# The gain to use if no Detector is present in the Exposure (ignored if NaN)
config.isr.gain=float('nan')

# The read noise to use if no Detector is present in the Exposure
config.isr.readNoise=0.0

# Calculate empirical read noise instead of value from AmpInfo data?
config.isr.doEmpiricalReadNoise=False

# Correct for nonlinearity of the detector's response?
config.isr.doLinearize=False

# Apply intra-CCD crosstalk correction?
config.isr.doCrosstalk=True

# Apply crosstalk correction before CCD assembly, and before trimming?
config.isr.doCrosstalkBeforeAssemble=False

# Set crosstalk mask plane for pixels over this value.
config.isr.crosstalk.minPixelToMask=45000.0

# Name for crosstalk mask plane.
config.isr.crosstalk.crosstalkMaskPlane='CROSSTALK'

# Type of background subtraction to use when applying correction.
config.isr.crosstalk.crosstalkBackgroundMethod='None'

# Ignore the detector crosstalk information in favor of CrosstalkConfig values?
config.isr.crosstalk.useConfigCoefficients=False

# Amplifier-indexed crosstalk coefficients to use.  This should be arranged as a 1 x nAmp**2 list of coefficients, such that when reshaped by crosstalkShape, the result is nAmp x nAmp. This matrix should be structured so CT * [amp0 amp1 amp2 ...]^T returns the column vector [corr0 corr1 corr2 ...]^T.
config.isr.crosstalk.crosstalkValues=[0.0]

# Shape of the coefficient array.  This should be equal to [nAmp, nAmp].
config.isr.crosstalk.crosstalkShape=[1]

# Apply correction for CCD defects, e.g. hot pixels?
config.isr.doDefect=False

# Mask NAN pixels?
config.isr.doNanMasking=True

# Widen bleed trails based on their width?
config.isr.doWidenSaturationTrails=True

# Apply the brighter fatter correction
config.isr.doBrighterFatter=False

# The level at which to correct for brighter-fatter.
config.isr.brighterFatterLevel='DETECTOR'

# Maximum number of iterations for the brighter fatter correction
config.isr.brighterFatterMaxIter=10

# Threshold used to stop iterating the brighter fatter correction.  It is the  absolute value of the difference between the current corrected image and the one from the previous iteration summed over all the pixels.
config.isr.brighterFatterThreshold=1000.0

# Should the gain be applied when applying the brighter fatter correction?
config.isr.brighterFatterApplyGain=True

# Number of pixels to grow the masks listed in config.maskListToInterpolate  when brighter-fatter correction is applied.
config.isr.brighterFatterMaskGrowSize=0

# Apply dark frame correction?
config.isr.doDark=False

# Name of the dark data product
config.isr.darkDataProductName='dark'

# Subtract stray light in the y-band (due to encoder LEDs)?
config.isr.doStrayLight=False

# 
config.isr.strayLight.doRotatorAngleCorrection=False

# Filters that need straylight correction.
config.isr.strayLight.filters=[]

# Apply flat field correction?
config.isr.doFlat=True

# Name of the flat data product
config.isr.flatDataProductName='flat'

# The method for scaling the flat on the fly.
config.isr.flatScalingType='USER'

# If flatScalingType is 'USER' then scale flat by this amount; ignored otherwise
config.isr.flatUserScale=1.0

# Tweak flats to match observed amplifier ratios?
config.isr.doTweakFlat=False

# Correct the amplifiers for their gains instead of applying flat correction
config.isr.doApplyGains=False

# Normalize all the amplifiers in each CCD to have the same median value.
config.isr.normalizeGains=False

# Apply fringe correction?
config.isr.doFringe=False

# Only fringe-subtract these filters
config.isr.fringe.filters=[]

# Number of fringe measurements
config.isr.fringe.num=30000

# Half-size of small (fringe) measurements (pixels)
config.isr.fringe.small=3

# Half-size of large (background) measurements (pixels)
config.isr.fringe.large=30

# Number of fitting iterations
config.isr.fringe.iterations=20

# Sigma clip threshold
config.isr.fringe.clip=3.0

# Ignore pixels with these masks
config.isr.fringe.stats.badMaskPlanes=['SAT']

# Statistic to use
config.isr.fringe.stats.stat=32

# Sigma clip threshold
config.isr.fringe.stats.clip=3.0

# Number of fitting iterations
config.isr.fringe.stats.iterations=3

# Offset to the random number generator seed (full seed includes exposure ID)
config.isr.fringe.stats.rngSeedOffset=0

# Remove fringe pedestal?
config.isr.fringe.pedestal=False

# Do fringe subtraction after flat-fielding?
config.isr.fringeAfterFlat=True

# Measure the background level on the reduced image?
config.isr.doMeasureBackground=False

# Mask camera-specific bad regions?
config.isr.doCameraSpecificMasking=False

# 
config.isr.masking.doSpecificMasking=False

# Interpolate masked pixels?
config.isr.doInterpolate=True

# Perform interpolation over pixels masked as saturated? NB: This is independent of doSaturation; if that is False this plane will likely be blank, resulting in a no-op here.
config.isr.doSaturationInterpolation=True

# Perform interpolation over pixels masked as NaN? NB: This is independent of doNanMasking; if that is False this plane will likely be blank, resulting in a no-op here.
config.isr.doNanInterpolation=True

# If True, ensure we interpolate NaNs after flat-fielding, even if we also have to interpolate them before flat-fielding.
config.isr.doNanInterpAfterFlat=False

# List of mask planes that should be interpolated.
config.isr.maskListToInterpolate=['SAT', 'BAD', 'UNMASKEDNAN']

# Save a copy of the pre-interpolated pixel values?
config.isr.doSaveInterpPixels=False

# The approximate flux of a zero-magnitude object in a one-second exposure, per filter.
config.isr.fluxMag0T1={'Unknown': 158489319246.11172}

# Default value for fluxMag0T1 (for an unrecognized filter).
config.isr.defaultFluxMag0T1=158489319246.11172

# Apply vignetting parameters?
config.isr.doVignette=False

# Center of vignetting pattern, in focal plane x coordinates.
config.isr.vignette.xCenter=0.0

# Center of vignetting pattern, in focal plane y coordinates.
config.isr.vignette.yCenter=0.0

# Radius of vignetting pattern, in focal plane coordinates.
config.isr.vignette.radius=100.0

# Number of points used to define the vignette polygon.
config.isr.vignette.numPolygonPoints=100

# Persist polygon used to define vignetted region?
config.isr.vignette.doWriteVignettePolygon=False

# Construct and attach a wavelength-dependent throughput curve for this CCD image?
config.isr.doAttachTransmissionCurve=False

# Load and use transmission_optics (if doAttachTransmissionCurve is True)?
config.isr.doUseOpticsTransmission=True

# Load and use transmission_filter (if doAttachTransmissionCurve is True)?
config.isr.doUseFilterTransmission=True

# Load and use transmission_sensor (if doAttachTransmissionCurve is True)?
config.isr.doUseSensorTransmission=True

# Load and use transmission_atmosphere (if doAttachTransmissionCurve is True)?
config.isr.doUseAtmosphereTransmission=True

# Perform illumination correction?
config.isr.doIlluminationCorrection=False

# Name of the illumination correction data product.
config.isr.illuminationCorrectionDataProductName='illumcor'

# Scale factor for the illumination correction.
config.isr.illumScale=1.0

# Only perform illumination correction for these filters.
config.isr.illumFilters=[]

# Persist postISRCCD?
config.isr.doWrite=True

# name for connection ccdExposure
config.isr.connections.ccdExposure='raw'

# name for connection camera
config.isr.connections.camera='camera'

# name for connection crosstalk
config.isr.connections.crosstalk='crosstalk'

# name for connection crosstalkSources
config.isr.connections.crosstalkSources='isrOverscanCorrected'

# name for connection bias
config.isr.connections.bias='bias'

# name for connection dark
config.isr.connections.dark='dark'

# name for connection flat
config.isr.connections.flat='flat'

# name for connection fringes
config.isr.connections.fringes='fringe'

# name for connection strayLightData
config.isr.connections.strayLightData='yBackground'

# name for connection bfKernel
config.isr.connections.bfKernel='bfKernel'

# name for connection newBFKernel
config.isr.connections.newBFKernel='brighterFatterKernel'

# name for connection defects
config.isr.connections.defects='defects'

# name for connection opticsTransmission
config.isr.connections.opticsTransmission='transmission_optics'

# name for connection filterTransmission
config.isr.connections.filterTransmission='transmission_filter'

# name for connection sensorTransmission
config.isr.connections.sensorTransmission='transmission_sensor'

# name for connection atmosphereTransmission
config.isr.connections.atmosphereTransmission='transmission_atmosphere'

# name for connection illumMaskedImage
config.isr.connections.illumMaskedImage='illum'

# name for connection outputExposure
config.isr.connections.outputExposure='postISRCCD'

# name for connection preInterpExposure
config.isr.connections.preInterpExposure='preInterpISRCCD'

# name for connection outputOssThumbnail
config.isr.connections.outputOssThumbnail='OssThumb'

# name for connection outputFlattenedThumbnail
config.isr.connections.outputFlattenedThumbnail='FlattenedThumb'

