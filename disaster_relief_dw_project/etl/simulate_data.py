"""
Disaster Relief Data Warehouse — Data Simulation Script
=========================================================
Generates CSV files for all dimension and fact tables.

Grounding strategy (see project proposal, Section 6.1):
  - dim_location: REAL Bangladesh divisions & districts (official administrative units)
  - dim_disaster_event: REAL historical Bangladesh disasters (name, type, real dates)
  - fact_* tables: SIMULATED operational figures (deaths/aid/deployment/donations),
    since granular day-by-day operational data of this kind is not publicly available.
    Magnitudes are calibrated to be roughly plausible relative to each event's real,
    publicly reported severity, but exact figures are NOT actual reported statistics.
"""

import csv
import random
import numpy as np
from datetime import date, timedelta
from faker import Faker

random.seed(42)
np.random.seed(42)
fake = Faker()
Faker.seed(42)

OUT = "data"

# ------------------------------------------------------------------
# 1. dim_location — real Bangladesh divisions & districts
# ------------------------------------------------------------------
# A representative subset of districts per division (real names), with
# approximate real coordinates and 2022 census-order-of-magnitude population.
DIVISIONS = {
    "Barisal":   [("Barisal", 22.7010, 90.3535, 2350000), ("Bhola", 22.6900, 90.6500, 1900000),
                  ("Patuakhali", 22.3596, 90.3298, 1600000)],
    "Chattogram":[("Chattogram", 22.3569, 91.7832, 7600000), ("Cox's Bazar", 21.4272, 92.0058, 2400000),
                  ("Cumilla", 23.4607, 91.1809, 6000000), ("Feni", 23.0159, 91.3976, 1500000),
                  ("Noakhali", 22.8696, 91.0995, 3200000)],
    "Dhaka":     [("Dhaka", 23.8103, 90.4125, 12000000), ("Gazipur", 23.9999, 90.4203, 5000000),
                  ("Narayanganj", 23.6238, 90.5000, 3500000), ("Tangail", 24.2513, 89.9167, 4200000)],
    "Khulna":    [("Khulna", 22.8456, 89.5403, 2400000), ("Satkhira", 22.7185, 89.0705, 2100000),
                  ("Bagerhat", 22.6602, 89.7895, 1600000)],
    "Mymensingh":[("Mymensingh", 24.7471, 90.4203, 5600000), ("Jamalpur", 24.9375, 89.9372, 2400000)],
    "Rajshahi":  [("Rajshahi", 24.3745, 88.6042, 2600000), ("Bogura", 24.8465, 89.3776, 3600000),
                  ("Pabna", 24.0064, 89.2372, 2600000)],
    "Rangpur":   [("Rangpur", 25.7439, 89.2752, 3200000), ("Kurigram", 25.8054, 89.6362, 2200000),
                  ("Lalmonirhat", 25.9923, 89.2847, 1300000)],
    "Sylhet":    [("Sylhet", 24.8949, 91.8687, 3800000), ("Sunamganj", 25.0658, 91.3950, 2700000),
                  ("Habiganj", 24.3745, 91.4156, 2200000), ("Moulvibazar", 24.4829, 91.7774, 2100000)],
}

location_rows = []
location_key = 1
district_to_key = {}
for division, districts in DIVISIONS.items():
    for (district, lat, lon, pop) in districts:
        vulnerability = round(np.random.uniform(4.0, 9.5), 2)
        # Give each district ONE SCD Type-2 change: a population update partway through the timeline
        location_rows.append({
            "location_key": location_key, "district": district, "division": division,
            "latitude": lat, "longitude": lon, "population": int(pop * 0.94),
            "vulnerability_index": vulnerability,
            "valid_from": "2007-01-01", "valid_to": "2021-12-31", "is_current": False
        })
        location_key += 1
        location_rows.append({
            "location_key": location_key, "district": district, "division": division,
            "latitude": lat, "longitude": lon, "population": pop,
            "vulnerability_index": vulnerability,
            "valid_from": "2022-01-01", "valid_to": None, "is_current": True
        })
        district_to_key[district] = location_key  # current version key
        location_key += 1

# ------------------------------------------------------------------
# 2. dim_disaster_event — REAL Bangladesh disasters (verified names/dates)
# ------------------------------------------------------------------
disasters = [
    {"event_name": "Cyclone Sidr", "disaster_type": "Cyclone", "severity": "Catastrophic",
     "start_date": "2007-11-15", "end_date": "2007-11-16",
     "districts": ["Barisal", "Bhola", "Patuakhali", "Bagerhat"]},
    {"event_name": "Cyclone Aila", "disaster_type": "Cyclone", "severity": "High",
     "start_date": "2009-05-25", "end_date": "2009-05-26",
     "districts": ["Satkhira", "Khulna", "Bagerhat"]},
    {"event_name": "2017 Sunamganj Flash Flood", "disaster_type": "Flood", "severity": "High",
     "start_date": "2017-04-01", "end_date": "2017-04-20",
     "districts": ["Sunamganj", "Habiganj", "Sylhet"]},
    {"event_name": "2020 South Asian Floods (Bangladesh)", "disaster_type": "Flood", "severity": "Catastrophic",
     "start_date": "2020-07-01", "end_date": "2020-08-15",
     "districts": ["Jamalpur", "Kurigram", "Lalmonirhat", "Tangail", "Bogura"]},
    {"event_name": "Cyclone Amphan", "disaster_type": "Cyclone", "severity": "High",
     "start_date": "2020-05-20", "end_date": "2020-05-21",
     "districts": ["Khulna", "Satkhira", "Bagerhat"]},
    {"event_name": "2022 Sylhet-Sunamganj Flood", "disaster_type": "Flood", "severity": "Catastrophic",
     "start_date": "2022-05-15", "end_date": "2022-06-30",
     "districts": ["Sylhet", "Sunamganj", "Moulvibazar", "Habiganj"]},
    {"event_name": "Cyclone Mocha", "disaster_type": "Cyclone", "severity": "Medium",
     "start_date": "2023-05-14", "end_date": "2023-05-15",
     "districts": ["Cox's Bazar", "Chattogram"]},
    {"event_name": "August 2024 Bangladesh Floods", "disaster_type": "Flood", "severity": "Catastrophic",
     "start_date": "2024-08-21", "end_date": "2024-09-10",
     "districts": ["Feni", "Cumilla", "Noakhali", "Chattogram"]},
]
for i, d in enumerate(disasters, start=1):
    d["disaster_key"] = i

# ------------------------------------------------------------------
# 3. dim_organization
# ------------------------------------------------------------------
organizations = [
    {"organization_key": 1, "org_name": "Department of Disaster Management (DDM)", "org_type": "Government", "country_of_origin": "Bangladesh"},
    {"organization_key": 2, "org_name": "Bangladesh Red Crescent Society", "org_type": "NGO", "country_of_origin": "Bangladesh"},
    {"organization_key": 3, "org_name": "BRAC", "org_type": "NGO", "country_of_origin": "Bangladesh"},
    {"organization_key": 4, "org_name": "World Food Programme", "org_type": "International", "country_of_origin": "International"},
    {"organization_key": 5, "org_name": "UNICEF Bangladesh", "org_type": "International", "country_of_origin": "International"},
    {"organization_key": 6, "org_name": "Bangladesh Armed Forces (Relief Wing)", "org_type": "Military", "country_of_origin": "Bangladesh"},
    {"organization_key": 7, "org_name": "Cyclone Preparedness Programme (CPP)", "org_type": "Government", "country_of_origin": "Bangladesh"},
]

# ------------------------------------------------------------------
# 4. dim_resource_type
# ------------------------------------------------------------------
resource_types = [
    {"resource_type_key": 1, "category": "Food", "unit_of_measure": "kg"},
    {"resource_type_key": 2, "category": "Drinking Water", "unit_of_measure": "litre"},
    {"resource_type_key": 3, "category": "Medicine", "unit_of_measure": "packet"},
    {"resource_type_key": 4, "category": "Blanket", "unit_of_measure": "unit"},
    {"resource_type_key": 5, "category": "Tent", "unit_of_measure": "unit"},
    {"resource_type_key": 6, "category": "Cash Assistance", "unit_of_measure": "BDT"},
]

# ------------------------------------------------------------------
# 5. dim_donor
# ------------------------------------------------------------------
donor_rows = []
donor_key = 1
for donor_type, countries in [
    ("Individual", ["Bangladesh", "UK", "USA", "UAE"]),
    ("Corporate", ["Bangladesh", "Japan", "Singapore"]),
    ("Government", ["Bangladesh", "India", "Japan", "USA"]),
    ("International", ["International"]),
]:
    for country in countries:
        donor_rows.append({"donor_key": donor_key, "donor_type": donor_type, "country": country})
        donor_key += 1

# ------------------------------------------------------------------
# 6. dim_shelter — a handful of shelters per disaster-affected district
# ------------------------------------------------------------------
shelter_rows = []
shelter_key = 1
FACILITY_TYPES = ["Cyclone Shelter", "Primary School", "Community Hall", "Flood Shelter"]
affected_districts = sorted(set(dd for d in disasters for dd in d["districts"]))
for district in affected_districts:
    loc_key = district_to_key[district]
    n_shelters = random.randint(2, 4)
    for i in range(n_shelters):
        shelter_rows.append({
            "shelter_key": shelter_key,
            "shelter_name": f"{district} {FACILITY_TYPES[i % len(FACILITY_TYPES)]} #{i+1}",
            "facility_type": FACILITY_TYPES[i % len(FACILITY_TYPES)],
            "location_key": loc_key,
            "capacity": random.choice([150, 200, 300, 500, 750, 1000])
        })
        shelter_key += 1

# ------------------------------------------------------------------
# 7. dim_time — daily grain, 2015-01-01 to 2026-07-22
# ------------------------------------------------------------------
start, end = date(2007, 1, 1), date(2026, 7, 22)
time_rows = []
d = start
while d <= end:
    time_rows.append({
        "time_key": int(d.strftime("%Y%m%d")), "full_date": d.isoformat(),
        "day": d.day, "month": d.month, "month_name": d.strftime("%B"),
        "quarter": (d.month - 1) // 3 + 1, "year": d.year,
        "is_monsoon_season": d.month in (6, 7, 8, 9, 10)
    })
    d += timedelta(days=1)

# ------------------------------------------------------------------
# 8. FACT TABLES — simulated, calibrated to each event's real severity tier
# ------------------------------------------------------------------
SEVERITY_SCALE = {"Low": 0.3, "Medium": 0.6, "High": 1.0, "Catastrophic": 2.2}

impact_rows, aid_rows, deploy_rows, donation_rows = [], [], [], []
impact_key = aid_key = deploy_key = donation_key = 1

for dis in disasters:
    scale = SEVERITY_SCALE[dis["severity"]]
    sd = date.fromisoformat(dis["start_date"])
    ed = date.fromisoformat(dis["end_date"]) if dis["end_date"] else sd
    n_days = max((ed - sd).days + 1, 1)
    relief_end = ed + timedelta(days=random.randint(14, 30))  # relief ops continue past the event

    for district in dis["districts"]:
        loc_key = district_to_key[district]

        # ---- fact_disaster_impact: one row per day of the event ----
        for day_offset in range(n_days):
            day = sd + timedelta(days=day_offset)
            time_key = int(day.strftime("%Y%m%d"))
            severity_decay = max(1 - day_offset / max(n_days, 1), 0.15)  # impact front-loaded
            impact_rows.append({
                "fact_key": impact_key, "time_key": time_key, "location_key": loc_key,
                "disaster_key": dis["disaster_key"],
                "deaths": int(np.random.poisson(3 * scale * severity_decay)),
                "injured": int(np.random.poisson(15 * scale * severity_decay)),
                "displaced": int(np.random.gamma(2, 2000 * scale * severity_decay)),
                "houses_damaged": int(np.random.gamma(2, 400 * scale * severity_decay)),
                "economic_loss_bdt": round(np.random.gamma(2, 8_000_000 * scale * severity_decay), 2)
            })
            impact_key += 1

        # ---- fact_aid_distribution: daily, across orgs & resources, through relief period ----
        rel_days = (relief_end - sd).days + 1
        for day_offset in range(0, rel_days, 2):  # every other day
            day = sd + timedelta(days=day_offset)
            time_key = int(day.strftime("%Y%m%d"))
            decay = max(1 - day_offset / rel_days, 0.2)
            for org in random.sample(organizations, k=random.randint(2, 4)):
                for res in random.sample(resource_types, k=random.randint(1, 3)):
                    qty = round(np.random.gamma(2, 500 * scale * decay), 1)
                    aid_rows.append({
                        "fact_key": aid_key, "time_key": time_key, "location_key": loc_key,
                        "organization_key": org["organization_key"],
                        "resource_type_key": res["resource_type_key"],
                        "disaster_key": dis["disaster_key"],
                        "quantity_delivered": qty,
                        "beneficiaries_reached": int(qty * np.random.uniform(0.8, 1.5)),
                        "delivery_cost_bdt": round(qty * np.random.uniform(15, 60), 2)
                    })
                    aid_key += 1

        # ---- fact_resource_deployment: daily, with shelter linkage where applicable ----
        district_shelters = [s for s in shelter_rows if s["location_key"] == loc_key]
        for day_offset in range(0, rel_days, 3):
            day = sd + timedelta(days=day_offset)
            time_key = int(day.strftime("%Y%m%d"))
            decay = max(1 - day_offset / rel_days, 0.2)
            for org in random.sample(organizations, k=random.randint(1, 3)):
                shelter = random.choice(district_shelters) if district_shelters and random.random() < 0.6 else None
                occ = None
                cap = None
                if shelter:
                    cap = shelter["capacity"]
                    occ = int(cap * np.random.uniform(0.4, 1.3) * decay)  # can exceed capacity (overcrowding)
                deploy_rows.append({
                    "fact_key": deploy_key, "time_key": time_key, "location_key": loc_key,
                    "organization_key": org["organization_key"], "disaster_key": dis["disaster_key"],
                    "shelter_key": shelter["shelter_key"] if shelter else None,
                    "personnel_deployed": int(np.random.gamma(2, 20 * scale * decay)),
                    "vehicles_deployed": int(np.random.gamma(2, 3 * scale * decay)),
                    "shelter_capacity": cap, "shelter_occupancy": occ
                })
                deploy_key += 1

    # ---- fact_donations: transactions over the relief period, not district-specific ----
    n_donations = int(60 * scale)
    for _ in range(n_donations):
        day_offset = int(np.random.triangular(0, 5, rel_days))
        day = sd + timedelta(days=min(day_offset, rel_days))
        time_key = int(day.strftime("%Y%m%d"))
        donor = random.choice(donor_rows)
        org = random.choice(organizations)
        is_cash = random.random() < 0.7
        amount = round(np.random.gamma(2, 50_000 * scale), 2) if is_cash else 0
        in_kind = 0 if is_cash else round(np.random.gamma(2, 80_000 * scale), 2)
        donation_rows.append({
            "fact_key": donation_key, "time_key": time_key, "donor_key": donor["donor_key"],
            "disaster_key": dis["disaster_key"], "organization_key": org["organization_key"],
            "donation_amount_bdt": amount, "in_kind_value_bdt": in_kind
        })
        donation_key += 1

# ------------------------------------------------------------------
# WRITE ALL CSVs
# ------------------------------------------------------------------
def write_csv(filename, rows, fieldnames):
    path = f"{OUT}/{filename}"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {filename}: {len(rows)} rows")

print("Writing CSV files to", OUT)
write_csv("dim_time.csv", time_rows, list(time_rows[0].keys()))
write_csv("dim_location.csv", location_rows, list(location_rows[0].keys()))
write_csv("dim_disaster_event.csv",
          [{k: v for k, v in d.items() if k != "districts"} | {"is_real_event": True} for d in disasters],
          ["disaster_key", "event_name", "disaster_type", "severity", "start_date", "end_date", "is_real_event"])
write_csv("dim_organization.csv", organizations, list(organizations[0].keys()))
write_csv("dim_resource_type.csv", resource_types, list(resource_types[0].keys()))
write_csv("dim_donor.csv", donor_rows, list(donor_rows[0].keys()))
write_csv("dim_shelter.csv", shelter_rows, list(shelter_rows[0].keys()))
write_csv("fact_disaster_impact.csv", impact_rows, list(impact_rows[0].keys()))
write_csv("fact_aid_distribution.csv", aid_rows, list(aid_rows[0].keys()))
write_csv("fact_resource_deployment.csv", deploy_rows, list(deploy_rows[0].keys()))
write_csv("fact_donations.csv", donation_rows, list(donation_rows[0].keys()))
print("Done.")
