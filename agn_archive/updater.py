"""
updater.py

Archive ingestion and update routines.
"""

import numpy as np
import pandas as pd

from pathlib import Path

from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u

from astropy.stats import sigma_clip
from astropy.stats import bootstrap

from .config import (
    RAW_DATA_PATH,
    ARCHIVE_PATH,
    TARGET_DATABASE,
    PIX_EDGE,
    APASS_MATCH_ARCSEC,
    MIN_STANDARDS,
    MAX_BOOTSTRAP,
    COMMIT_EVERY,
)

from .utils import (
    choose_aperture,
    robust_agn_match,
)


class ArchiveUpdater:

    def __init__(self, archive):

        self.archive = archive
        self.conn = archive.conn
        self.cur = self.conn.cursor()

    # ============================================================
    # Helper
    # ============================================================

    def _load_target_coordinates(self):

        target_file = Path(TARGET_DATABASE)

        targets = pd.read_csv(
            target_file,
            comment="#"
        )

        coords = {}

        for _, row in targets.iterrows():

            coords[row["directory"]] = (
                float(row["ra"]),
                float(row["dec"])
            )

        return coords

    # ============================================================
    # Find and ingest new images
    # ============================================================

    def update_images(self, target):

        print(f"Scanning {target}")

        sexdir = (
            ARCHIVE_PATH
            / target
            / "sextractor_ava"
        )

        cats = sorted(
            sexdir.glob("*_cat.fits")
        )

        print( f"Found {len(cats)} catalogues")

        for catfile in cats:

            fits_name = (
                catfile.name
                .replace(
                    "_cat.fits",
                    ".fits.fz"
                )
            )

            obs_date = (
                fits_name
                .split("-")[2]
            )

            exists = pd.read_sql(
                """
                SELECT image_id
                FROM images
                WHERE fits_file=?
                """,
                self.conn,
                params=[fits_name]
            )

            if len(exists):
                continue

            fits_path = (
                RAW_DATA_PATH
                / target
                / obs_date
                / fits_name
            )

            if not fits_path.exists():

                print(
                    f"Missing FITS:"
                    f" {fits_path}"
                )
                continue

            try:

                hdr = fits.getheader(
                    fits_path,
                    "SCI"
                )

            except Exception:

                hdr = fits.getheader(
                    fits_path,
                    1
                )

            row = {

                "fits_file":
                    fits_name,

                "obs_date":
                    obs_date,

                "object":
                    hdr.get(
                        "OBJECT",
                        target
                    ),

                "mjd":
                    hdr.get(
                        "MJD-OBS",
                        np.nan
                    ),

                "filter":
                    hdr.get(
                        "FILTER",
                        None
                    ),

                "airmass":
                    hdr.get(
                        "AIRMASS",
                        np.nan
                    ),

                "exptime":
                    hdr.get(
                        "EXPTIME",
                        np.nan
                    ),

                "seeing":
                    np.nan,

                "fwhm":
                    np.nan,

                "observatory":
                    hdr.get(
                        "SITEID",
                        None
                    ),

                "telid":
                    hdr.get(
                        "TELID",
                        None
                    ),

                "zp_mag":
                    np.nan,

                "zp_err":
                    np.nan,

                "n_std":
                    np.nan,

                "airmass_corr":
                    np.nan
            }

            pd.DataFrame(
                [row]
            ).to_sql(
                "images",
                self.conn,
                if_exists="append",
                index=False
            )

        self.conn.commit()

    # ============================================================
    # Process unprocessed images
    # ============================================================

    # def update_measurements(
    #     self,
    #     target,
    #     apass,
    #     filt_dict
    # ):

    #     target_coords = (
    #         self._load_target_coordinates()
    #     )

    #     if target not in target_coords:

    #         raise KeyError(
    #             f"{target} not found "
    #             f"in target database"
    #         )

    #     ra_agn, dec_agn = (
    #         target_coords[target]
    #     )

    #     agn_coord = SkyCoord(
    #         ra_agn * u.deg,
    #         dec_agn * u.deg
    #     )

    #     coo_apass = SkyCoord(
    #         apass["radeg"].values
    #         * u.deg,
    #         apass["decdeg"].values
    #         * u.deg
    #     )

    #     images = pd.read_sql(
    #         """
    #         SELECT i.*

    #         FROM images i

    #         LEFT JOIN
    #         agn_measurements a

    #         ON i.image_id=a.image_id

    #         WHERE
    #             i.object=?
    #         AND
    #             a.image_id IS NULL

    #         ORDER BY i.mjd
    #         """,
    #         self.conn,
    #         params=[target]
    #     )

    #     print(
    #         f"{target}: "
    #         f"{len(images)} "
    #         f"new images"
    #     )

    #     for i, row in images.iterrows():

    #         image_id = int(
    #             row.image_id
    #         )

    #         catfile = (
    #             ARCHIVE_PATH
    #             / target
    #             / "sextractor_ava"
    #             / row.fits_file.replace(
    #                 ".fits.fz",
    #                 "_cat.fits"
    #             )
    #         )

    #         if not catfile.exists():
    #             continue

    #         data = fits.getdata(catfile)

    #         if len(data) == 0:
    #             continue

    #         # =================================================
    #         # Update FWHM
    #         # =================================================

    #         fwhm = np.nanmedian(
    #             data["FWHM_IMAGE"]
    #         )

    #         self.cur.execute(
    #             """
    #             UPDATE images
    #             SET fwhm=?
    #             WHERE image_id=?
    #             """,
    #             (
    #                 float(fwhm),
    #                 image_id
    #             )
    #         )

    #         # =================================================
    #         # Coordinates
    #         # =================================================

    #         star_coord = SkyCoord(
    #             data["ALPHA_J2000"]
    #             * u.deg,
    #             data["DELTA_J2000"]
    #             * u.deg
    #         )

    #         idx_agn, sep, coords = (
    #             robust_agn_match(
    #                 star_coord,
    #                 agn_coord
    #             )
    #         )

    #         if idx_agn is None:
    #             continue

    #         idx_apass, d2d, _ = (
    #             coords.match_to_catalog_sky(
    #                 coo_apass
    #             )
    #         )
