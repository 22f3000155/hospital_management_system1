# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date, time
from models import db, User, Department, Appointment, Treatment, Availability, DoctorSchedule

app = Flask(__name__)
app.config['SECRET_KEY'] = 'something'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()





@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register/patient', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        password = request.form['password']
        address = request.form['address']
        gender = request.form['gender']
        role="patient",
        is_active=True 

        
        if User.query.filter_by(email=email).first():
            flash("Email already exists", "danger")
            return redirect(url_for('register'))

        
        user = User(
            name=name,
            email=email,
            password=password,
            address=address,
            gender=gender,
            role="patient"
        )

        db.session.add(user)
        db.session.commit()

        flash("Registered successfully Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').lower()
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Email not found", "danger")
            return redirect(url_for('login'))
        
        if user.password != password:
            flash("Incorrect password!", "danger")
            return redirect(url_for('login'))

        
        session['user_id'] = user.id
        session['role'] = user.role

        
        if user.role == "admin":
            return redirect(url_for('admin_dashboard'))
        elif user.role == "doctor":
            return redirect(url_for('doctor_dashboard'))
        else:
            return redirect(url_for('patient_dashboard'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))



@app.route('/admin')
def admin_dashboard():

    if 'user_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('login'))

    current = User.query.get(session['user_id'])

    if current.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    doctors = User.query.filter_by(role='doctor').all()
    patients = User.query.filter_by(role='patient').all()
    appointments = Appointment.query.all()

    return render_template(
        'admin_dashboard.html',
        doctors=doctors,
        patients=patients,
        appointments=appointments
    )

@app.route('/search', methods=['GET'])
def search_all():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))

    query = request.args.get('q', '').lower().strip()

    # Fetch matching doctors and patients by name or email
    doctors = User.query.filter(
        User.role == 'doctor',
        (User.name.ilike(f'%{query}%')) | (User.email.ilike(f'%{query}%'))
    ).all()

    patients = User.query.filter(
        User.role == 'patient',
        (User.name.ilike(f'%{query}%')) | (User.email.ilike(f'%{query}%'))
    ).all()

    appointments = Appointment.query.all()

    return render_template(
        'admin_dashboard.html',
        doctors=doctors,
        patients=patients,
        appointments=appointments,
        search_query=query
    )


@app.route('/admin/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))

    current = User.query.get(session['user_id'])

    
    if current.role != "admin":
        flash("Access denied Only admin can add doctors.", "danger")
        return redirect(url_for('login'))


    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        password = request.form['password'] 
        specialization = request.form['specialization']
        dept_name = request.form['department']

    
        if User.query.filter_by(email=email).first():
            flash("Email already in use", "danger")
            return redirect(url_for('add_doctor'))

    
        dept = Department.query.filter_by(name=dept_name).first()
        if not dept:
            dept = Department(name=dept_name)
            db.session.add(dept)
            db.session.flush()

        
        doctor = User(
            name=name,
            email=email,
            password=password,  
            role='doctor',
            department_id=dept.id
        )
        doctor.specialization = specialization

        db.session.add(doctor)
        db.session.commit()

        flash("Doctor added successfully!", "success")
        return redirect(url_for('admin_dashboard'))

   
    departments = Department.query.all()
    return render_template('admin_add_doctor.html', departments=departments)


@app.route('/admin/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
def edit_doctor(doctor_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    admin = User.query.get(session['user_id'])
    if admin.role != 'admin':
        return redirect(url_for('login'))

    doctor = User.query.get(doctor_id)
    if not doctor or doctor.role != 'doctor':
        flash("Doctor not found", "danger")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        doctor.name = request.form['name']
        doctor.email = request.form['email']
        doctor.password = request.form['password']
        doctor.specialization = request.form['specialization']
        dept_name = request.form['department']

        # update department
        dept = Department.query.filter_by(name=dept_name).first()
        if not dept:
            dept = Department(name=dept_name)
            db.session.add(dept)
            db.session.flush()

        doctor.department_id = dept.id
        db.session.commit()

        flash("Doctor updated successfully", "success")
        return redirect(url_for('admin_dashboard'))

    departments = Department.query.all()
    return render_template("admin_edit_doctor.html", doctor=doctor, departments=departments)


@app.route('/admin/delete_doctor/<int:doctor_id>')
def delete_doctor(doctor_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    admin = User.query.get(session['user_id'])
    if admin.role != 'admin':
        return redirect(url_for('login'))

    doctor = User.query.get(doctor_id)

    if not doctor or doctor.role != 'doctor':
        flash("Doctor not found", "danger")
        return redirect(url_for('admin_dashboard'))

    db.session.delete(doctor)
    db.session.commit()

    flash("Doctor removed", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_blacklist/<int:doctor_id>')
def toggle_blacklist(doctor_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    admin = User.query.get(session['user_id'])
    if admin.role != 'admin':
        return redirect(url_for('login'))

    doctor = User.query.get_or_404(doctor_id)
    if doctor.role != 'doctor':
        flash("Invalid action — not a doctor.", "danger")
        return redirect(url_for('admin_dashboard'))

    # Toggle blacklist status
    doctor.blacklist = not doctor.blacklist
    db.session.commit()

    if doctor.blacklist:
        flash(f"Doctor {doctor.name} has been blacklisted.", "warning")
    else:
        flash(f"Doctor {doctor.name} has been unblocked.", "success")

    return redirect(url_for('admin_dashboard'))



@app.route('/admin/edit_patient/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):
    patient = User.query.get_or_404(id)
    if request.method == 'POST':
        patient.name = request.form['name']
        patient.email = request.form['email']

        db.session.commit()
        flash("Patient updated successfully.", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_patient.html', patient=patient)

@app.route('/admin/delete_patient/<int:id>')
def delete_patient(id):
    patient = User.query.get_or_404(id)
    db.session.delete(patient)
    db.session.commit()
    flash("Patient deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_blacklist_patient/<int:patient_id>')
def toggle_blacklist_patient(patient_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    admin = User.query.get(session['user_id'])
    if admin.role != 'admin':
        return redirect(url_for('login'))

    patient = User.query.get_or_404(patient_id)
    if patient.role != 'patient':
        flash("Invalid action — not a patient.", "danger")
        return redirect(url_for('admin_dashboard'))

    # Toggle blacklist status
    patient.blacklist = not patient.blacklist
    db.session.commit()

    if patient.blacklist:
        flash(f"Patient {patient.name} has been blacklisted.", "warning")
    else:
        flash(f"Patient {patient.name} has been unblocked.", "success")

    return redirect(url_for('admin_dashboard'))


@app.route('/doctor') # doctor routes
def doctor_dashboard():
    if 'user_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('login'))

    doctor = User.query.get(session['user_id'])
    if doctor.role != "doctor":
        flash("Access denied", "danger")
        return redirect(url_for('login'))

    # Booked appointments
    appointments = Appointment.query.filter_by(
        doctor_id=doctor.id
    ).order_by(Appointment.date.asc(), Appointment.time.asc()).all()

    # Available slots (not booked yet)
    available_slots = DoctorSchedule.query.filter_by(
        doctor_id=doctor.id,
        is_booked=False
    ).filter(DoctorSchedule.date >= date.today()).order_by(
        DoctorSchedule.date.asc(), DoctorSchedule.time.asc()
    ).all()

    return render_template(
        'doctor_dashboard.html',
        doctor=doctor,
        appointments=appointments,
        available_slots=available_slots
    )

@app.route('/doctor/add_availability', methods=['GET', 'POST'])
def add_availability():
    doctor = User.query.get(session['user_id'])
    if request.method == 'POST':
        date = request.form['date']  
        time = request.form['time']  

        existing = Availability.query.filter_by(doctor_id=doctor.id, date=date, time=time).first()
        if existing:
            flash("Slot already exists", "warning")
        else:
            slot = Availability(doctor_id=doctor.id, date=date, time=time)
            db.session.add(slot)
            db.session.commit()
            flash("Availability added successfully.", "success")
        return redirect(url_for('doctor_dashboard'))

    return render_template('add_availability.html')

@app.route('/doctor/provide_availability', methods=['GET', 'POST'])
def provide_availability():
    if request.method == 'POST':
        date_str = request.form.get('date')  
        time_str = request.form.get('time') 

        
        if not date_str or not time_str:
            flash("Please select appintment")
            return redirect (url_for("provide_availability"))
        
        date_obj = datetime.strtime(date_str, '%Y-%m-%d').date()
        time_obj = datetime.strtime(time_str, '%H:%M').time()

        new_slot = DoctorSchedule(doctor_id=user.id,
                                  date=date_obj,
                                  time=time_obj,
                                  is_booked=False)
        db.session.add(new_slot)
        db.session.commit()
        flash("Availability added successfully.", "success")

    return render_template('provide_availability.html')

@app.route('/doctor/complete/<int:appointment_id>')
def mark_completed(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = "Completed"
    db.session.commit()
    flash("Appointment marked as completed.", "success")
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/cancel/<int:appointment_id>')
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = "Cancelled"
    db.session.commit()
    flash("Appointment cancelled.", "warning")
    return redirect(url_for('doctor_dashboard'))


@app.route('/patient')
def patient_dashboard():
    if 'user_id' not in session or session.get('role') != 'patient':
        flash("Please login first!", "warning")
        return redirect(url_for('login'))

    patient = User.query.get(session['user_id'])
    appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.date.asc()).all()
    return render_template('patient_dashboard.html', patient=patient, appointments=appointments)



@app.route('/patient/book', methods=['GET', 'POST'])
def book_appointment():
    if 'user_id' not in session or session.get('role') != 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    today = date.today()
    next_7_days = [today + timedelta(days=i) for i in range(7)]

    slots = DoctorSchedule.query.filter(
        DoctorSchedule.date.in_(next_7_days),
        DoctorSchedule.is_booked == False
    ).order_by(DoctorSchedule.date.asc(), DoctorSchedule.time.asc()).all()

    if request.method == 'POST':
        slot_id = request.form['slot_id']
        slot = DoctorSchedule.query.get(slot_id)
        if slot.is_booked:
            flash("Slot already booked.", "warning")
            return redirect(url_for('book_appointment'))

        appointment = Appointment(
            patient_id=session['user_id'],
            doctor_id=slot.doctor_id,
            date=slot.date,
            time=slot.time,
            status='Booked'
        )
        slot.is_booked = True
        db.session.add(appointment)
        db.session.commit()
        flash("Appointment booked successfully!", "success")
        return redirect(url_for('patient_dashboard'))

    return render_template('patient_book.html', slots=slots)


@app.route('/doctor/add_schedule', methods=['GET', 'POST'])
def add_schedule():
    if 'user_id' not in session or session.get('role') != 'doctor':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    doctor = User.query.get(session['user_id'])
    today = date.today().isoformat()

    if request.method == 'POST':
        
        schedule_date_str = request.form['date']  
        schedule_time_str = request.form['time']  
        
        schedule_date = datetime.strptime(schedule_date_str, '%Y-%m-%d').date()
        schedule_time = datetime.strptime(schedule_time_str, '%H:%M').time()

        exists = DoctorSchedule.query.filter_by(
            doctor_id=doctor.id,
            date=schedule_date,
            time=schedule_time
        ).first()

        if exists:
            flash("This slot already exists.", "warning")
            return redirect(url_for('add_schedule'))

        
        slot = DoctorSchedule(
            doctor_id=doctor.id,
            date=schedule_date,
            time=schedule_time,
            is_booked=False
        )
        db.session.add(slot)
        db.session.commit()
        flash("Schedule added successfully.", "success")
        return redirect(url_for('doctor_dashboard'))

    return render_template('doctor_add_schedule.html', today=today)

@app.route('/admin/appointment/complete/<int:appointment_id>')
def admin_complete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = "Completed"
    db.session.commit()
    flash("Appointment marked as completed.", "success")
    return redirect(url_for('admin_dashboard'))

# @app.route('/admin/appointment/cancel/<int:appointment_id>', meethod=["POST"])
@app.route('/patient/appointment/cancel/<int:appointment_id>', methods=['POST'])
def patient_cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = "Cancelled"
    db.session.commit()
    flash("Appointment cancelled.", "warning")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/patient_history/<int:patient_id>')
def patient_history(patient_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    patient = User.query.get_or_404(patient_id)

    
    history = Appointment.query.filter_by(patient_id=patient_id).order_by(
        Appointment.date.desc(), Appointment.time.desc()
    ).all()

    return render_template('patient_history.html', patient=patient, history=history)


@app.route('/update_history', methods=['POST'])
def update_history():
    patient_id = request.form['patient_id']
    visit_type = request.form['visit_type']
    test = request.form['test']
    diagnosis = request.form['diagnosis']
    medicines = request.form['medicines']
    prescription = request.form['prescription']

    
    new_entry = PatientHistory(
        patient_id=patient_id,
        visit_type=visit_type,
        test=test,
        diagnosis=diagnosis,
        medicines=medicines,
        prescription=prescription
    )
    db.session.add(new_entry)
    db.session.commit()

    flash("Patient history updated successfully!", "success")
    return redirect('/doctor_dashboard')




if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role="admin").first():
            admin = User(name="Admin", email="admin@example.com", password="admin123", role="admin")
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)