from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    users = db.relationship(
        'User',
        backref='department',
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    blacklist = db.Column(db.Boolean,default = False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'), nullable=True)

    doctor_appointments = db.relationship(
        'Appointment',
        backref='doctor',
        lazy='dynamic',
        foreign_keys='Appointment.doctor_id',
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    patient_appointments = db.relationship('Appointment',backref='patient',lazy='dynamic',foreign_keys='Appointment.patient_id',
        cascade="all, delete-orphan",passive_deletes=True)
    availabilities = db.relationship('Availability',backref='doctor',lazy=True,cascade="all, delete-orphan",passive_deletes=True)
    schedules = db.relationship('DoctorSchedule',backref='doctor',lazy=True,cascade="all, delete-orphan",passive_deletes=True)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default="Pending")

    treatments = db.relationship('Treatment',backref='appointment',cascade="all, delete-orphan",passive_deletes=True)
    prescriptions = db.relationship('Prescription',backref='appointment',cascade="all, delete-orphan",passive_deletes=True)
    tests = db.relationship('MedicalTest',backref='appointment',cascade="all, delete-orphan",passive_deletes=True)

class Availability(db.Model):
    __tablename__ = 'availabilities'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)

class DoctorSchedule(db.Model):
    __tablename__ = 'doctor_schedules'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)

class Treatment(db.Model):
    __tablename__ = 'treatments'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', ondelete='CASCADE'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    diagnosis = db.Column(db.String(200))
    notes = db.Column(db.Text)
    date = db.Column(db.Date)

    doctor = db.relationship("User", foreign_keys=[doctor_id])
    patient = db.relationship("User", foreign_keys=[patient_id])

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', ondelete='CASCADE'))
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))

    medicine_name = db.Column(db.String(120))
    dosage = db.Column(db.String(120))
    frequency = db.Column(db.String(120))
    duration = db.Column(db.String(120))

    doctor = db.relationship("User", foreign_keys=[doctor_id])
    patient = db.relationship("User", foreign_keys=[patient_id])

class MedicalTest(db.Model):
    __tablename__ = 'medical_tests'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', ondelete='CASCADE'))
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))

    test_name = db.Column(db.String(120))
    result = db.Column(db.Text)
    report_file = db.Column(db.String(200))
    date = db.Column(db.Date)

    doctor = db.relationship("User", foreign_keys=[doctor_id])
    patient = db.relationship("User", foreign_keys=[patient_id])


class PatientHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, nullable=False)
    visit_type = db.Column(db.String(100))
    test = db.Column(db.String(200))
    diagnosis = db.Column(db.Text)
    medicines = db.Column(db.Text)
    prescription = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    