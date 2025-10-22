For collaborators

This repository contains code and instructions to rebuild a local DuckDB warehouse from Brazil’s SIM mortality Parquet files.
Raw data and large artifacts are not stored here—only scripts, SQL, and docs for full reproducibility.

TL;DR (5-minute setup)
# 0) Prereqs (macOS)
brew install duckdb                     # database engine
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip -r requirements.txt  # pandas/pyarrow etc.

# 1) Ensure you have the Parquet data locally:
#    /Users/kiyomotoyuuki/projects/Brazil Data/DATA/<UF>/ETLSIM.DORES_<UF>_<YYYY>_t.parquet

# 2) Build the warehouse (creates dores.duckdb)
duckdb "/Users/kiyomotoyuuki/projects/Brazil Data/WAREHOUSE/dores.duckdb" -c ".read scripts/build_warehouse.sql"

# 3) Create analysis view
duckdb "/Users/kiyomotoyuuki/projects/Brazil Data/WAREHOUSE/dores.duckdb" -c ".read scripts/create_view_clean.sql"

# 4) Quick health checks
duckdb "/Users/kiyomotoyuuki/projects/Brazil Data/WAREHOUSE/dores.duckdb" -c ".read scripts/quick_checks.sql"

What’s in here (data model)

Base table: dores – A warehouse “raw” table that unions all SIM Parquet files.

It mirrors source columns and adds just three helpers:

year (from filename), uf (state code from folder), filename (source path).

Purpose: traceability/debugging, “raw-ish” access.

Analysis view: dores_clean – A read-only view with analysis-friendly columns:

uf, year, date_death (from DTOBITO), date_birth (from DTNASC),
sex_code (from SEXO), race_code (from RACACOR), icd10_underlying (from CAUSABAS).

Dates are normalized (strip non-digits → left-pad to 8 → format YYYY-MM-DD → DATE).

Uses TRY_* conversions (bad values become NULL). No mutation of dores.

Codebook table: codebook – Variable documentation:

Schema: (var TEXT, label_en TEXT, descr_en TEXT, source TEXT).

Loaded from WAREHOUSE/codebook.csv. It does not change your data tables.

Naming note: dores is just a table name. If preferred, we can rename it to sim_deaths—update the SQL accordingly.

Repository layout (code only)
scripts/
  ├─ build_warehouse.sql       # create/refresh base table `dores`
  ├─ create_view_clean.sql     # create/refresh `dores_clean` view
  ├─ quick_checks.sql          # coverage sanity checks
  └─ run_all.sh                # one-shot: build + view + checks + example export
tools/
  └─ parquet_to_csv.py         # quick single-file Parquet → CSV helper
runbook/
  └─ YYYY-MM-DD_progress.md    # step-by-step notes (optional)


.gitignore excludes DATA/, *.duckdb, and other large artifacts by default.

Build & refresh

Rebuild anytime from the Parquet source:

duckdb "/Users/kiyomotoyuuki/projects/Brazil Data/WAREHOUSE/dores.duckdb" \
  -c ".read scripts/build_warehouse.sql"

duckdb "/Users/kiyomotoyuuki/projects/Brazil Data/WAREHOUSE/dores.duckdb" \
  -c ".read scripts/create_view_clean.sql"


Load/update the codebook (optional, for documentation within the DB):

duckdb "/Users/kiyomotoyuuki/projects/Brazil Data/WAREHOUSE/dores.duckdb" -c "
CREATE TABLE IF NOT EXISTS codebook(var TEXT, label_en TEXT, descr_en TEXT, source TEXT);
DELETE FROM codebook;
COPY codebook FROM '/Users/kiyomotoyuuki/projects/Brazil Data/WAREHOUSE/codebook.csv' (HEADER, DELIMITER ',');
SELECT COUNT(*) AS n_rows FROM codebook;
"

Common tasks
Preview raw data (AC, 2016 – first 5 rows)
duckdb "/Users/kiyomotoyuuki/projects/Brazil Data/WAREHOUSE/dores.duckdb" -c "
COPY (
  SELECT * FROM dores WHERE uf='AC' AND year=2016 LIMIT 5
) TO '/Users/kiyomotoyuuki/projects/Brazil Data/WAREHOUSE/AC_2016_head5_raw.csv'
(HEADER, DELIMITER ',');
"

Export a clean subset (AC, 2016 – selected columns, first 5 rows)
duckdb "/Users/kiyomotoyuuki/projects/Brazil Data/WAREHOUSE/dores.duckdb" -c "
COPY (
  SELECT uf, year, date_death, date_birth, sex_code, race_code, icd10_underlying
  FROM dores_clean
  WHERE uf='AC' AND year=2016
  ORDER BY date_death NULLS LAST
  LIMIT 5
) TO '/Users/kiyomotoyuuki/projects/Brazil Data/WAREHOUSE/AC_2016_head5_clean.csv'
(HEADER, DELIMITER ',');
"

Coverage & sanity checks
duckdb "/Users/kiyomotoyuuki/projects/Brazil Data/WAREHOUSE/dores.duckdb" -c ".read scripts/quick_checks.sql"

List full column schema of a source Parquet (for auditing)
duckdb -c "
CREATE TEMP VIEW _p AS
SELECT * FROM read_parquet('/Users/kiyomotoyuuki/projects/Brazil Data/DATA/AC/ETLSIM.DORES_AC_2016_t.parquet') LIMIT 0;
SELECT ordinal_position AS pos, column_name AS name, data_type
FROM information_schema.columns WHERE table_name='_p' ORDER BY pos;
"

Do / Don’t

Do

Keep RAW Parquet immutable. Rebuild the DB whenever needed.

Use dores_clean for analysis/exports; explicitly list columns in SELECT (avoid SELECT *).

Record variable meanings in codebook.csv and load into the DB.

Don’t

Don’t commit DATA/ or any *.duckdb/large CSV to Git.

Don’t mutate dores; add derived/cleaned fields via the view.

Don’t rely on mixed date formats—use the view’s normalized dates.

Optional: GitHub CLI quickstart
brew install gh
gh --version
gh auth login     # choose HTTPS → browser login

# Create a new repo from current folder and push
gh repo create Brazil-Data-warehouse --public --source=. --remote=origin --push

Questions / contributions

Open an Issue or PR on GitHub.

When adding columns to the clean view, please:

update scripts/create_view_clean.sql,

add the variable to WAREHOUSE/codebook.csv,

include a brief note in runbook/<date>_progress.md.