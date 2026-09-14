# Disaster Relief Data Warehouse — Bangladesh

An MSc Data Warehousing course project: a dimensional data warehouse (fact constellation)
covering disaster impact, aid distribution, resource deployment, and donations for
disaster relief operations in Bangladesh.

## What's real vs. simulated

- **Real:** the 8 disaster events (names, types, dates), and the Bangladesh division/district
  geography used for `dim_location`.
- **Simulated:** all operational figures — deaths/injuries/displacement magnitudes, aid
  quantities, resource deployments, shelter occupancy, and donations. These are generated
  with realistic statistical distributions calibrated to each event's real severity tier,
  but they are **not actual reported statistics**. This mirrors the approach agreed in the
  project proposal (Section 6.1): ground the disaster dimension in reality, simulate the
  operational layer since granular data of that kind isn't publicly available.

## Folder structure

```
dw_project/
├── sql/
│   └── schema.sql              # DDL: all dimension & fact tables (PostgreSQL)
├── etl/
│   ├── simulate_data.py        # Generates all CSV data (dimensions + facts)
│   └── etl_load.py             # Loads CSVs into PostgreSQL via COPY
├── data/                       # Generated CSVs (output of simulate_data.py)
├── queries/
│   └── analytical_queries.sql  # All business questions + explicit OLAP demos
├── dashboard/
│   ├── export_dashboard_data.py# Pulls aggregates from the warehouse into JSON
│   ├── dashboard_data.json     # The exported aggregates
│   └── dashboard.html          # Self-contained interactive dashboard
└── docs/
    └── README.md                # This file
```

## How to run it end-to-end

Requires PostgreSQL 14+ and Python 3 with `pandas`, `numpy`, `faker`, `psycopg2-binary`.

```bash
# 1. Create the schema
psql -U postgres -d disaster_relief_dw -f sql/schema.sql

# 2. Generate the simulated data (writes CSVs to data/)
python3 etl/simulate_data.py

# 3. Load the data into the warehouse
python3 etl/etl_load.py

# 4. Run the analytical queries
psql -U postgres -d disaster_relief_dw -f queries/analytical_queries.sql

# 5. Rebuild the dashboard after any data change
python3 dashboard/export_dashboard_data.py
python3 dashboard/build_dashboard.py

# 6. Rebuild the DSS after any data change
psql -U postgres -d disaster_relief_dw -f sql/dss_view.sql
python3 dashboard/export_dss_data.py
python3 dashboard/build_dss.py
```

## Part 2: Decision Support System (dss.html)

A rule-based district prioritization tool answering "where should relief go next?" —
built directly on top of the warehouse, not a separate system.

**How it works:** `sql/dss_view.sql` creates `dw.vw_dss_district_factors`, a view that
computes four normalized (0–1) factors per district:
- **Impact severity** — deaths, displaced, economic loss
- **Aid coverage gap** — impact relative to aid already delivered (underserved districts score higher)
- **Shelter overcrowding risk** — peak shelter occupancy vs. capacity (can exceed 1.0)
- **Baseline vulnerability** — from `dim_location.vulnerability_index`

`export_dss_data.py` pulls this view into JSON; `build_dss.py` embeds it into
`dss_template.html` to produce `dss.html`. The final dashboard lets you drag four
weight sliders and re-ranks all districts live, in the browser, with a plain-language
rationale per district (e.g. "shelters over capacity; high need relative to aid received").
This is intentionally transparent and rule-based rather than a black-box model, so every
ranking can be explained and defended in a viva.

**To reproduce a change flowing through to the DSS:** any INSERT/UPDATE to
`fact_disaster_impact`, `fact_aid_distribution`, or `fact_resource_deployment`, followed by
re-running the DSS view + export + build steps above, will change the rankings — this can be
demonstrated the same way the dashboard's live-data behavior was verified (see the project's
"how it works" discussion in your report's methodology section).


## Design notes for your report

- **Grain statements** (needed for your write-up):
  - `fact_disaster_impact`: one row per disaster event, per affected district, per day
  - `fact_aid_distribution`: one row per organization, per resource type, per district, per day
  - `fact_resource_deployment`: one row per organization, per district, per day (with optional shelter linkage)
  - `fact_donations`: one row per donation transaction
- **Slowly Changing Dimension**: `dim_location` is Type 2 — every district has two versions
  (pre-2022 and 2022-onward) with different population figures, demonstrating historical
  tracking. Query 6.1 in `analytical_queries.sql` shows this for Khulna.
- **Conformed dimensions**: `dim_time`, `dim_location`, `dim_disaster_event`, and
  `dim_organization` are shared across multiple fact tables — this is what makes it a
  fact constellation rather than a simple star schema.
- **Shelter as a resource**: rather than a fifth fact table, shelter capacity/occupancy
  are measures within `fact_resource_deployment`, linked via `dim_shelter`, since shelters
  are a resource organizations deploy and manage alongside personnel and vehicles.

## Known simplifications (worth acknowledging in your report's limitations section)

- Real-time/streaming ingestion is out of scope; this is a batch-loaded warehouse.
- Aid distribution and resource deployment are simulated with independent random draws
  per organization/day rather than a realistic logistics/coordination model.
- Donor identities are anonymized/generic donor-type categories, not real individuals or
  companies, which is intentional (privacy) but means donor-level analysis is illustrative only.
