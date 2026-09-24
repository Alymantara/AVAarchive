"""
Main AGNArchive interface.
"""

import sqlite3
import numpy as np
import pandas as pd

from astropy.time import Time

from .utils import (
    date_to_mjd,
    apply_calibration,
    calibrated_mag_error,
)

from .updater import ArchiveUpdater


class AGNArchive:

    def __init__(self, dbfile):

        self.dbfile = dbfile

        self.conn = sqlite3.connect(
            dbfile
        )

    # ========================================================
    # Basic methods
    # ========================================================

    def close(self):

        self.conn.close()

    def query(
        self,
        sql,
        params=None
    ):

        return pd.read_sql(
            sql,
            self.conn,
            params=params
        )

    # ========================================================
    # Internal utilities
    # ========================================================

    def _to_mjd(
        self,
        value
    ):

        return date_to_mjd(
            value
        )

    # ========================================================
    # Database creation
    # ========================================================

    def create_tables(self):

        cur = self.conn.cursor()

        # ----------------------------------------------------
        # Images
        # ----------------------------------------------------

        cur.execute("""
        CREATE TABLE IF NOT EXISTS images (

            image_id INTEGER PRIMARY KEY AUTOINCREMENT,

            fits_file TEXT UNIQUE,

            obs_date TEXT,

            object TEXT,

            mjd REAL,

            filter TEXT,

            airmass REAL,

            exptime REAL,

            seeing REAL,

            fwhm REAL,

            observatory TEXT,

            telid TEXT,

            zp_mag REAL,

            zp_err REAL,

            n_std INTEGER,

            airmass_corr REAL

        )
        """)

        # ----------------------------------------------------
        # AGN measurements
        # ----------------------------------------------------

        cur.execute("""
        CREATE TABLE IF NOT EXISTS agn_measurements (

            measurement_id INTEGER
            PRIMARY KEY AUTOINCREMENT,

            image_id INTEGER UNIQUE,

            apass_id INTEGER,

            mag REAL,
            mag_err REAL,

            aperture INTEGER,

            x_image REAL,
            y_image REAL,

            separation_arcsec REAL,

            valid_calibrator INTEGER
            DEFAULT 0,

            FOREIGN KEY(image_id)
            REFERENCES images(image_id)

        )
        """)

        # ----------------------------------------------------
        # Field measurements
        # ----------------------------------------------------

        cur.execute("""
        CREATE TABLE IF NOT EXISTS field_measurements (

            measurement_id INTEGER
            PRIMARY KEY AUTOINCREMENT,

            image_id INTEGER NOT NULL,

            source_id INTEGER,

            apass_id INTEGER,

            is_agn INTEGER
            DEFAULT 0,

            valid_calibrator INTEGER
            DEFAULT 0,

            x_image REAL,
            y_image REAL,

            mag REAL,
            mag_err REAL,

            aperture INTEGER,

            apass_sep_arcsec REAL,

            FOREIGN KEY(image_id)
            REFERENCES images(image_id)

        )
        """)

        # ----------------------------------------------------
        # Indexes
        # ----------------------------------------------------

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_object
        ON images(object)
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_mjd
        ON images(mjd)
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_agn_image
        ON agn_measurements(image_id)
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_field_image
        ON field_measurements(image_id)
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_field_apass
        ON field_measurements(apass_id)
        """)

        self.conn.commit()

    # ========================================================
    # Summary
    # ========================================================

    def summary(self):

        sql = """
        SELECT

            COUNT(*) AS n_images,

            COUNT(DISTINCT object)
            AS n_targets,

            MIN(mjd) AS first_mjd,

            MAX(mjd) AS last_mjd

        FROM images
        """

        return pd.read_sql(
            sql,
            self.conn
        )

    # ========================================================
    # Target information
    # ========================================================

    def list_targets(self):

        sql = """
        SELECT DISTINCT object
        FROM images
        ORDER BY object
        """

        return pd.read_sql(
            sql,
            self.conn
        )

    # ========================================================
    # Image table
    # ========================================================

    def get_image_info(
        self,
        target,
        start=None,
        end=None
    ):

        start = self._to_mjd(start)
        end = self._to_mjd(end)

        sql = """
        SELECT *
        FROM images
        WHERE object=?
        """

        params = [target]

        if start is not None:

            sql += """
            AND mjd >= ?
            """

            params.append(start)

        if end is not None:

            sql += """
            AND mjd <= ?
            """

            params.append(end)

        sql += """
        ORDER BY mjd
        """

        return pd.read_sql(
            sql,
            self.conn,
            params=params
        )

    # ========================================================
    # AGN light curve
    # ========================================================

    def get_agn_lc(
        self,
        target,
        start=None,
        end=None,
        calibrated=True
    ):

        start = self._to_mjd(start)
        end = self._to_mjd(end)

        sql = """
        SELECT

            i.object,
            i.mjd,
            i.filter,
            i.telid,

            i.zp_mag,
            i.zp_err,

            i.airmass_corr,

            a.*

        FROM agn_measurements a

        JOIN images i

        ON a.image_id=i.image_id

        WHERE i.object=?
        """

        params = [target]

        if start is not None:

            sql += """
            AND i.mjd >= ?
            """

            params.append(start)

        if end is not None:

            sql += """
            AND i.mjd <= ?
            """

            params.append(end)

        sql += """
        ORDER BY i.mjd
        """

        df = pd.read_sql(
            sql,
            self.conn,
            params=params
        )

        if calibrated:

            df["cal_mag"] = (
                df["mag"]
                + df["zp_mag"]
                - df["airmass_corr"]
            )

            df["cal_mag_err"] = (
                calibrated_mag_error(
                    df["mag_err"],
                    df["zp_err"]
                )
            )

        return df

    # ========================================================
    # Field stars
    # ========================================================

    def get_agn_stan(
        self,
        target,
        start=None,
        end=None,
        calibrators_only=False
    ):

        start = self._to_mjd(start)
        end = self._to_mjd(end)

        sql = """
        SELECT

            i.object,
            i.mjd,
            i.filter,
            i.telid,

            i.airmass,
            i.seeing,

            i.zp_mag,
            i.zp_err,

            i.airmass_corr,

            f.*

        FROM field_measurements f

        JOIN images i

        ON f.image_id=i.image_id

        WHERE i.object=?
        """

        params = [target]

        if start is not None:

            sql += """
            AND i.mjd >= ?
            """

            params.append(start)

        if end is not None:

            sql += """
            AND i.mjd <= ?
            """

            params.append(end)

        if calibrators_only:

            sql += """
            AND f.valid_calibrator=1
            """

        sql += """
        ORDER BY i.mjd
        """

        df = pd.read_sql(
            sql,
            self.conn,
            params=params
        )

        df["cal_mag"] = (
            df["mag"]
            + df["zp_mag"]
            - df["airmass_corr"]
        )

        df["cal_mag_err"] = (
            calibrated_mag_error(
                df["mag_err"],
                df["zp_err"]
            )
        )

        return df

    # ========================================================
    # PyTICS export
    # ========================================================

    def get_pytics(
        self,
        target,
        start=None,
        end=None
    ):

        df = self.get_agn_stan(
            target,
            start=start,
            end=end,
            calibrators_only=True
        )

        return df[[
            "apass_id",
            "filter",
            "mjd",
            "mag",
            "mag_err",
            "airmass_corr",
            "zp_mag",
            "zp_err",
            "telid",
            "airmass",
            "seeing"
        ]].rename(
            columns={
                "airmass_corr": "extra",
                "zp_mag": "zp",
                "zp_err": "zp_err"
            }
        )

    # ========================================================
    # Updating routines
    # ========================================================

    def update_images(
        self,
        target
    ):

        ArchiveUpdater(
            self
        ).update_images(
            target
        )

    def update_measurements(
        self,
        target,
        apass,
        filt_dict
    ):

        ArchiveUpdater(
            self
        ).update_measurements(
            target,
            apass,
            filt_dict
        )

    def update_target(
        self,
        target,
        apass,
        filt_dict
    ):

        ArchiveUpdater(
            self
        ).update_target(
            target,
            apass,
            filt_dict
        )