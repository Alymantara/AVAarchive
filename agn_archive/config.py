"""
Configuration for AGNArchive
"""

from pathlib import Path


# ============================================================
# Paths
# ============================================================

# Root directory containing raw FITS files
#
# Example:
# /data/jvhs1/agn/raw_data/
#     Mrk_817/
#     NGC_5548/
#
RAW_DATA_PATH = Path(
    "/data/jvhs1/agn/raw_data"
)


# Root directory containing target folders
#
# Example:
# /data/jvhs1/agn/
#     Mrk_817/
#         sextractor_ava/
#
ARCHIVE_PATH = Path(
    "/data/jvhs1/agn"
)


# ============================================================
# Photometry settings
# ============================================================

# Minimum distance from image edge (pixels)
PIX_EDGE = 30

# Maximum AGN-source matching distance
MAX_AGN_MATCH_ARCSEC = 3.0

# Maximum astrometric shift allowed before
# catalogue correction is considered invalid
MAX_SHIFT_ARCSEC = 20.0

# APASS matching radius
APASS_MATCH_ARCSEC = 1.5


# ============================================================
# Zeropoint settings
# ============================================================

# Minimum number of standards required
MIN_STANDARDS = 3

# Sigma clipping threshold
SIGMA_CLIP = 3.0

# Maximum bootstrap realizations
MAX_BOOTSTRAP = 1000


# ============================================================
# Database settings
# ============================================================

# Commit frequency during large ingests
COMMIT_EVERY = 100


# ============================================================
# Aperture selection
# ============================================================

# Old catalogues (MJD < 60909)
#
# 10 aperture catalogues:
#   apertures 1-10
#
# New catalogues (MJD >= 60909)
#
# 12 aperture catalogues:
#   apertures 1-12
#
# Stored as zero-indexed array positions.
#

APER_1M_OLD = 7     # aperture 7
APER_1M_NEW = 9     # aperture 9

APER_2M_OLD = 10     # aperture 10
APER_2M_NEW = 12    # aperture 12


CATALOG_CHANGE_MJD = 60909


# ============================================================
# Default filenames
# ============================================================

TARGET_DATABASE = (
    "database_all_targets.txt"
)

FILTER_DICTIONARY = (
    "filter_dict.txt"
)

APASS_CATALOG = (
    "apass_pytics.csv"
)