import json
import sqlite3
from contextlib import closing


DATABASE = "hospital.db"


def connect():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, age INTEGER, gender TEXT,
                heart_rate INTEGER, blood_pressure INTEGER,
                oxygen_saturation INTEGER, temperature REAL,
                consciousness TEXT, chest_pain INTEGER, sweating INTEGER,
                left_arm_pain INTEGER, bleeding TEXT, facial_drooping INTEGER,
                speech_slurred INTEGER, arm_weakness INTEGER, trauma INTEGER,
                mechanism TEXT DEFAULT 'none', has_allergy INTEGER,
                allergy_drug TEXT, icu_available INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS diagnoses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL, patient_status TEXT, alert_level TEXT,
                rules_fired TEXT, facts_json TEXT, trace_json TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """)
        _add_missing_columns(conn, "patients", {"mechanism": "TEXT DEFAULT 'none'"})
        _add_missing_columns(conn, "diagnoses", {
            "facts_json": "TEXT DEFAULT '{}'", "trace_json": "TEXT DEFAULT '[]'"
        })


def _add_missing_columns(conn, table, columns):
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, definition in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def save_patient(data):
    columns = (
        "name", "age", "gender", "heart_rate", "blood_pressure", "oxygen_saturation",
        "temperature", "consciousness", "chest_pain", "sweating", "left_arm_pain",
        "bleeding", "facial_drooping", "speech_slurred", "arm_weakness", "trauma",
        "mechanism", "has_allergy", "allergy_drug", "icu_available"
    )
    values = [data[column] for column in columns]
    with closing(connect()) as conn, conn:
        cursor = conn.execute(
            f"INSERT INTO patients ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
            values,
        )
        return cursor.lastrowid


def save_diagnosis(patient_id, facts, rules_fired, trace):
    with closing(connect()) as conn, conn:
        conn.execute("""
            INSERT INTO diagnoses
                (patient_id, patient_status, alert_level, rules_fired, facts_json, trace_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            patient_id, facts["patient_status"], facts["alert_level"],
            ", ".join(rules_fired), json.dumps(facts), json.dumps(trace),
        ))


def get_all_patients(query=""):
    sql = """
        SELECT p.*, d.patient_status, d.alert_level, d.rules_fired,
               d.facts_json, d.trace_json
        FROM patients p
        LEFT JOIN diagnoses d ON d.id = (
            SELECT d2.id FROM diagnoses d2
            WHERE d2.patient_id = p.id ORDER BY d2.id DESC LIMIT 1
        )
    """
    params = []
    if query:
        sql += " WHERE p.name LIKE ? OR CAST(p.id AS TEXT) = ? OR d.patient_status LIKE ?"
        params = [f"%{query}%", query, f"%{query}%"]
    sql += " ORDER BY p.timestamp DESC, p.id DESC"

    with closing(connect()) as conn:
        rows = conn.execute(sql, params).fetchall()

    patients = []
    for row in rows:
        patient = dict(row)
        patient["facts"] = json.loads(patient.pop("facts_json") or "{}")
        patient["trace"] = json.loads(patient.pop("trace_json") or "[]")
        patients.append(patient)
    return patients


def get_patient(patient_id):
    sql = """
        SELECT p.*, d.patient_status, d.alert_level, d.rules_fired,
               d.facts_json, d.trace_json
        FROM patients p
        LEFT JOIN diagnoses d ON d.id = (
            SELECT d2.id FROM diagnoses d2
            WHERE d2.patient_id = p.id ORDER BY d2.id DESC LIMIT 1
        )
        WHERE p.id = ?
    """
    with closing(connect()) as conn:
        row = conn.execute(sql, (patient_id,)).fetchone()
    if row is None:
        return None
    patient = dict(row)
    patient["facts"] = json.loads(patient.pop("facts_json") or "{}")
    patient["trace"] = json.loads(patient.pop("trace_json") or "[]")
    return patient
