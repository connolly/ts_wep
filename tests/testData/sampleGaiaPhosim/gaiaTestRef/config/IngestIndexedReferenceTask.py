import lsst.meas.algorithms.ingestIndexReferenceTask
assert type(config)==lsst.meas.algorithms.ingestIndexReferenceTask.IngestIndexedReferenceConfig, 'config is of type %s.%s instead of lsst.meas.algorithms.ingestIndexReferenceTask.IngestIndexedReferenceConfig' % (type(config).__module__, type(config).__name__)
import lsst.meas.algorithms.readTextCatalogTask
import lsst.meas.algorithms.indexerRegistry
# Version number of the persisted on-disk storage format.
# Version 0 had Jy as flux units (default 0 for unversioned catalogs).
# Version 1 had nJy as flux units.
config.dataset_config.format_version=1

# String to pass to the butler to retrieve persisted files.
config.dataset_config.ref_dataset_name='cal_ref_cat'

# Depth of the HTM tree to make.  Default is depth=7 which gives ~ 0.3 sq. deg. per trixel.
config.dataset_config.indexer['HTM'].depth=7

config.dataset_config.indexer.name='HTM'
# Number of python processes to use when ingesting.
config.n_processes=1

# Number of lines to skip when reading the text reference file.
config.file_reader.header_lines=0

# An ordered list of column names to use in ingesting the catalog. With an empty list, column names will be discovered from the first line after the skipped header lines.
config.file_reader.colnames=[]

# Delimiter to use when reading text reference files.  Comma is default.
config.file_reader.delimiter=','

# Format of files to read, from the astropy.table I/O list here:http://docs.astropy.org/en/stable/io/unified.html#built-in-table-readers-writers
config.file_reader.format='csv'

# Name of RA column (values in decimal degrees)
config.ra_name='ra'

# Name of Dec column (values in decimal degrees)
config.dec_name='dec'

# Name of RA error column
config.ra_err_name='ra_err'

# Name of Dec error column
config.dec_err_name='dec_err'

# Unit of RA/Dec error fields (astropy.unit.Unit compatible)
config.coord_err_unit='arcsec'

# The values in the reference catalog are assumed to be in AB magnitudes. List of column names to use for photometric information.  At least one entry is required.
config.mag_column_list=['phot_g_mean', 'phot_rp_mean']

# A map of magnitude column name (key) to magnitude error column (value).
config.mag_err_column_map={'phot_g_mean': 'phot_g_mean_err', 'phot_rp_mean': 'phot_rp_mean_err'}

# Name of column stating if satisfactory for photometric calibration (optional).
config.is_photometric_name=None

# Name of column stating if the object is resolved (optional).
config.is_resolved_name=None

# Name of column stating if the object is measured to be variable (optional).
config.is_variable_name=None

# Name of column to use as an identifier (optional).
config.id_name='id'

# Name of proper motion RA column
config.pm_ra_name=None

# Name of proper motion Dec column
config.pm_dec_name=None

# Name of proper motion RA error column
config.pm_ra_err_name=None

# Name of proper motion Dec error column
config.pm_dec_err_name=None

# Scale factor by which to multiply proper motion values to obtain units of milliarcsec/year
config.pm_scale=1.0

# Name of parallax column
config.parallax_name=None

# Name of parallax error column
config.parallax_err_name=None

# Scale factor by which to multiply parallax values to obtain units of milliarcsec
config.parallax_scale=1.0

# Name of epoch column
config.epoch_name=None

# Format of epoch column: any value accepted by astropy.time.Time, e.g. 'iso' or 'unix'
config.epoch_format=None

# Scale of epoch column: any value accepted by astropy.time.Time, e.g. 'utc'
config.epoch_scale=None

# Extra columns to add to the reference catalog.
config.extra_col_names=[]

