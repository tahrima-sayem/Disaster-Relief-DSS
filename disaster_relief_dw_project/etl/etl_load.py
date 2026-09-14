"""
Disaster Relief Data Warehouse — ETL Load Script
==================================================
Loads simulated CSV data into PostgreSQL using efficient COPY.
Load order respects foreign key dependencies:
  dimensions first (dim_location -> dim_shelter needs it),
  then fact tables.
"""

import psycopg2
import os

DATA_DIR = "data"
CONN_PARAMS = dict(host="localhost", dbname="disaster_relief_dw", user="postgres", password="postgres")

# (table_name, csv_file, column_order)
LOAD_ORDER = [
    ("dw.dim_time", "dim_time.csv",
     "time_key, full_date, day, month, month_name, quarter, year, is_monsoon_season"),
    ("dw.dim_location", "dim_location.csv",
     "location_key, district, division, latitude, longitude, population, vulnerability_index, valid_from, valid_to, is_current"),
    ("dw.dim_disaster_event", "dim_disaster_event.csv",
     "disaster_key, event_name, disaster_type, severity, start_date, end_date, is_real_event"),
    ("dw.dim_organization", "dim_organization.csv",
     "organization_key, org_name, org_type, country_of_origin"),
    ("dw.dim_resource_type", "dim_resource_type.csv",
     "resource_type_key, category, unit_of_measure"),
    ("dw.dim_donor", "dim_donor.csv", "donor_key, donor_type, country"),
    ("dw.dim_shelter", "dim_shelter.csv",
     "shelter_key, shelter_name, facility_type, location_key, capacity"),
    ("dw.fact_disaster_impact", "fact_disaster_impact.csv",
     "fact_key, time_key, location_key, disaster_key, deaths, injured, displaced, houses_damaged, economic_loss_bdt"),
    ("dw.fact_aid_distribution", "fact_aid_distribution.csv",
     "fact_key, time_key, location_key, organization_key, resource_type_key, disaster_key, quantity_delivered, beneficiaries_reached, delivery_cost_bdt"),
    ("dw.fact_resource_deployment", "fact_resource_deployment.csv",
     "fact_key, time_key, location_key, organization_key, disaster_key, shelter_key, personnel_deployed, vehicles_deployed, shelter_capacity, shelter_occupancy"),
    ("dw.fact_donations", "fact_donations.csv",
     "fact_key, time_key, donor_key, disaster_key, organization_key, donation_amount_bdt, in_kind_value_bdt"),
]


def main():
    conn = psycopg2.connect(**CONN_PARAMS)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        for table, filename, columns in LOAD_ORDER:
            path = os.path.join(DATA_DIR, filename)
            with open(path, "r") as f:
                copy_sql = f"COPY {table} ({columns}) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')"
                cur.copy_expert(copy_sql, f)
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  Loaded {table:<32} {count:>6} rows")
        # Reset sequences so future inserts don't collide with loaded keys
        seq_fixes = [
            ("dw.dim_location_location_key_seq", "dw.dim_location", "location_key"),
            ("dw.dim_disaster_event_disaster_key_seq", "dw.dim_disaster_event", "disaster_key"),
            ("dw.dim_organization_organization_key_seq", "dw.dim_organization", "organization_key"),
            ("dw.dim_resource_type_resource_type_key_seq", "dw.dim_resource_type", "resource_type_key"),
            ("dw.dim_donor_donor_key_seq", "dw.dim_donor", "donor_key"),
            ("dw.dim_shelter_shelter_key_seq", "dw.dim_shelter", "shelter_key"),
            ("dw.fact_disaster_impact_fact_key_seq", "dw.fact_disaster_impact", "fact_key"),
            ("dw.fact_aid_distribution_fact_key_seq", "dw.fact_aid_distribution", "fact_key"),
            ("dw.fact_resource_deployment_fact_key_seq", "dw.fact_resource_deployment", "fact_key"),
            ("dw.fact_donations_fact_key_seq", "dw.fact_donations", "fact_key"),
        ]
        for seq, table, col in seq_fixes:
            cur.execute(f"SELECT setval('{seq}', (SELECT MAX({col}) FROM {table}))")
        conn.commit()
        print("ETL load complete — committed.")
    except Exception as e:
        conn.rollback()
        print("ETL FAILED, rolled back:", e)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
