"""
AGNArchive

SQLite-based archive for AGN monitoring data.

Main interface:

    from agn_archive import AGNArchive

"""

from .agn_archive import AGNArchive

from .utils import (
    choose_aperture,
    robust_agn_match,
    date_to_mjd,
    mjd_to_date,
    counts_to_rate_mag,
    apply_calibration,
    calibrated_mag_error,
    abmag_to_jy,
    abmag_to_mjy,
    jy_to_abmag,
    mjy_to_abmag,
    magerr_to_fluxerr,
)

__version__ = "0.1.0"

__all__ = [
    "AGNArchive",

    "choose_aperture",
    "robust_agn_match",

    "date_to_mjd",
    "mjd_to_date",

    "counts_to_rate_mag",
    "apply_calibration",
    "calibrated_mag_error",

    "abmag_to_jy",
    "abmag_to_mjy",
    "jy_to_abmag",
    "mjy_to_abmag",
    "magerr_to_fluxerr",
]