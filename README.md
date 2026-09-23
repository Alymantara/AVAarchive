# AGNArchive

`AGNArchive` is a lightweight Python interface for querying an SQLite database containing astronomical image metadata. It is designed for long-term AGN monitoring programs, but can be adapted to any imaging archive.

The class provides a simple API to retrieve observations by target, date range, observing night, filter, or telescope, while returning results as Pandas DataFrames.

---

## Database Structure

The archive assumes a table named `images` with the following schema:

```sql
CREATE TABLE IF NOT EXISTS images (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE,
    folder TEXT,
    object_name TEXT,
    mjd REAL,
    filter TEXT,
    exptime REAL,
    seeing REAL,
    fwhm REAL,
    obs TEXT,
    telid TEXT,
    zp REAL,
    zp_err REAL,
    nstd INT
);
```

---

## Recommended Indexes

For efficient AGN and time-range queries:

```sql
CREATE INDEX IF NOT EXISTS idx_object
ON images(object_name);

CREATE INDEX IF NOT EXISTS idx_mjd
ON images(mjd);

CREATE INDEX IF NOT EXISTS idx_object_mjd
ON images(object_name, mjd);
```

The composite `(object_name, mjd)` index significantly speeds up queries such as:

```python
archive.get_agn(
    "Mrk_817",
    start="2021-01-01",
    end="2022-01-01"
)
```

---

## Installation

```python
from agn_archive import AGNArchive
```

Create a connection to an existing archive:

```python
archive = AGNArchive("agn_archive.db")
```

---

## Methods

### get_agn()

Retrieve observations of a target.

```python
archive.get_agn("Mrk_817")
```

Returns all observations of the target.

#### Date range selection

Calendar dates:

```python
archive.get_agn(
    "Mrk_817",
    start="2021-01-01",
    end="2022-01-01"
)
```

MJD values:

```python
archive.get_agn(
    "Mrk_817",
    start=59215,
    end=59600
)
```

Date strings are automatically converted to MJD using Astropy.

---

### list_targets()

Return all unique objects in the archive.

```python
targets = archive.list_targets()
```

Example output:

```text
Mrk_817
NGC_5548
ESO_511-30
Ark_120
```

---

### get_night()

Retrieve all observations from a particular observing date folder.

```python
archive.get_night("20210129")
```

---

### get_filter()

Retrieve all observations obtained with a given filter.

```python
archive.get_filter("rp")
```

---

### get_telid()

Retrieve all observations obtained with a specific telescope.

```python
archive.get_telid("elp1m006")
```

---

### nearest_observation()

Find the observation closest to a specified MJD.

```python
archive.nearest_observation(
    "Mrk_817",
    59243.5
)
```

Returns a DataFrame containing the nearest exposure.

---

### summary()

Return basic archive statistics.

```python
archive.summary()
```

Example:

```text
n_images     527431
n_targets        92
first_mjd   54892.3
last_mjd    61234.7
```

---

### query()

Execute arbitrary SQL queries.

```python
archive.query("""
SELECT *
FROM images
WHERE seeing < 1.5
""")
```

Returns a Pandas DataFrame.

---

## Working in Jupyter Notebooks

To automatically reload changes made to the class during development:

```python
%load_ext autoreload
%autoreload 2

from agn_archive import AGNArchive
```

Any modifications to `agn_archive.py` will be available immediately after saving.

---

## Example Workflow

```python
from agn_archive import AGNArchive

archive = AGNArchive("agn_archive.db")

# Retrieve all observations
mrk817 = archive.get_agn("Mrk_817")

# Retrieve observations in a date range
mrk817_recent = archive.get_agn(
    "Mrk_817",
    start="2023-01-01",
    end="2024-01-01"
)

# List all targets
targets = archive.list_targets()

# Summary statistics
summary = archive.summary()

archive.close()
```

---

## Future Extensions

Potential additions include:

- Coordinate-based cone searches
- Crossmatching with external catalogues
- HEALPix indexing
- Automatic FITS-header ingestion
- Light-curve generation
- Observation quality filtering
- Multi-object queries
- Interactive plotting utilities
