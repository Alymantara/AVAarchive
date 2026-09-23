import sqlite3
import pandas as pd
from astropy.time import Time


class AGNArchive:

    def __init__(self, dbfile):
        """
        Connect to an SQLite database.

        Parameters
        ----------
        dbfile : str
            Path to SQLite database.
        """
        self.conn = sqlite3.connect(dbfile)

    def close(self):
        """Close database connection."""
        self.conn.close()

    def _to_mjd(self, value):
        """
        Convert YYYY-MM-DD string to MJD.
        If already numeric, return unchanged.
        """

        if value is None:
            return None

        if isinstance(value, str):
            return Time(value).mjd

        return float(value)

    def query(self, sql, params=None):
        """
        Generic SQL query returning a dataframe.
        """

        return pd.read_sql(
            sql,
            self.conn,
            params=params
        )

    def get_agn(self,
                target,
                start=None,
                end=None):
        """
        Retrieve observations for a target.

        Parameters
        ----------
        target : str
            Object name.

        start, end :
            Either MJD or YYYY-MM-DD.

        Returns
        -------
        pandas.DataFrame
        """

        start = self._to_mjd(start)
        end = self._to_mjd(end)

        sql = """
        SELECT *
        FROM images
        WHERE object = ?
        """

        params = [target]

        if start is not None:
            sql += " AND mjd >= ?"
            params.append(start)

        if end is not None:
            sql += " AND mjd <= ?"
            params.append(end)

        sql += " ORDER BY mjd"

        return pd.read_sql(
            sql,
            self.conn,
            params=params
        )

    def list_targets(self):
        """
        Return list of all targets.
        """

        sql = """
        SELECT DISTINCT object
        FROM images
        ORDER BY object
        """

        return pd.read_sql(sql, self.conn)

    def get_night(self, folder):
        """
        Return all observations
        from a specific date folder.

        Example:
            20210129
        """

        sql = """
        SELECT *
        FROM images
        WHERE folder = ?
        """

        return pd.read_sql(
            sql,
            self.conn,
            params=[str(folder)]
        )

    def get_filter(self, filt):
        """
        Return observations in filter.
        """

        sql = """
        SELECT *
        FROM images
        WHERE filter = ?
        ORDER BY mjd
        """

        return pd.read_sql(
            sql,
            self.conn,
            params=[filt]
        )

    def get_telid(self, telid):
        """
        Return observations
        from a specific telescope.
        """

        sql = """
        SELECT *
        FROM images
        WHERE telid = ?
        ORDER BY mjd
        """

        return pd.read_sql(
            sql,
            self.conn,
            params=[telid]
        )

    def nearest_observation(self,
                            target,
                            mjd):
        """
        Find closest observation in time.
        """

        sql = """
        SELECT *
        FROM images
        WHERE object = ?
        ORDER BY ABS(mjd - ?)
        LIMIT 1
        """

        return pd.read_sql(
            sql,
            self.conn,
            params=[target, mjd]
        )

    def summary(self):
        """
        Quick archive summary.
        """

        sql = """
        SELECT
            COUNT(*) AS n_images,
            COUNT(DISTINCT object) AS n_targets,
            MIN(mjd) AS first_mjd,
            MAX(mjd) AS last_mjd
        FROM images
        """

        return pd.read_sql(sql, self.conn)