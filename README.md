# 🏥 MediCare — Hospital Management System

A full-stack web application for managing hospital appointments and patient records.

## Features
- Role-based login for Doctors and Patients
- Doctor: manage appointments, search patients, upload lab reports
- Patient: book appointments, view lab reports, edit profile

## Tech Stack
Python, Flask, SQLite, Tailwind CSS, JavaScript

## Run Locally
pip install flask
python app.py

Open → http://127.0.0.1:5000

## Demo Logins
| Role | Email | Password |
|------|-------|----------|
| Doctor | arjun@hospital.com | doctor123 |
| Patient | amit@gmail.com | patient123 |

## Project Structure
├── app.py          # All Flask routes
├── database.py     # Schema, DB connection, seed data
├── requirements.txt
└── templates/
    ├── base.html
    ├── index.html
    ├── auth/
    ├── doctor/
    └── patient/
