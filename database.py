import sqlite3

def init_db():
    conn = sqlite3.connect("hospital.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            heart_rate INTEGER,
            blood_pressure INTEGER,
            oxygen_saturation INTEGER,
            temperature REAL,
            consciousness TEXT,
            chest_pain INTEGER,
            sweating INTEGER,
            left_arm_pain INTEGER,
            bleeding TEXT,
            facial_drooping INTEGER,
            speech_slurred INTEGER,
            arm_weakness INTEGER,
            trauma INTEGER,
            has_allergy INTEGER,
            allergy_drug TEXT,
            icu_available INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diagnoses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            patient_status TEXT,
            alert_level TEXT,
            cardiac_event INTEGER,
            stroke_suspected INTEGER,
            recommend_ECG INTEGER,
            recommend_ICU INTEGER,
            emergency_transfer INTEGER,
            notify_senior_doctor INTEGER,
            notify_pediatric INTEGER,
            skip_triage INTEGER,
            tpa_blocked INTEGER,
            rules_fired TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    """)

    conn.commit()
    conn.close()
    print("Database ready!")

def save_patient(d):
    conn = sqlite3.connect("hospital.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO patients (
            name, age, gender, heart_rate, blood_pressure,
            oxygen_saturation, temperature, consciousness,
            chest_pain, sweating, left_arm_pain, bleeding,
            facial_drooping, speech_slurred, arm_weakness,
            trauma, has_allergy, allergy_drug, icu_available
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        d["name"], d["age"], d["gender"],
        d["heart_rate"], d["blood_pressure"],
        d["oxygen_saturation"], d["temperature"],
        d["consciousness"], d["chest_pain"],
        d["sweating"], d["left_arm_pain"],
        d["bleeding"], d["facial_drooping"],
        d["speech_slurred"], d["arm_weakness"],
        d["trauma"], d["has_allergy"],
        d["allergy_drug"], d["icu_available"]
    ))
    patient_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return patient_id

def save_diagnosis(patient_id, facts, rules_fired):
    conn = sqlite3.connect("hospital.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO diagnoses (
            patient_id, patient_status, alert_level,
            cardiac_event, stroke_suspected,
            recommend_ECG, recommend_ICU, emergency_transfer,
            notify_senior_doctor, notify_pediatric,
            skip_triage, tpa_blocked, rules_fired
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        patient_id,
        facts.get("patient_status", "stable"),
        facts.get("alert_level", "GREEN"),
        1 if facts.get("cardiac_event_suspected") else 0,
        1 if facts.get("stroke_suspected") else 0,
        1 if facts.get("recommend_ECG") else 0,
        1 if facts.get("recommend_ICU") else 0,
        1 if facts.get("emergency_transfer") else 0,
        1 if facts.get("notify_senior_doctor") else 0,
        1 if facts.get("notify_pediatric") else 0,
        1 if facts.get("skip_triage") else 0,
        1 if facts.get("tPA_blocked") else 0,
        ", ".join(rules_fired)
    ))
    conn.commit()
    conn.close()

def get_all_patients():
    conn = sqlite3.connect("hospital.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, d.patient_status, d.alert_level,
               d.cardiac_event, d.stroke_suspected,
               d.recommend_ECG, d.recommend_ICU,
               d.notify_senior_doctor, d.notify_pediatric,
               d.skip_triage, d.rules_fired,
               d.emergency_transfer, d.tpa_blocked
        FROM patients p
        LEFT JOIN diagnoses d ON p.id = d.patient_id
        ORDER BY p.timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
