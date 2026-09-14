-- ============================================================
-- Disaster Relief Data Warehouse — Schema DDL
-- Dimensional model: fact constellation (galaxy schema)
-- Target: PostgreSQL 14+
-- ============================================================

DROP SCHEMA IF EXISTS dw CASCADE;
CREATE SCHEMA dw;
SET search_path TO dw;

-- ------------------------------------------------------------
-- DIMENSION TABLES
-- ------------------------------------------------------------

CREATE TABLE dim_time (
    time_key        INT PRIMARY KEY,          -- YYYYMMDD
    full_date       DATE NOT NULL UNIQUE,
    day             SMALLINT NOT NULL,
    month           SMALLINT NOT NULL,
    month_name      VARCHAR(20) NOT NULL,
    quarter         SMALLINT NOT NULL,
    year            SMALLINT NOT NULL,
    is_monsoon_season BOOLEAN NOT NULL        -- Jun-Oct: relevant for flood risk in Bangladesh
);

-- Type 2 Slowly Changing Dimension: tracks changes to population / vulnerability_index over time
CREATE TABLE dim_location (
    location_key    SERIAL PRIMARY KEY,
    district        VARCHAR(100) NOT NULL,
    division        VARCHAR(50) NOT NULL,
    latitude        NUMERIC(9,6),
    longitude       NUMERIC(9,6),
    population      INT,
    vulnerability_index NUMERIC(4,2),          -- 0.00 (low) - 10.00 (extreme)
    valid_from      DATE NOT NULL,
    valid_to        DATE,                      -- NULL = current version
    is_current      BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (district, valid_from)
);

CREATE TABLE dim_disaster_event (
    disaster_key    SERIAL PRIMARY KEY,
    event_name      VARCHAR(150) NOT NULL,
    disaster_type   VARCHAR(50) NOT NULL,      -- Flood, Cyclone, Landslide, Earthquake, Drought
    severity        VARCHAR(20) NOT NULL,      -- Low, Medium, High, Catastrophic
    start_date      DATE NOT NULL,
    end_date        DATE,
    is_real_event   BOOLEAN NOT NULL DEFAULT TRUE  -- flags whether the event itself is historically real
);

CREATE TABLE dim_organization (
    organization_key SERIAL PRIMARY KEY,
    org_name        VARCHAR(150) NOT NULL,
    org_type        VARCHAR(50) NOT NULL,      -- Government, NGO, International, Military
    country_of_origin VARCHAR(50)
);

CREATE TABLE dim_resource_type (
    resource_type_key SERIAL PRIMARY KEY,
    category        VARCHAR(50) NOT NULL,      -- Food, Water, Medicine, Blanket, Tent, Cash
    unit_of_measure VARCHAR(20) NOT NULL       -- kg, litre, packet, unit, BDT
);

CREATE TABLE dim_donor (
    donor_key       SERIAL PRIMARY KEY,
    donor_type      VARCHAR(30) NOT NULL,      -- Individual, Corporate, Government, International
    country         VARCHAR(50)
);

CREATE TABLE dim_shelter (
    shelter_key     SERIAL PRIMARY KEY,
    shelter_name    VARCHAR(150) NOT NULL,
    facility_type   VARCHAR(50) NOT NULL,      -- School, Cyclone Center, Community Hall, Tent Camp
    location_key    INT NOT NULL REFERENCES dim_location(location_key),
    capacity        INT NOT NULL
);

-- ------------------------------------------------------------
-- FACT TABLES
-- ------------------------------------------------------------

-- Grain: one row per disaster event, per affected district, per day
CREATE TABLE fact_disaster_impact (
    fact_key        BIGSERIAL PRIMARY KEY,
    time_key        INT NOT NULL REFERENCES dim_time(time_key),
    location_key    INT NOT NULL REFERENCES dim_location(location_key),
    disaster_key    INT NOT NULL REFERENCES dim_disaster_event(disaster_key),
    deaths          INT NOT NULL DEFAULT 0,
    injured         INT NOT NULL DEFAULT 0,
    displaced       INT NOT NULL DEFAULT 0,
    houses_damaged  INT NOT NULL DEFAULT 0,
    economic_loss_bdt NUMERIC(16,2) NOT NULL DEFAULT 0   -- Bangladeshi Taka
);

-- Grain: one row per organization, per resource type, per district, per day
CREATE TABLE fact_aid_distribution (
    fact_key        BIGSERIAL PRIMARY KEY,
    time_key        INT NOT NULL REFERENCES dim_time(time_key),
    location_key    INT NOT NULL REFERENCES dim_location(location_key),
    organization_key INT NOT NULL REFERENCES dim_organization(organization_key),
    resource_type_key INT NOT NULL REFERENCES dim_resource_type(resource_type_key),
    disaster_key    INT NOT NULL REFERENCES dim_disaster_event(disaster_key),
    quantity_delivered NUMERIC(14,2) NOT NULL DEFAULT 0,
    beneficiaries_reached INT NOT NULL DEFAULT 0,
    delivery_cost_bdt NUMERIC(14,2) NOT NULL DEFAULT 0
);

-- Grain: one row per organization, per district, per day (personnel/vehicles),
-- plus shelter capacity/occupancy where a shelter is associated
CREATE TABLE fact_resource_deployment (
    fact_key        BIGSERIAL PRIMARY KEY,
    time_key        INT NOT NULL REFERENCES dim_time(time_key),
    location_key    INT NOT NULL REFERENCES dim_location(location_key),
    organization_key INT NOT NULL REFERENCES dim_organization(organization_key),
    disaster_key    INT NOT NULL REFERENCES dim_disaster_event(disaster_key),
    shelter_key     INT REFERENCES dim_shelter(shelter_key),   -- nullable: not all deployments involve a shelter
    personnel_deployed INT NOT NULL DEFAULT 0,
    vehicles_deployed INT NOT NULL DEFAULT 0,
    shelter_capacity INT,
    shelter_occupancy INT
);

-- Grain: one row per donation transaction
CREATE TABLE fact_donations (
    fact_key        BIGSERIAL PRIMARY KEY,
    time_key        INT NOT NULL REFERENCES dim_time(time_key),
    donor_key       INT NOT NULL REFERENCES dim_donor(donor_key),
    disaster_key    INT NOT NULL REFERENCES dim_disaster_event(disaster_key),
    organization_key INT NOT NULL REFERENCES dim_organization(organization_key),
    donation_amount_bdt NUMERIC(14,2) NOT NULL DEFAULT 0,
    in_kind_value_bdt NUMERIC(14,2) NOT NULL DEFAULT 0
);

-- ------------------------------------------------------------
-- INDEXES for common analytical join/filter patterns
-- ------------------------------------------------------------
CREATE INDEX idx_impact_location ON fact_disaster_impact(location_key);
CREATE INDEX idx_impact_disaster ON fact_disaster_impact(disaster_key);
CREATE INDEX idx_impact_time ON fact_disaster_impact(time_key);

CREATE INDEX idx_aid_location ON fact_aid_distribution(location_key);
CREATE INDEX idx_aid_org ON fact_aid_distribution(organization_key);
CREATE INDEX idx_aid_resource ON fact_aid_distribution(resource_type_key);

CREATE INDEX idx_deploy_location ON fact_resource_deployment(location_key);
CREATE INDEX idx_deploy_shelter ON fact_resource_deployment(shelter_key);

CREATE INDEX idx_donation_donor ON fact_donations(donor_key);
CREATE INDEX idx_donation_disaster ON fact_donations(disaster_key);

CREATE INDEX idx_location_current ON dim_location(is_current) WHERE is_current = TRUE;
