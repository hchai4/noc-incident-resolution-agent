import os
import sqlite3
from typing import Optional, Dict, Any

DB_PATH = os.getenv("TELEMETRY_DB_PATH", "data/circuits_telemetry.db")


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Returns dict-like rows
    return conn


def initialize_telemetry_db():
    """
    Creates and seeds the enterprise client circuit telemetry database.
    """
    schema_sql = """
    DROP TABLE IF EXISTS circuits;
    CREATE TABLE circuits (
        circuit_id TEXT PRIMARY KEY,
        client_name TEXT NOT NULL,
        client_tier TEXT NOT NULL CHECK(client_tier IN ('Tier-1', 'Tier-2', 'Tier-3')),
        contracted_sla_hours INTEGER NOT NULL,
        origin_location TEXT NOT NULL,
        dest_location TEXT NOT NULL,
        contact_email TEXT NOT NULL,
        circuit_status TEXT DEFAULT 'UP'
    );
    """

    sample_circuits = [
        (
            "IEPL-9021-LAX-TYO",
            "Goldman & Sachs Trading",
            "Tier-1",
            4,
            "Equinix LA1 (Los Angeles)",
            "Equinix TY2 (Tokyo)",
            "noc-alerts@gs-trading.com",
            "UP"
        ),
        (
            "DIA-4410-SFO-JFK",
            "Stripe Cloud Platform",
            "Tier-1",
            2,
            "Digital Realty SFO",
            "Equinix NY4 (Secaucus)",
            "network-ops@stripe-infra.com",
            "UP"
        ),
        (
            "METRO-3301-ORD-CHI",
            "Midwest Logistics Corp",
            "Tier-2",
            6,
            "Coresite CHI1",
            "Coresite CHI2",
            "it-support@midwestlogistics.com",
            "UP"
        ),
        (
            "IPLC-8812-LON-FRA",
            "Acme Retail Wholesale",
            "Tier-3",
            8,
            "Telehouse London Docklands",
            "Interxion Frankfurt",
            "admin@acmeretail.eu",
            "UP"
        )
    ]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        cursor.executemany(
            """
            INSERT INTO circuits (
                circuit_id, client_name, client_tier, contracted_sla_hours,
                origin_location, dest_location, contact_email, circuit_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            sample_circuits
        )
        conn.commit()

    print(f"✅ Telemetry DB initialized with {len(sample_circuits)} enterprise circuits.")


def get_circuit_details(circuit_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches ground-truth circuit metadata by circuit_id.
    """
    query = "SELECT * FROM circuits WHERE circuit_id = ?;"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (circuit_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


if __name__ == "__main__":
    initialize_telemetry_db()
    
    # Test query
    test_id = "IEPL-9021-LAX-TYO"
    result = get_circuit_details(test_id)
    print(f"\n[Test Query Result for {test_id}]:")
    print(result)
    