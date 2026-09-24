"""
Utility functions for AGNArchive.
"""

import numpy as np

from astropy.time import Time
from astropy.coordinates import SkyCoord
import astropy.units as u

from .config import (
    APER_1M_OLD,
    APER_1M_NEW,
    APER_2M_OLD,
    APER_2M_NEW,
    CATALOG_CHANGE_MJD,
)


# ============================================================
# Time utilities
# ============================================================

def date_to_mjd(date):

    if date is None:
        return None

    if isinstance(date, str):
        return Time(date).mjd

    return float(date)


def mjd_to_date(mjd):

    return Time(mjd, format="mjd").iso


# ============================================================
# Aperture selection
# ============================================================

def choose_aperture(
    mjd,
    telid,
    naper
):
    """
    Choose science aperture.

    1m:
        aperture 7 (old)
        aperture 9 (new)

    2m:
        aperture 10 (old)
        aperture 12 (new)
    """

    telid = str(telid).lower()

    is_2m = "2m" in telid

    if is_2m:

        if mjd < CATALOG_CHANGE_MJD:
            return min(
                APER_2M_OLD,
                naper - 1
            )

        return min(
            APER_2M_NEW,
            naper - 1
        )

    else:

        if mjd < CATALOG_CHANGE_MJD:
            return min(
                APER_1M_OLD,
                naper - 1
            )

        return min(
            APER_1M_NEW,
            naper - 1
        )


# ============================================================
# Photometric conversions
# ============================================================

def counts_to_rate_mag(
    mag,
    exptime
):
    """
    Convert instrumental magnitude
    to count-rate magnitude.
    """

    if not np.isfinite(exptime):
        return np.nan

    if exptime <= 0:
        return np.nan

    return (
        mag
        + 2.5*np.log10(exptime)
    )


def apply_calibration(
    mag,
    zp_mag,
    airmass_corr=0.0
):
    """
    Apply zeropoint calibration.
    """

    return (
        mag
        + zp_mag
        - airmass_corr
    )


def calibrated_mag_error(
    mag_err,
    zp_err
):
    """
    Propagate magnitude uncertainty.
    """

    return np.sqrt(
        mag_err**2 +
        zp_err**2
    )


# ============================================================
# AB magnitude conversions
# ============================================================

def abmag_to_jy(mag):
    """
    AB magnitude -> Jy
    """

    return (
        3631.0
        * 10**(-0.4 * mag)
    )


def abmag_to_mjy(mag):
    """
    AB magnitude -> mJy
    """

    return (
        3631e3
        * 10**(-0.4 * mag)
    )


def jy_to_abmag(jy):
    """
    Jy -> AB magnitude
    """

    jy = np.asarray(jy)

    return (
        -2.5*np.log10(jy / 3631.)
    )


def mjy_to_abmag(mjy):
    """
    mJy -> AB magnitude
    """

    return jy_to_abmag(
        np.asarray(mjy) / 1000.
    )


def magerr_to_fluxerr(
    mag,
    mag_err
):
    """
    Convert AB mag error
    into mJy error.
    """

    flux = abmag_to_mjy(mag)

    return (
        flux
        * np.log(10)
        / 2.5
        * mag_err
    )


# ============================================================
# Matching utilities
# ============================================================

def robust_agn_match(
    star_coord,
    agn_coord,
    max_sep_arcsec=3.0,
    shift_limit_arcsec=20.0,
):
    """
    Robust AGN matching.

    Attempts direct match.

    If unsuccessful:
        estimate a global astrometric
        shift and retry.
    """

    idx, sep, _ = (
        agn_coord.match_to_catalog_sky(
            star_coord
        )
    )

    idx = int(
        np.asarray(idx).ravel()[0]
    )

    sep = np.asarray(
        sep
    ).ravel()[0]

    if sep.arcsec < max_sep_arcsec:

        return (
            idx,
            sep.arcsec,
            star_coord
        )

    dra = (
        agn_coord.ra.deg
        - star_coord[idx].ra.deg
    )

    ddec = (
        agn_coord.dec.deg
        - star_coord[idx].dec.deg
    )

    shift = (
        np.sqrt(
            dra**2 + ddec**2
        )
        * 3600.
    )

    if shift > shift_limit_arcsec:

        return (
            None,
            None,
            None
        )

    corrected = SkyCoord(
        (star_coord.ra.deg + dra)
        * u.deg,

        (star_coord.dec.deg + ddec)
        * u.deg
    )

    idx2, sep2, _ = (
        agn_coord.match_to_catalog_sky(
            corrected
        )
    )

    idx2 = int(
        np.asarray(idx2).ravel()[0]
    )

    sep2 = np.asarray(
        sep2
    ).ravel()[0]

    if sep2.arcsec < max_sep_arcsec:

        return (
            idx2,
            sep2.arcsec,
            corrected
        )

    return (
        None,
        None,
        None
    )