SET search_path TO dw;

-- ============================================================
-- 1. DISASTER ANALYSIS
-- ============================================================

-- 1.1 Which disaster type occurs most frequently, and what's the human toll?
SELECT de.disaster_type,
       COUNT(DISTINCT de.disaster_key) AS num_events,
       SUM(fi.deaths) AS total_deaths,
       SUM(fi.displaced) AS total_displaced
FROM fact_disaster_impact fi
JOIN dim_disaster_event de ON fi.disaster_key = de.disaster_key
GROUP BY de.disaster_type
ORDER BY num_events DESC;

-- 1.2 Which district is most disaster-prone (by cumulative economic loss)?
SELECT dl.district, dl.division,
       SUM(fi.economic_loss_bdt) AS total_economic_loss_bdt,
       SUM(fi.deaths) AS total_deaths
FROM fact_disaster_impact fi
JOIN dim_location dl ON fi.location_key = dl.location_key
GROUP BY dl.district, dl.division
ORDER BY total_economic_loss_bdt DESC
LIMIT 10;

-- 1.3 Yearly trend of disaster impact (ROLL-UP from day -> year)
SELECT dt.year,
       SUM(fi.deaths) AS total_deaths,
       SUM(fi.displaced) AS total_displaced,
       ROUND(SUM(fi.economic_loss_bdt) / 1e6, 2) AS total_loss_million_bdt
FROM fact_disaster_impact fi
JOIN dim_time dt ON fi.time_key = dt.time_key
GROUP BY dt.year
ORDER BY dt.year;

-- ============================================================
-- 2. RELIEF / AID ANALYSIS
-- ============================================================

-- 2.1 Which organization distributed the most food (by quantity)?
SELECT o.org_name,
       SUM(fa.quantity_delivered) AS total_food_kg
FROM fact_aid_distribution fa
JOIN dim_organization o ON fa.organization_key = o.organization_key
JOIN dim_resource_type rt ON fa.resource_type_key = rt.resource_type_key
WHERE rt.category = 'Food'
GROUP BY o.org_name
ORDER BY total_food_kg DESC;

-- 2.2 Which district received the highest total relief cost?
SELECT dl.district,
       ROUND(SUM(fa.delivery_cost_bdt), 2) AS total_relief_cost_bdt,
       SUM(fa.beneficiaries_reached) AS total_beneficiaries
FROM fact_aid_distribution fa
JOIN dim_location dl ON fa.location_key = dl.location_key
GROUP BY dl.district
ORDER BY total_relief_cost_bdt DESC
LIMIT 10;

-- 2.3 Most frequently distributed resource types
SELECT rt.category, COUNT(*) AS num_deliveries,
       ROUND(SUM(fa.quantity_delivered), 1) AS total_quantity
FROM fact_aid_distribution fa
JOIN dim_resource_type rt ON fa.resource_type_key = rt.resource_type_key
GROUP BY rt.category
ORDER BY num_deliveries DESC;

-- ============================================================
-- 3. SHELTER ANALYSIS
-- ============================================================

-- 3.1 Which shelters exceeded capacity (overcrowding), and by how much?
SELECT s.shelter_name, dl.district,
       MAX(fr.shelter_occupancy) AS peak_occupancy,
       s.capacity,
       ROUND(100.0 * MAX(fr.shelter_occupancy) / s.capacity, 1) AS peak_occupancy_pct
FROM fact_resource_deployment fr
JOIN dim_shelter s ON fr.shelter_key = s.shelter_key
JOIN dim_location dl ON s.location_key = dl.location_key
WHERE fr.shelter_occupancy IS NOT NULL
GROUP BY s.shelter_name, dl.district, s.capacity
HAVING MAX(fr.shelter_occupancy) > s.capacity
ORDER BY peak_occupancy_pct DESC;

-- 3.2 Average shelter occupancy rate by district
SELECT dl.district,
       ROUND(AVG(100.0 * fr.shelter_occupancy / fr.shelter_capacity), 1) AS avg_occupancy_pct
FROM fact_resource_deployment fr
JOIN dim_location dl ON fr.location_key = dl.location_key
WHERE fr.shelter_occupancy IS NOT NULL
GROUP BY dl.district
ORDER BY avg_occupancy_pct DESC;

-- ============================================================
-- 4. FINANCIAL ANALYSIS
-- ============================================================

-- 4.1 Total relief spending by year (aid delivery cost + donations)
SELECT dt.year,
       ROUND(SUM(fa.delivery_cost_bdt), 2) AS total_aid_cost_bdt
FROM fact_aid_distribution fa
JOIN dim_time dt ON fa.time_key = dt.time_key
GROUP BY dt.year
ORDER BY dt.year;

-- 4.2 Donation totals by disaster event
SELECT de.event_name,
       ROUND(SUM(fd.donation_amount_bdt), 2) AS total_cash_donations_bdt,
       ROUND(SUM(fd.in_kind_value_bdt), 2) AS total_in_kind_value_bdt
FROM fact_donations fd
JOIN dim_disaster_event de ON fd.disaster_key = de.disaster_key
GROUP BY de.event_name
ORDER BY total_cash_donations_bdt DESC;

-- 4.3 NGO expenditure comparison (aid delivery cost by organization)
SELECT o.org_name, o.org_type,
       ROUND(SUM(fa.delivery_cost_bdt), 2) AS total_expenditure_bdt
FROM fact_aid_distribution fa
JOIN dim_organization o ON fa.organization_key = o.organization_key
GROUP BY o.org_name, o.org_type
ORDER BY total_expenditure_bdt DESC;

-- ============================================================
-- 5. OLAP OPERATIONS DEMONSTRATED EXPLICITLY
-- ============================================================

-- 5.1 ROLL-UP: affected people by district -> division -> whole country
SELECT COALESCE(dl.division, 'ALL DIVISIONS') AS division,
       COALESCE(dl.district, 'ALL DISTRICTS') AS district,
       SUM(fi.displaced) AS total_displaced
FROM fact_disaster_impact fi
JOIN dim_location dl ON fi.location_key = dl.location_key
GROUP BY ROLLUP (dl.division, dl.district)
ORDER BY dl.division NULLS LAST, dl.district NULLS LAST;

-- 5.2 DRILL-DOWN: yearly totals down to month, for a single division (Sylhet)
SELECT dt.year, dt.month_name,
       SUM(fi.deaths) AS deaths, SUM(fi.displaced) AS displaced
FROM fact_disaster_impact fi
JOIN dim_time dt ON fi.time_key = dt.time_key
JOIN dim_location dl ON fi.location_key = dl.location_key
WHERE dl.division = 'Sylhet'
GROUP BY dt.year, dt.month, dt.month_name
ORDER BY dt.year, dt.month;

-- 5.3 SLICE: only Flood-type events
SELECT de.event_name, dl.district, fi.displaced, fi.economic_loss_bdt
FROM fact_disaster_impact fi
JOIN dim_disaster_event de ON fi.disaster_key = de.disaster_key
JOIN dim_location dl ON fi.location_key = dl.location_key
WHERE de.disaster_type = 'Flood'
ORDER BY fi.economic_loss_bdt DESC
LIMIT 15;

-- 5.4 DICE: Floods in Sylhet Division during 2022 only
SELECT de.event_name, dl.district, dt.full_date, fi.deaths, fi.displaced
FROM fact_disaster_impact fi
JOIN dim_disaster_event de ON fi.disaster_key = de.disaster_key
JOIN dim_location dl ON fi.location_key = dl.location_key
JOIN dim_time dt ON fi.time_key = dt.time_key
WHERE de.disaster_type = 'Flood'
  AND dl.division = 'Sylhet'
  AND dt.year = 2022
ORDER BY dt.full_date;

-- 5.5 PIVOT-style: organizations (rows) vs disaster types (columns), total aid cost
SELECT o.org_name,
       ROUND(SUM(fa.delivery_cost_bdt) FILTER (WHERE de.disaster_type = 'Flood'), 2) AS flood_cost_bdt,
       ROUND(SUM(fa.delivery_cost_bdt) FILTER (WHERE de.disaster_type = 'Cyclone'), 2) AS cyclone_cost_bdt
FROM fact_aid_distribution fa
JOIN dim_organization o ON fa.organization_key = o.organization_key
JOIN dim_disaster_event de ON fa.disaster_key = de.disaster_key
GROUP BY o.org_name
ORDER BY o.org_name;

-- ============================================================
-- 6. SLOWLY CHANGING DIMENSION DEMONSTRATION
-- ============================================================

-- 6.1 Show both historical versions of a district's population (Type 2 SCD)
SELECT district, population, vulnerability_index, valid_from, valid_to, is_current
FROM dim_location
WHERE district = 'Khulna'
ORDER BY valid_from;
