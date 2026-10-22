"""Telemetry writer for services/telemetry (ADR 8)."""
import os

import psycopg

DSN = os.environ.get("TELEMETRY_DSN", "postgresql://haulmark:placeholder@localhost:5432/haulmark_telemetry")

SCHEMA = """
CREATE TABLE IF NOT EXISTS positions (
    vehicle_id TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    location GEOGRAPHY(POINT) NOT NULL
);
SELECT create_hypertable('positions', 'recorded_at', if_not_exists => TRUE);
"""


def write_position(conn, vehicle_id: str, recorded_at, lon: float, lat: float):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO positions VALUES (%s, %s, ST_MakePoint(%s, %s)::geography)",
            (vehicle_id, recorded_at, lon, lat),
        )
