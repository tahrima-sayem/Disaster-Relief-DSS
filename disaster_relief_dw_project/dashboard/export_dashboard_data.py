import psycopg2
import psycopg2.extras
import json

conn = psycopg2.connect(host="localhost", dbname="disaster_relief_dw", user="postgres", password="postgres")
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("SET search_path TO dw")

def q(sql):
    cur.execute(sql)
    return [dict(r) for r in cur.fetchall()]

data = {}

data["by_disaster_type"] = q("""
    SELECT de.disaster_type, COUNT(DISTINCT de.disaster_key) AS num_events,
           SUM(fi.deaths) AS deaths, SUM(fi.displaced) AS displaced
    FROM fact_disaster_impact fi JOIN dim_disaster_event de ON fi.disaster_key = de.disaster_key
    GROUP BY de.disaster_type ORDER BY num_events DESC
""")

data["yearly_trend"] = q("""
    SELECT dt.year, SUM(fi.deaths) AS deaths, SUM(fi.displaced) AS displaced,
           ROUND(SUM(fi.economic_loss_bdt)/1e6, 1) AS loss_million_bdt
    FROM fact_disaster_impact fi JOIN dim_time dt ON fi.time_key = dt.time_key
    GROUP BY dt.year ORDER BY dt.year
""")

data["top_districts_loss"] = q("""
    SELECT dl.district, ROUND(SUM(fi.economic_loss_bdt)/1e6, 1) AS loss_million_bdt
    FROM fact_disaster_impact fi JOIN dim_location dl ON fi.location_key = dl.location_key
    GROUP BY dl.district ORDER BY loss_million_bdt DESC LIMIT 8
""")

data["aid_by_org"] = q("""
    SELECT o.org_name, ROUND(SUM(fa.delivery_cost_bdt)/1e6, 2) AS cost_million_bdt
    FROM fact_aid_distribution fa JOIN dim_organization o ON fa.organization_key = o.organization_key
    GROUP BY o.org_name ORDER BY cost_million_bdt DESC
""")

data["resource_distribution"] = q("""
    SELECT rt.category, COUNT(*) AS num_deliveries
    FROM fact_aid_distribution fa JOIN dim_resource_type rt ON fa.resource_type_key = rt.resource_type_key
    GROUP BY rt.category ORDER BY num_deliveries DESC
""")

data["shelter_overcapacity"] = q("""
    SELECT s.shelter_name || ' (' || dl.district || ')' AS shelter, s.capacity,
           MAX(fr.shelter_occupancy) AS peak_occupancy,
           ROUND(100.0 * MAX(fr.shelter_occupancy) / s.capacity, 0) AS pct
    FROM fact_resource_deployment fr
    JOIN dim_shelter s ON fr.shelter_key = s.shelter_key
    JOIN dim_location dl ON s.location_key = dl.location_key
    WHERE fr.shelter_occupancy IS NOT NULL
    GROUP BY s.shelter_name, dl.district, s.capacity
    ORDER BY pct DESC LIMIT 8
""")

data["donations_by_event"] = q("""
    SELECT de.event_name, ROUND(SUM(fd.donation_amount_bdt)/1e6, 2) AS cash_million_bdt,
           ROUND(SUM(fd.in_kind_value_bdt)/1e6, 2) AS in_kind_million_bdt
    FROM fact_donations fd JOIN dim_disaster_event de ON fd.disaster_key = de.disaster_key
    GROUP BY de.event_name ORDER BY cash_million_bdt DESC
""")

data["summary"] = q("""
    SELECT
        (SELECT COUNT(*) FROM dim_disaster_event) AS total_events,
        (SELECT SUM(deaths) FROM fact_disaster_impact) AS total_deaths,
        (SELECT SUM(displaced) FROM fact_disaster_impact) AS total_displaced,
        (SELECT ROUND(SUM(economic_loss_bdt)/1e9, 2) FROM fact_disaster_impact) AS total_loss_billion_bdt,
        (SELECT ROUND(SUM(delivery_cost_bdt)/1e6, 1) FROM fact_aid_distribution) AS total_aid_cost_million_bdt,
        (SELECT COUNT(*) FROM dim_shelter) AS total_shelters
""")[0]

with open("dashboard_data.json", "w") as f:
    json.dump(data, f, indent=2, default=str)

print("Exported dashboard_data.json")
for k, v in data.items():
    print(f"  {k}: {len(v) if isinstance(v, list) else 1} rows")
