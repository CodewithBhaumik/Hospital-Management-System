import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "hospital.db")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # access columns by name: row['name']
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password):
    """SHA-256 hash — never store plain-text passwords."""
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    """Create tables and seed demo data on first run."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    # ── Create tables (3NF normalised schema) ────────────────────────────────
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS doctors (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT    NOT NULL,
            email          TEXT    UNIQUE NOT NULL,
            password       TEXT    NOT NULL,
            specialization TEXT    NOT NULL,
            phone          TEXT
        );

        CREATE TABLE IF NOT EXISTS patients (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            age         INTEGER,
            gender      TEXT,
            phone       TEXT,
            blood_group TEXT
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id  INTEGER NOT NULL,
            doctor_id   INTEGER NOT NULL,
            date        TEXT    NOT NULL,
            time_slot   TEXT    NOT NULL,
            reason      TEXT,
            status      TEXT    DEFAULT 'pending',
            notes       TEXT    DEFAULT '',
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id)  REFERENCES doctors(id)
        );

        CREATE TABLE IF NOT EXISTS test_reports (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id   INTEGER NOT NULL,
            doctor_id    INTEGER NOT NULL,
            test_name    TEXT    NOT NULL,
            result       TEXT    NOT NULL,
            normal_range TEXT,
            remarks      TEXT,
            date         TEXT    NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id)  REFERENCES doctors(id)
        );
    """)

    # ── Seed doctors ──────────────────────────────────────────────────────────
    doctors = [
        ("Dr. Arjun Mehta",  "arjun@hospital.com",  hash_password("doctor123"), "Cardiology",    "9876543210"),
        ("Dr. Priya Sharma", "priya@hospital.com",  hash_password("doctor123"), "Neurology",     "9876543211"),
        ("Dr. Ravi Kumar",   "ravi@hospital.com",   hash_password("doctor123"), "Orthopedics",   "9876543212"),
        ("Dr. Neha Gupta",   "neha@hospital.com",   hash_password("doctor123"), "Dermatology",   "9876543213"),
    ]
    for d in doctors:
        try:
            conn.execute(
                "INSERT INTO doctors (name,email,password,specialization,phone) VALUES (?,?,?,?,?)", d)
        except Exception:
            pass   # skip if already seeded

    # ── Seed patients ─────────────────────────────────────────────────────────
    patients = [
        ("Amit Singh",  "amit@gmail.com",  hash_password("patient123"), 22, "Male",   "9123456789", "O+"),
        ("Sneha Patel", "sneha@gmail.com", hash_password("patient123"), 28, "Female", "9123456790", "B+"),
    ]
    for p in patients:
        try:
            conn.execute(
                "INSERT INTO patients (name,email,password,age,gender,phone,blood_group) VALUES (?,?,?,?,?,?,?)", p)
        except Exception:
            pass

    # ── Seed appointments ─────────────────────────────────────────────────────
    appointments = [
        (1, 1, "2025-06-10", "10:00 AM", "Chest pain checkup",     "completed", "ECG done. Prescribed rest."),
        (2, 2, "2025-06-12", "11:30 AM", "Headache and dizziness", "pending",   ""),
        (1, 3, "2025-06-15", "02:00 PM", "Knee pain",              "pending",   ""),
        (2, 1, "2025-06-18", "09:00 AM", "Routine checkup",        "cancelled", "Patient cancelled."),
    ]
    for a in appointments:
        try:
            conn.execute(
                "INSERT INTO appointments (patient_id,doctor_id,date,time_slot,reason,status,notes) VALUES (?,?,?,?,?,?,?)", a)
        except Exception:
            pass

    # ── Seed test reports ─────────────────────────────────────────────────────
    reports = [
        (1, 1, "Complete Blood Count (CBC)", "Hemoglobin: 13.5 g/dL, WBC: 7200/uL", "Hb: 12-17 g/dL",   "All values within normal range.",      "2025-06-10"),
        (1, 1, "ECG",                        "Normal Sinus Rhythm, HR: 72 bpm",      "Normal",            "No cardiac abnormalities detected.",   "2025-06-10"),
        (2, 2, "MRI Brain",                  "No lesions or abnormalities",          "Clear",             "Mild tension headache. Rest advised.", "2025-06-12"),
        (2, 2, "Blood Pressure",             "120/80 mmHg",                          "90/60-120/80 mmHg", "Normal. No hypertension.",             "2025-06-12"),
    ]
    for r in reports:
        try:
            conn.execute(
                "INSERT INTO test_reports (patient_id,doctor_id,test_name,result,normal_range,remarks,date) VALUES (?,?,?,?,?,?,?)", r)
        except Exception:
            pass

    conn.commit()
    conn.close()
    print("=" * 55)
    print("  DB initialised with demo data")
    print("  Doctor login  : arjun@hospital.com  / doctor123")
    print("  Patient login : amit@gmail.com       / patient123")
    print("=" * 55)
