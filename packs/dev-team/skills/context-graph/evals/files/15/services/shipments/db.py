"""Shipment persistence for services/shipments (ADR 2)."""
import os

import psycopg

DSN = os.environ.get("SHIPMENTS_DSN", "postgresql://haulmark:placeholder@localhost:5432/haulmark_core")


def connect():
    return psycopg.connect(DSN)


def get_shipment(conn, shipment_id: str):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, customer_id, status, custom_fields FROM shipments WHERE id = %s",
            (shipment_id,),
        )
        return cur.fetchone()


def mark_stop_delivered(conn, shipment_id: str, stop_id: str):
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("UPDATE stops SET status = 'delivered' WHERE id = %s", (stop_id,))
            cur.execute(
                "UPDATE shipments SET status = 'delivered' WHERE id = %s "
                "AND NOT EXISTS (SELECT 1 FROM stops WHERE shipment_id = %s AND status <> 'delivered')",
                (shipment_id, shipment_id),
            )
