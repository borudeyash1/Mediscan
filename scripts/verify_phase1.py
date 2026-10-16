"""
MediScan Enterprise — Verification Gate 1 Audit Script
======================================================
Strict verification of:
  1. PostgreSQL 16: Core clinical tables, RLS active, and AES-256-GCM envelope encryption round-trip
  2. TimescaleDB: patient_vital_telemetry hypertable & vital_telemetry_5m_rollup continuous aggregate
  3. Neo4j: >= 30 Disease, >= 100 Symptom, >= 60 Medication nodes, active DDI & Contraindication edges
  4. Qdrant: clinical_evidence_rag collection with 768-dim vectors and >= 20 clinical guideline chunks
"""

import sys
import os
import psycopg2
from neo4j import GraphDatabase
from qdrant_client import QdrantClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def test_postgresql():
    print("\n[1/4] AUDITING POSTGRESQL 16 (Clinical Store)...")
    conn = psycopg2.connect(
        host=os.getenv("MEDISCAN_PG_CLINICAL_HOST", "localhost"),
        port=int(os.getenv("MEDISCAN_PG_CLINICAL_PORT", "5432")),
        dbname=os.getenv("MEDISCAN_PG_CLINICAL_DB", "mediscan_clinical"),
        user=os.getenv("MEDISCAN_PG_CLINICAL_USER", "mediscan_admin"),
        password=os.getenv("MEDISCAN_PG_CLINICAL_PASSWORD", "mediscan_dev_2026"),
    )
    cur = conn.cursor()

    # 1. Check tables exist
    required_tables = [
        "tenants",
        "patient_identity_vault",
        "clinical_encounters",
        "ai_diagnostic_inferences",
        "immutable_audit_ledger",
    ]
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public';
    """)
    existing_tables = {row[0] for row in cur.fetchall()}
    for table in required_tables:
        assert table in existing_tables, f"Missing PostgreSQL table: {table}"
        print(f"  ✓ Table '{table}' verified")

    # 2. Assert Row-Level Security (RLS) is active on clinical_encounters
    cur.execute("""
        SELECT relrowsecurity 
        FROM pg_class 
        WHERE relname = 'clinical_encounters';
    """)
    row = cur.fetchone()
    assert row and row[0] is True, "RLS is NOT active on clinical_encounters table!"
    print("  ✓ Row-Level Security (RLS) active on clinical_encounters")

    # 3. Assert AES-256-GCM encrypt/decrypt round-trip via envelope functions
    test_secret = "Confidential Patient PII: DOB 1980-05-12, SSN 000-12-3456"
    cur.execute("""
        SELECT generate_dek() as dek;
    """)
    dek = cur.fetchone()[0]

    cur.execute("""
        SELECT decrypt_pii_envelope(encrypt_pii_envelope(%s, %s), %s);
    """, (test_secret, dek, dek))
    decrypted = cur.fetchone()[0]
    assert decrypted == test_secret, f"Encryption round-trip mismatch: got {decrypted}"
    print("  ✓ AES-256-GCM envelope encrypt/decrypt round-trip succeeded")

    cur.close()
    conn.close()
    print("  ✓ PostgreSQL 16 Audit: PASSED")


def test_timescaledb():
    print("\n[2/4] AUDITING TIMESCALEDB (Telemetry Store)...")
    conn = psycopg2.connect(
        host=os.getenv("MEDISCAN_TSDB_HOST", "localhost"),
        port=int(os.getenv("MEDISCAN_TSDB_PORT", "5433")),
        dbname=os.getenv("MEDISCAN_TSDB_DB", "mediscan_telemetry"),
        user=os.getenv("MEDISCAN_TSDB_USER", "mediscan_admin"),
        password=os.getenv("MEDISCAN_TSDB_PASSWORD", "mediscan_dev_2026"),
    )
    cur = conn.cursor()

    # 1. Check patient_vital_telemetry is a registered hypertable
    cur.execute("""
        SELECT hypertable_name 
        FROM timescaledb_information.hypertables 
        WHERE hypertable_name = 'patient_vital_telemetry';
    """)
    row = cur.fetchone()
    assert row and row[0] == "patient_vital_telemetry", "patient_vital_telemetry is NOT a registered TimescaleDB hypertable!"
    print("  ✓ Hypertable 'patient_vital_telemetry' registered")

    # 2. Check vital_telemetry_5m_rollup continuous aggregate view exists
    cur.execute("""
        SELECT view_name 
        FROM timescaledb_information.continuous_aggregates 
        WHERE view_name = 'vital_telemetry_5m_rollup';
    """)
    row = cur.fetchone()
    assert row and row[0] == "vital_telemetry_5m_rollup", "vital_telemetry_5m_rollup continuous aggregate NOT found!"
    print("  ✓ Continuous aggregate 'vital_telemetry_5m_rollup' verified")

    cur.close()
    conn.close()
    print("  ✓ TimescaleDB Audit: PASSED")


def test_neo4j():
    print("\n[3/4] AUDITING NEO4J KNOWLEDGE GRAPH...")
    uri = os.getenv("MEDISCAN_NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("MEDISCAN_NEO4J_USER", "neo4j")
    pwd = os.getenv("MEDISCAN_NEO4J_PASSWORD", "mediscan_dev_2026")

    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    with driver.session() as session:
        # Check node counts
        diseases = session.run("MATCH (n:Disease) RETURN count(n) AS cnt").single()["cnt"]
        symptoms = session.run("MATCH (n:Symptom) RETURN count(n) AS cnt").single()["cnt"]
        meds = session.run("MATCH (n:Medication) RETURN count(n) AS cnt").single()["cnt"]

        print(f"  ✓ Diseases: {diseases} (Assert >= 30)")
        assert diseases >= 30, f"Expected >= 30 Disease nodes, got {diseases}"

        print(f"  ✓ Symptoms: {symptoms} (Assert >= 100)")
        assert symptoms >= 100, f"Expected >= 100 Symptom nodes, got {symptoms}"

        print(f"  ✓ Medications: {meds} (Assert >= 60)")
        assert meds >= 60, f"Expected >= 60 Medication nodes, got {meds}"

        # Check relationships
        ddis = session.run("MATCH ()-[r:INTERACTS_WITH]->() RETURN count(r) AS cnt").single()["cnt"]
        contra = session.run("MATCH ()-[r:CONTRAINDICATED_IN]->() RETURN count(r) AS cnt").single()["cnt"]

        print(f"  ✓ Active DDI edges (:INTERACTS_WITH): {ddis} (Assert > 0)")
        assert ddis > 0, "No active :INTERACTS_WITH edges found!"

        print(f"  ✓ Active Contraindication edges (:CONTRAINDICATED_IN): {contra} (Assert > 0)")
        assert contra > 0, "No active :CONTRAINDICATED_IN edges found!"

    driver.close()
    print("  ✓ Neo4j Audit: PASSED")


def test_qdrant():
    print("\n[4/4] AUDITING QDRANT HYBRID RAG...")
    host = os.getenv("MEDISCAN_QDRANT_HOST", "localhost")
    port = int(os.getenv("MEDISCAN_QDRANT_PORT", "6333"))

    client = QdrantClient(host=host, port=port)
    collection_name = "clinical_evidence_rag"

    info = client.get_collection(collection_name=collection_name)
    assert info is not None, f"Collection '{collection_name}' not found!"
    print(f"  ✓ Collection '{collection_name}' exists")

    dim = info.config.params.vectors.size
    print(f"  ✓ Vector dimension: {dim} (Assert == 768)")
    assert dim == 768, f"Expected 768-dim vectors, got {dim}"

    count = info.points_count
    print(f"  ✓ Indexed clinical guideline chunks: {count} (Assert >= 20)")
    assert count >= 20, f"Expected >= 20 indexed chunks, got {count}"

    print("  ✓ Qdrant Audit: PASSED")


def main():
    print("============================================================")
    print("VERIFICATION GATE 1: INFRASTRUCTURE & POLYGLOT DATA AUDIT")
    print("============================================================")
    try:
        test_postgresql()
        test_timescaledb()
        test_neo4j()
        test_qdrant()
        print("\n" + "=" * 60)
        print("ALL VERIFICATION GATE 1 CHECKS PASSED (100% HEALTHY)")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n[FAIL] Assertion Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
