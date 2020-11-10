# -*- coding: utf-8 -*-
from .ButlerWrapper import ButlerWrapper
from .CamDataCollector import CamDataCollector
from .CamIsrWrapper import CamIsrWrapper
from .SourceProcessor import SourceProcessor
from .WepController import WepController
from .Utility import FilterType, CamType, BscDbType

# These classes need the scons to build the .so library. In the Jenkins test,
# this will be a problem to import.
try:
    from .WfEstimator import WfEstimator
    from .SourceSelector import SourceSelector
except ImportError:
    pass

# The version file is gotten by the scons. However, the scons does not support
# the build without unit tests. This is a needed function for the Jenkins to
# use.
try:
    from .version import *
except ImportError:
    __version__ = "?"
