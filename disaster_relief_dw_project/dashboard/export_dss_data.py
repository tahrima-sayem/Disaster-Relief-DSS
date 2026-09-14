import psycopg2
import psycopg2.extras
import json

conn = psycopg2.connect(host="localhost", dbname="disaster_relief_dw", user="postgres", password="postgres")
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("SET search_path TO dw")
cur.execute("SELECT * FROM dw.vw_dss_district_factors")
rows = [dict(r) for r in cur.fetchall()]

with open("dss_data.json", "w") as f:
    json.dump(rows, f, indent=2, default=str)

print(f"Exported {len(rows)} districts to dss_data.json")
