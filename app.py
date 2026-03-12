from flask import (Flask, render_template, request,
                   redirect, url_for, session, flash, jsonify, g)
from database import init_db, get_db, hash_password
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hms_dev_secret_key"  


# open one DB connection per request, close it after 
@app.teardown_appcontext
def close_db(_):
    db = getattr(g, "_db", None)
    if db:
        db.close()

def db():
    if "_db" not in g:
        g._db = get_db()
    return g._db


# helper for clean routing 
def role_required(role):
    return session.get("role") == role


#  LANDING
@app.route("/")
def index():
    return render_template("index.html")


#  AUTH
@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    if role not in ("doctor", "patient"):
        return redirect(url_for("index"))

    if request.method == "POST":
        email    = request.form["email"].strip().lower()
        password = hash_password(request.form["password"])
        table    = "doctors" if role == "doctor" else "patients"

        user = db().execute(
            f"SELECT * FROM {table} WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()

        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["role"]    = role
            session["name"]    = user["name"]
            return redirect(url_for("doctor_dashboard" if role == "doctor" else "patient_dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("auth/login.html", role=role)


@app.route("/register/<role>", methods=["GET", "POST"])
def register(role):
    if role not in ("doctor", "patient"):
        return redirect(url_for("index"))

    if request.method == "POST":
        name     = request.form["name"].strip()
        email    = request.form["email"].strip().lower()
        password = hash_password(request.form["password"])

        try:
            if role == "doctor":
                db().execute(
                    "INSERT INTO doctors (name,email,password,specialization,phone) VALUES (?,?,?,?,?)",
                    (name, email, password,
                     request.form["specialization"], request.form["phone"])
                )
            else:
                db().execute(
                    "INSERT INTO patients (name,email,password,age,gender,phone,blood_group) VALUES (?,?,?,?,?,?,?)",
                    (name, email, password,
                     request.form["age"],   request.form["gender"],
                     request.form["phone"], request.form["blood_group"])
                )
            db().commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login", role=role))

        except Exception:
            flash("Email already registered.", "error")

    return render_template("auth/register.html", role=role)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


#  DOCTOR ROUTES
@app.route("/doctor/dashboard")
def doctor_dashboard():
    if not role_required("doctor"):
        return redirect(url_for("index"))

    appointments = db().execute("""
        SELECT a.*, p.name AS patient_name, p.age, p.gender, p.blood_group, p.phone
        FROM   appointments a
        JOIN   patients p ON a.patient_id = p.id
        WHERE  a.doctor_id = ?
        ORDER  BY a.date DESC
    """, (session["user_id"],)).fetchall()

    stats = {
        "total":     len(appointments),
        "pending":   sum(1 for a in appointments if a["status"] == "pending"),
        "completed": sum(1 for a in appointments if a["status"] == "completed"),
        "cancelled": sum(1 for a in appointments if a["status"] == "cancelled"),
    }
    return render_template("doctor/dashboard.html", appointments=appointments, stats=stats)


@app.route("/doctor/patients")
def doctor_patients():
    if not role_required("doctor"):
        return redirect(url_for("index"))

    q    = request.args.get("q", "").strip()
    like = f"%{q}%"

    if q:
        patients = db().execute("""
            SELECT DISTINCT p.*
            FROM   patients p
            JOIN   appointments a ON p.id = a.patient_id
            WHERE  a.doctor_id = ?
              AND  (p.name LIKE ? OR p.blood_group LIKE ? OR p.phone LIKE ?)
        """, (session["user_id"], like, like, like)).fetchall()
    else:
        patients = db().execute("""
            SELECT DISTINCT p.*
            FROM   patients p
            JOIN   appointments a ON p.id = a.patient_id
            WHERE  a.doctor_id = ?
        """, (session["user_id"],)).fetchall()

    return render_template("doctor/patients.html", patients=patients, query=q)


@app.route("/doctor/appointment/<int:appt_id>", methods=["POST"])
def update_appointment(appt_id):
    if not role_required("doctor"):
        return redirect(url_for("index"))

    db().execute(
        "UPDATE appointments SET status = ?, notes = ? WHERE id = ?",
        (request.form["status"], request.form.get("notes", ""), appt_id)
    )
    db().commit()
    flash("Appointment updated.", "success")
    return redirect(url_for("doctor_dashboard"))


@app.route("/doctor/add_report", methods=["GET", "POST"])
def add_report():
    if not role_required("doctor"):
        return redirect(url_for("index"))

    if request.method == "POST":
        db().execute("""
            INSERT INTO test_reports
                (patient_id, doctor_id, test_name, result, normal_range, remarks, date)
            VALUES (?,?,?,?,?,?,?)
        """, (
            request.form["patient_id"], session["user_id"],
            request.form["test_name"],  request.form["result"],
            request.form["normal_range"], request.form["remarks"],
            datetime.now().strftime("%Y-%m-%d")
        ))
        db().commit()
        flash("Test report added successfully.", "success")
        return redirect(url_for("doctor_dashboard"))

    patients = db().execute("""
        SELECT DISTINCT p.id, p.name
        FROM   patients p
        JOIN   appointments a ON p.id = a.patient_id
        WHERE  a.doctor_id = ?
        ORDER  BY p.name
    """, (session["user_id"],)).fetchall()

    return render_template("doctor/add_report.html", patients=patients)


@app.route("/doctor/reports")
def doctor_reports():
    if not role_required("doctor"):
        return redirect(url_for("index"))

    reports = db().execute("""
        SELECT r.*, p.name AS patient_name, p.blood_group
        FROM   test_reports r
        JOIN   patients p ON r.patient_id = p.id
        WHERE  r.doctor_id = ?
        ORDER  BY r.date DESC
    """, (session["user_id"],)).fetchall()

    return render_template("doctor/reports.html", reports=reports)


#  PATIENT ROUTES
@app.route("/patient/dashboard")
def patient_dashboard():
    if not role_required("patient"):
        return redirect(url_for("index"))

    appointments = db().execute("""
        SELECT a.*, d.name AS doctor_name, d.specialization
        FROM   appointments a
        JOIN   doctors d ON a.doctor_id = d.id
        WHERE  a.patient_id = ?
        ORDER  BY a.date DESC
    """, (session["user_id"],)).fetchall()

    reports = db().execute("""
        SELECT r.*, d.name AS doctor_name, d.specialization
        FROM   test_reports r
        JOIN   doctors d ON r.doctor_id = d.id
        WHERE  r.patient_id = ?
        ORDER  BY r.date DESC
    """, (session["user_id"],)).fetchall()

    stats = {
        "total_appointments": len(appointments),
        "pending":  sum(1 for a in appointments if a["status"] == "pending"),
        "reports":  len(reports),
    }
    return render_template("patient/dashboard.html",
                           appointments=appointments, reports=reports, stats=stats)


@app.route("/patient/book", methods=["GET", "POST"])
def book_appointment():
    if not role_required("patient"):
        return redirect(url_for("index"))

    if request.method == "POST":
        db().execute("""
            INSERT INTO appointments (patient_id, doctor_id, date, time_slot, reason, status)
            VALUES (?,?,?,?,?,?)
        """, (
            session["user_id"], request.form["doctor_id"],
            request.form["date"],      request.form["time_slot"],
            request.form["reason"],    "pending"
        ))
        db().commit()
        flash("Appointment booked! The doctor will confirm shortly.", "success")
        return redirect(url_for("patient_dashboard"))

    doctors = db().execute(
        "SELECT id, name, specialization, phone FROM doctors ORDER BY name"
    ).fetchall()
    return render_template("patient/book.html", doctors=doctors)


@app.route("/patient/reports")
def patient_reports():
    if not role_required("patient"):
        return redirect(url_for("index"))

    reports = db().execute("""
        SELECT r.*, d.name AS doctor_name, d.specialization
        FROM   test_reports r
        JOIN   doctors d ON r.doctor_id = d.id
        WHERE  r.patient_id = ?
        ORDER  BY r.date DESC
    """, (session["user_id"],)).fetchall()

    return render_template("patient/reports.html", reports=reports)


@app.route("/patient/profile", methods=["GET", "POST"])
def patient_profile():
    if not role_required("patient"):
        return redirect(url_for("index"))

    if request.method == "POST":
        db().execute(
            "UPDATE patients SET phone = ?, age = ?, blood_group = ? WHERE id = ?",
            (request.form["phone"], request.form["age"],
             request.form["blood_group"], session["user_id"])
        )
        db().commit()
        flash("Profile updated.", "success")

    patient = db().execute(
        "SELECT * FROM patients WHERE id = ?", (session["user_id"],)
    ).fetchone()
    return render_template("patient/profile.html", patient=patient)

#  PATIENT — cancel appointment
@app.route("/patient/appointment/<int:appt_id>/cancel", methods=["POST"])
def cancel_appointment(appt_id):
    if not role_required("patient"):
        return redirect(url_for("index"))
    # make sure this appointment actually belongs to this patient
    appt = db().execute(
        "SELECT * FROM appointments WHERE id = ? AND patient_id = ?",
        (appt_id, session["user_id"])
    ).fetchone()
    if appt:
        db().execute(
            "UPDATE appointments SET status = 'cancelled' WHERE id = ?", (appt_id,)
        )
        db().commit()
        flash("Appointment cancelled.", "success")
    else:
        flash("Appointment not found.", "error")
    return redirect(url_for("patient_dashboard"))


#  DOCTOR — delete wrong report
@app.route("/doctor/report/<int:report_id>/delete", methods=["POST"])
def delete_report(report_id):
    if not role_required("doctor"):
        return redirect(url_for("index"))
    # make sure this report belongs to this doctor
    report = db().execute(
        "SELECT * FROM test_reports WHERE id = ? AND doctor_id = ?",
        (report_id, session["user_id"])
    ).fetchone()
    if report:
        db().execute("DELETE FROM test_reports WHERE id = ?", (report_id,))
        db().commit()
        flash("Report deleted.", "success")
    else:
        flash("Report not found.", "error")
    return redirect(url_for("doctor_reports"))


#  JSON API — live doctor-search (Fetch API)
@app.route("/api/doctors")
def api_doctors():
    q    = request.args.get("q", "")
    rows = db().execute(
        "SELECT id, name, specialization FROM doctors WHERE name LIKE ? OR specialization LIKE ?",
        (f"%{q}%", f"%{q}%")
    ).fetchall()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
