SET search_path TO dw;

-- ============================================================
-- Decision Support System — District Priority Scoring
-- ============================================================
-- Purpose: rank districts by relief priority using four factors:
--   1. Impact severity   (deaths, displaced, economic loss)
--   2. Aid gap           (impact relative to aid already delivered — underserved = high priority)
--   3. Shelter risk       (peak shelter occupancy vs. capacity)
--   4. Baseline vulnerability (dim_location.vulnerability_index)
--
-- All four are normalized to a 0-1 scale (min-max normalization across
-- affected districts) so they can be combined with adjustable weights.
-- This view does the normalization once; the dashboard applies weights
-- client-side so a user can interactively re-rank without re-querying.
-- ============================================================

DROP VIEW IF EXISTS dw.vw_dss_district_factors;

CREATE VIEW dw.vw_dss_district_factors AS
WITH impact AS (
    SELECT dl.district, dl.division,
           SUM(fi.deaths) AS total_deaths,
           SUM(fi.displaced) AS total_displaced,
           SUM(fi.economic_loss_bdt) AS total_economic_loss
    FROM fact_disaster_impact fi
    JOIN dim_location dl ON fi.location_key = dl.location_key
    GROUP BY dl.district, dl.division
),
aid AS (
    SELECT dl.district,
           SUM(fa.delivery_cost_bdt) AS total_aid_delivered
    FROM fact_aid_distribution fa
    JOIN dim_location dl ON fa.location_key = dl.location_key
    GROUP BY dl.district
),
shelter AS (
    SELECT dl.district,
           MAX(100.0 * fr.shelter_occupancy / NULLIF(fr.shelter_capacity, 0)) AS peak_occupancy_pct
    FROM fact_resource_deployment fr
    JOIN dim_location dl ON fr.location_key = dl.location_key
    WHERE fr.shelter_occupancy IS NOT NULL
    GROUP BY dl.district
),
vulnerability AS (
    SELECT district, vulnerability_index
    FROM dim_location
    WHERE is_current = TRUE
),
combined AS (
    SELECT
        i.district, i.division,
        i.total_deaths, i.total_displaced, i.total_economic_loss,
        COALESCE(a.total_aid_delivered, 0) AS total_aid_delivered,
        COALESCE(s.peak_occupancy_pct, 0) AS peak_occupancy_pct,
        v.vulnerability_index,
        -- impact magnitude: deaths weighted heavily, displaced + loss contribute
        (i.total_deaths * 1000.0 + i.total_displaced + i.total_economic_loss / 1000.0) AS impact_raw,
        -- aid gap: impact per unit of aid received (higher = more underserved); avoid divide-by-zero
        (i.total_deaths * 1000.0 + i.total_displaced + i.total_economic_loss / 1000.0)
            / NULLIF(COALESCE(a.total_aid_delivered, 0), 0.01) AS aid_gap_raw
    FROM impact i
    LEFT JOIN aid a ON i.district = a.district
    LEFT JOIN shelter s ON i.district = s.district
    LEFT JOIN vulnerability v ON i.district = v.district
)
SELECT
    district, division,
    total_deaths, total_displaced, ROUND(total_economic_loss, 0) AS total_economic_loss,
    ROUND(total_aid_delivered, 0) AS total_aid_delivered,
    ROUND(peak_occupancy_pct, 1) AS peak_occupancy_pct,
    vulnerability_index,
    -- min-max normalize each raw factor to 0-1 across all rows
    ROUND((impact_raw - MIN(impact_raw) OVER ()) /
          NULLIF(MAX(impact_raw) OVER () - MIN(impact_raw) OVER (), 0), 3) AS impact_score,
    ROUND((aid_gap_raw - MIN(aid_gap_raw) OVER ()) /
          NULLIF(MAX(aid_gap_raw) OVER () - MIN(aid_gap_raw) OVER (), 0), 3) AS aid_gap_score,
    ROUND(peak_occupancy_pct / 100.0, 3) AS shelter_risk_score,  -- >1.0 means over capacity
    ROUND(vulnerability_index / 10.0, 3) AS vulnerability_score
FROM combined
ORDER BY impact_raw DESC;

-- Preview
SELECT * FROM dw.vw_dss_district_factors;
