# 🏥 MediCare — Hospital Management System

A full-stack web application built with **Python (Flask)**, **SQLite**, and **Tailwind CSS**.

## Features
- Role-based login for Doctors and Patients (SHA-256 hashing)
- Doctor: manage appointments, search patients, upload lab reports
- Patient: book appointments with live doctor search, view lab reports, edit profile
- RESTful JSON API endpoint for live doctor search via Fetch API

## Tech Stack
Python, Flask, SQLite, Jinja2, Tailwind CSS, JavaScript

## Run Locally
```bash
pip install flask
python app.py
```
Open → http://127.0.0.1:5000

## Demo Logins
| Role | Email | Password |
|------|-------|----------|
| Doctor | arjun@hospital.com | doctor123 |
| Patient | amit@gmail.com | patient123 |

## Project Structure
```
├── app.py          # All Flask routes
├── database.py     # Schema, DB connection, seed data
├── requirements.txt
└── templates/
    ├── base.html           # Shared sidebar layout
    ├── index.html          # Landing page
    ├── auth/login.html
    ├── auth/register.html
    ├── doctor/dashboard.html
    ├── doctor/patients.html
    ├── doctor/add_report.html
    ├── doctor/reports.html
    ├── patient/dashboard.html
    ├── patient/book.html
    ├── patient/reports.html
    └── patient/profile.html
```
