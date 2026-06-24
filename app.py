from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from datetime import date, datetime, time, timedelta

app = Flask(__name__)

app.secret_key = 'klinik_rahasia'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'clinic_reservation'

mysql = MySQL(app)


def get_doctor_time_slots():
    return [
        '08:00', '09:00', '10:00', '11:00', '12:00',
        '13:00', '14:00', '15:00', '16:00', '17:00'
    ]


def get_ambulance_time_slots():
    slots = []
    for hour in range(24):
        slots.append(f"{hour:02d}:00")
    return slots


def format_date_value(value):
    if value is None:
        return ''
    if isinstance(value, (datetime, date)):
        return value.strftime('%Y-%m-%d')
    return str(value)[:10]


def format_time_value(value):
    if value is None:
        return ''
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    if isinstance(value, time):
        return value.strftime('%H:%M')
    if isinstance(value, datetime):
        return value.strftime('%H:%M')

    text = str(value)
    parts = text.split(':')
    if len(parts) >= 2:
        try:
            return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
        except:
            return text[:5]
    return text


def format_rows_date_time(rows, date_index, time_index):
    result = []
    for row in rows:
        row = list(row)
        row[date_index] = format_date_value(row[date_index])
        row[time_index] = format_time_value(row[time_index])
        result.append(row)
    return result


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            flash('Email sudah terdaftar, silakan gunakan email lain.', 'danger')
            return redirect(url_for('register'))

        cur.execute(
            "INSERT INTO users (full_name, email, password, role) VALUES (%s, %s, %s, %s)",
            (full_name, email, password, 'user')
        )
        mysql.connection.commit()
        cur.close()

        flash('Registrasi berhasil, silakan login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        account = cur.fetchone()
        cur.close()

        if account:
            session['loggedin'] = True
            session['user_id'] = account[0]
            session['full_name'] = account[1]
            session['email'] = account[2]
            session['role'] = account[4]

            flash('Login berhasil.', 'success')

            if account[4] == 'admin':
                return redirect(url_for('dashboard_admin'))
            else:
                return redirect(url_for('dashboard_user'))
        else:
            flash('Email atau password salah.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard-user')
def dashboard_user():
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    if session['role'] != 'user':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    return render_template('dashboard_user.html')


@app.route('/dashboard-admin')
def dashboard_admin():
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    if session['role'] != 'admin':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    return render_template('dashboard_admin.html')


@app.route('/doctors')
def doctors():
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM doctors ORDER BY id DESC")
    doctors_data = cur.fetchall()
    cur.close()

    return render_template('doctors.html', doctors=doctors_data)


@app.route('/add-doctor', methods=['POST'])
def add_doctor():
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    doctor_name = request.form['doctor_name']
    specialization = request.form['specialization']
    schedule_day = request.form['schedule_day']
    schedule_time = request.form['schedule_time']
    photo = request.form['photo']

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO doctors (doctor_name, specialization, schedule_day, schedule_time, photo) VALUES (%s, %s, %s, %s, %s)",
        (doctor_name, specialization, schedule_day, schedule_time, photo)
    )
    mysql.connection.commit()
    cur.close()

    flash('Data dokter berhasil ditambahkan.', 'success')
    return redirect(url_for('doctors'))


@app.route('/edit-doctor/<int:id>', methods=['POST'])
def edit_doctor(id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    doctor_name = request.form['doctor_name']
    specialization = request.form['specialization']
    schedule_day = request.form['schedule_day']
    schedule_time = request.form['schedule_time']
    photo = request.form['photo']

    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE doctors SET doctor_name=%s, specialization=%s, schedule_day=%s, schedule_time=%s, photo=%s WHERE id=%s",
        (doctor_name, specialization, schedule_day, schedule_time, photo, id)
    )
    mysql.connection.commit()
    cur.close()

    flash('Data dokter berhasil diupdate.', 'info')
    return redirect(url_for('doctors'))


@app.route('/delete-doctor/<int:id>')
def delete_doctor(id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM doctors WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()

    flash('Data dokter berhasil dihapus.', 'warning')
    return redirect(url_for('doctors'))


@app.route('/appointments')
def appointments():
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, doctor_name, specialization FROM doctors ORDER BY doctor_name ASC")
    doctors_data = cur.fetchall()

    if session['role'] == 'admin':
        cur.execute("""
            SELECT
                appointments.id,
                appointments.user_id,
                users.full_name,
                appointments.doctor_id,
                doctors.doctor_name,
                doctors.specialization,
                appointments.appointment_date,
                appointments.appointment_time,
                appointments.complaint,
                appointments.status
            FROM appointments
            JOIN users ON appointments.user_id = users.id
            JOIN doctors ON appointments.doctor_id = doctors.id
            ORDER BY appointments.id DESC
        """)
        appointments_data = format_rows_date_time(cur.fetchall(), 6, 7)
    else:
        appointments_data = []

    cur.close()

    return render_template(
        'appointments.html',
        appointments=appointments_data,
        doctors=doctors_data,
        time_slots=get_doctor_time_slots()
    )


@app.route('/my-appointments')
def my_appointments():
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    if session['role'] != 'user':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, doctor_name, specialization FROM doctors ORDER BY doctor_name ASC")
    doctors_data = cur.fetchall()

    cur.execute("""
        SELECT
            appointments.id,
            appointments.user_id,
            users.full_name,
            appointments.doctor_id,
            doctors.doctor_name,
            doctors.specialization,
            appointments.appointment_date,
            appointments.appointment_time,
            appointments.complaint,
            appointments.status
        FROM appointments
        JOIN users ON appointments.user_id = users.id
        JOIN doctors ON appointments.doctor_id = doctors.id
        WHERE appointments.user_id = %s
        ORDER BY appointments.id DESC
    """, (session['user_id'],))
    appointments_data = format_rows_date_time(cur.fetchall(), 6, 7)
    cur.close()

    return render_template(
        'my_appointments.html',
        appointments=appointments_data,
        doctors=doctors_data,
        time_slots=get_doctor_time_slots()
    )


@app.route('/status')
def status_page():
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    if session['role'] != 'user':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            appointments.id,
            doctors.doctor_name,
            doctors.specialization,
            appointments.appointment_date,
            appointments.appointment_time,
            appointments.complaint,
            appointments.status
        FROM appointments
        JOIN doctors ON appointments.doctor_id = doctors.id
        WHERE appointments.user_id = %s
        ORDER BY appointments.id DESC
    """, (session['user_id'],))
    appointment_status = format_rows_date_time(cur.fetchall(), 3, 4)

    cur.execute("""
        SELECT
            ambulance_bookings.id,
            ambulance_bookings.pickup_address,
            ambulance_bookings.destination_address,
            ambulance_bookings.booking_date,
            ambulance_bookings.booking_time,
            ambulance_bookings.patient_condition,
            ambulance_bookings.status
        FROM ambulance_bookings
        WHERE ambulance_bookings.user_id = %s
        ORDER BY ambulance_bookings.id DESC
    """, (session['user_id'],))
    ambulance_status = format_rows_date_time(cur.fetchall(), 3, 4)

    cur.close()
    return render_template('status.html', appointment_status=appointment_status, ambulance_status=ambulance_status)


@app.route('/add-appointment', methods=['POST'])
def add_appointment():
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    if session['role'] != 'user':
        flash('Hanya user yang bisa membuat reservasi.', 'danger')
        return redirect(url_for('appointments'))

    doctor_id = request.form['doctor_id']
    appointment_date = request.form['appointment_date']
    appointment_time = request.form['appointment_time']
    complaint = request.form['complaint']

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT * FROM appointments
        WHERE doctor_id = %s
        AND appointment_date = %s
        AND appointment_time = %s
        AND status IN ('pending', 'approved')
    """, (doctor_id, appointment_date, appointment_time))
    existing_schedule = cur.fetchone()

    if existing_schedule:
        cur.close()
        flash('Reservasi gagal, jadwal dokter di jam itu sudah terisi.', 'danger')
        return redirect(url_for('appointments'))

    cur.execute("""
        INSERT INTO appointments (user_id, doctor_id, appointment_date, appointment_time, complaint, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (session['user_id'], doctor_id, appointment_date, appointment_time, complaint, 'pending'))
    mysql.connection.commit()
    cur.close()

    flash('Reservasi berhasil dibuat.', 'success')
    return redirect(url_for('status_page'))


@app.route('/edit-appointment/<int:id>', methods=['POST'])
def edit_appointment(id):
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    doctor_id = request.form['doctor_id']
    appointment_date = request.form['appointment_date']
    appointment_time = request.form['appointment_time']
    complaint = request.form['complaint']

    cur = mysql.connection.cursor()

    if session['role'] == 'admin':
        cur.execute("SELECT * FROM appointments WHERE id=%s", (id,))
    else:
        cur.execute("SELECT * FROM appointments WHERE id=%s AND user_id=%s", (id, session['user_id']))

    appointment = cur.fetchone()

    if not appointment:
        cur.close()
        flash('Data reservasi tidak ditemukan.', 'danger')
        return redirect(url_for('appointments'))

    if session['role'] == 'user' and appointment[6] != 'pending':
        cur.close()
        flash('Reservasi yang sudah diproses tidak bisa diedit user.', 'danger')
        return redirect(url_for('my_appointments'))

    cur.execute("""
        SELECT * FROM appointments
        WHERE doctor_id = %s
        AND appointment_date = %s
        AND appointment_time = %s
        AND id != %s
        AND status IN ('pending', 'approved')
    """, (doctor_id, appointment_date, appointment_time, id))
    duplicate_schedule = cur.fetchone()

    if duplicate_schedule:
        cur.close()
        flash('Update gagal, jadwal dokter di jam itu sudah terisi.', 'danger')
        if session['role'] == 'admin':
            return redirect(url_for('appointments'))
        return redirect(url_for('my_appointments'))

    if session['role'] == 'admin':
        cur.execute("""
            UPDATE appointments
            SET doctor_id=%s, appointment_date=%s, appointment_time=%s, complaint=%s
            WHERE id=%s
        """, (doctor_id, appointment_date, appointment_time, complaint, id))
    else:
        cur.execute("""
            UPDATE appointments
            SET doctor_id=%s, appointment_date=%s, appointment_time=%s, complaint=%s
            WHERE id=%s AND user_id=%s
        """, (doctor_id, appointment_date, appointment_time, complaint, id, session['user_id']))

    mysql.connection.commit()
    cur.close()

    flash('Data reservasi berhasil diupdate.', 'info')

    if session['role'] == 'admin':
        return redirect(url_for('appointments'))
    return redirect(url_for('my_appointments'))


@app.route('/delete-appointment/<int:id>')
def delete_appointment(id):
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    if session['role'] == 'admin':
        cur.execute("DELETE FROM appointments WHERE id=%s", (id,))
        mysql.connection.commit()
        cur.close()
        flash('Data reservasi berhasil dihapus.', 'warning')
        return redirect(url_for('appointments'))

    cur.execute("SELECT * FROM appointments WHERE id=%s AND user_id=%s", (id, session['user_id']))
    appointment = cur.fetchone()

    if not appointment:
        cur.close()
        flash('Data reservasi tidak ditemukan.', 'danger')
        return redirect(url_for('my_appointments'))

    if appointment[6] != 'pending':
        cur.close()
        flash('Reservasi yang sudah diproses tidak bisa dihapus user.', 'danger')
        return redirect(url_for('my_appointments'))

    cur.execute("DELETE FROM appointments WHERE id=%s AND user_id=%s", (id, session['user_id']))
    mysql.connection.commit()
    cur.close()

    flash('Data reservasi berhasil dihapus.', 'warning')
    return redirect(url_for('my_appointments'))


@app.route('/appointment-approve/<int:id>')
def appointment_approve(id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT status FROM appointments WHERE id=%s", (id,))
    appointment = cur.fetchone()

    if not appointment:
        cur.close()
        flash('Data reservasi tidak ditemukan.', 'danger')
        return redirect(url_for('appointments'))

    current_status = appointment[0]

    if current_status == 'approved':
        cur.close()
        flash('Reservasi ini sudah disetujui sebelumnya.', 'info')
        return redirect(url_for('appointments'))

    if current_status == 'completed':
        cur.close()
        flash('Reservasi ini sudah selesai konsultasi.', 'warning')
        return redirect(url_for('appointments'))

    cur.execute("UPDATE appointments SET status='approved' WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()

    flash('Permohonan reservasi disetujui.', 'success')
    return redirect(url_for('appointments'))


@app.route('/appointment-reject/<int:id>')
def appointment_reject(id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT status FROM appointments WHERE id=%s", (id,))
    appointment = cur.fetchone()

    if not appointment:
        cur.close()
        flash('Data reservasi tidak ditemukan.', 'danger')
        return redirect(url_for('appointments'))

    current_status = appointment[0]

    if current_status == 'rejected':
        cur.close()
        flash('Reservasi ini sudah ditolak sebelumnya.', 'info')
        return redirect(url_for('appointments'))

    if current_status == 'completed':
        cur.close()
        flash('Reservasi yang sudah selesai konsultasi tidak bisa ditolak.', 'warning')
        return redirect(url_for('appointments'))

    cur.execute("UPDATE appointments SET status='rejected' WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()

    flash('Permohonan reservasi ditolak.', 'danger')
    return redirect(url_for('appointments'))


@app.route('/appointment-complete/<int:id>')
def appointment_complete(id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT status FROM appointments WHERE id=%s", (id,))
    appointment = cur.fetchone()

    if not appointment:
        cur.close()
        flash('Data reservasi tidak ditemukan.', 'danger')
        return redirect(url_for('appointments'))

    current_status = appointment[0]

    if current_status != 'approved':
        cur.close()
        flash('Pasien hanya bisa ditandai sudah konsul jika reservasi sudah approved.', 'warning')
        return redirect(url_for('appointments'))

    cur.execute("UPDATE appointments SET status='completed' WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()

    flash('Pasien ditandai sudah konsul ke dokter.', 'info')
    return redirect(url_for('appointments'))


@app.route('/ambulance')
def ambulance():
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    if session['role'] == 'admin':
        cur.execute("""
            SELECT
                ambulance_bookings.id,
                users.full_name,
                ambulance_bookings.pickup_address,
                ambulance_bookings.destination_address,
                ambulance_bookings.booking_date,
                ambulance_bookings.booking_time,
                ambulance_bookings.patient_condition,
                ambulance_bookings.status
            FROM ambulance_bookings
            JOIN users ON ambulance_bookings.user_id = users.id
            ORDER BY ambulance_bookings.id DESC
        """)
        ambulance_data = format_rows_date_time(cur.fetchall(), 4, 5)
    else:
        ambulance_data = []

    cur.close()
    return render_template('ambulance.html', bookings=ambulance_data, time_slots=get_ambulance_time_slots())


@app.route('/my-ambulance')
def my_ambulance():
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    if session['role'] != 'user':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            ambulance_bookings.id,
            users.full_name,
            ambulance_bookings.pickup_address,
            ambulance_bookings.destination_address,
            ambulance_bookings.booking_date,
            ambulance_bookings.booking_time,
            ambulance_bookings.patient_condition,
            ambulance_bookings.status
        FROM ambulance_bookings
        JOIN users ON ambulance_bookings.user_id = users.id
        WHERE ambulance_bookings.user_id = %s
        ORDER BY ambulance_bookings.id DESC
    """, (session['user_id'],))
    ambulance_data = format_rows_date_time(cur.fetchall(), 4, 5)
    cur.close()

    return render_template('my_ambulance.html', bookings=ambulance_data, time_slots=get_ambulance_time_slots())


@app.route('/add-ambulance', methods=['POST'])
def add_ambulance():
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    if session['role'] != 'user':
        flash('Hanya user yang bisa booking ambulance.', 'danger')
        return redirect(url_for('ambulance'))

    pickup_address = request.form['pickup_address']
    destination_address = request.form['destination_address']
    booking_date = request.form['booking_date']
    booking_time = request.form['booking_time']
    patient_condition = request.form['patient_condition']

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO ambulance_bookings (user_id, pickup_address, destination_address, booking_date, booking_time, patient_condition, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (session['user_id'], pickup_address, destination_address, booking_date, booking_time, patient_condition, 'pending'))
    mysql.connection.commit()
    cur.close()

    flash('Booking ambulance berhasil dibuat.', 'success')
    return redirect(url_for('status_page'))


@app.route('/edit-ambulance/<int:id>', methods=['POST'])
def edit_ambulance(id):
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    pickup_address = request.form['pickup_address']
    destination_address = request.form['destination_address']
    booking_date = request.form['booking_date']
    booking_time = request.form['booking_time']
    patient_condition = request.form['patient_condition']

    cur = mysql.connection.cursor()

    if session['role'] == 'admin':
        cur.execute("SELECT * FROM ambulance_bookings WHERE id=%s", (id,))
    else:
        cur.execute("SELECT * FROM ambulance_bookings WHERE id=%s AND user_id=%s", (id, session['user_id']))

    booking = cur.fetchone()

    if not booking:
        cur.close()
        flash('Data booking ambulance tidak ditemukan.', 'danger')
        return redirect(url_for('ambulance'))

    if session['role'] == 'user' and booking[7] != 'pending':
        cur.close()
        flash('Booking yang sudah diproses tidak bisa diedit user.', 'danger')
        return redirect(url_for('my_ambulance'))

    if session['role'] == 'admin':
        cur.execute("""
            UPDATE ambulance_bookings
            SET pickup_address=%s, destination_address=%s, booking_date=%s, booking_time=%s, patient_condition=%s
            WHERE id=%s
        """, (pickup_address, destination_address, booking_date, booking_time, patient_condition, id))
    else:
        cur.execute("""
            UPDATE ambulance_bookings
            SET pickup_address=%s, destination_address=%s, booking_date=%s, booking_time=%s, patient_condition=%s
            WHERE id=%s AND user_id=%s
        """, (pickup_address, destination_address, booking_date, booking_time, patient_condition, id, session['user_id']))

    mysql.connection.commit()
    cur.close()

    flash('Booking ambulance berhasil diupdate.', 'info')

    if session['role'] == 'admin':
        return redirect(url_for('ambulance'))
    return redirect(url_for('my_ambulance'))


@app.route('/delete-ambulance/<int:id>')
def delete_ambulance(id):
    if 'loggedin' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    if session['role'] == 'admin':
        cur.execute("DELETE FROM ambulance_bookings WHERE id=%s", (id,))
        mysql.connection.commit()
        cur.close()
        flash('Data booking ambulance berhasil dihapus.', 'warning')
        return redirect(url_for('ambulance'))

    cur.execute("SELECT * FROM ambulance_bookings WHERE id=%s AND user_id=%s", (id, session['user_id']))
    booking = cur.fetchone()

    if not booking:
        cur.close()
        flash('Data booking ambulance tidak ditemukan.', 'danger')
        return redirect(url_for('my_ambulance'))

    if booking[7] != 'pending':
        cur.close()
        flash('Booking yang sudah diproses tidak bisa dihapus user.', 'danger')
        return redirect(url_for('my_ambulance'))

    cur.execute("DELETE FROM ambulance_bookings WHERE id=%s AND user_id=%s", (id, session['user_id']))
    mysql.connection.commit()
    cur.close()

    flash('Data booking ambulance berhasil dihapus.', 'warning')
    return redirect(url_for('my_ambulance'))


@app.route('/ambulance-approve/<int:id>')
def ambulance_approve(id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT status FROM ambulance_bookings WHERE id=%s", (id,))
    booking = cur.fetchone()

    if not booking:
        cur.close()
        flash('Data booking ambulance tidak ditemukan.', 'danger')
        return redirect(url_for('ambulance'))

    current_status = booking[0]

    if current_status == 'approved':
        cur.close()
        flash('Booking ambulance ini sudah disetujui sebelumnya.', 'info')
        return redirect(url_for('ambulance'))

    if current_status == 'completed':
        cur.close()
        flash('Booking ambulance ini sudah selesai.', 'warning')
        return redirect(url_for('ambulance'))

    cur.execute("UPDATE ambulance_bookings SET status='approved' WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()

    flash('Booking ambulance disetujui.', 'success')
    return redirect(url_for('ambulance'))


@app.route('/ambulance-reject/<int:id>')
def ambulance_reject(id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT status FROM ambulance_bookings WHERE id=%s", (id,))
    booking = cur.fetchone()

    if not booking:
        cur.close()
        flash('Data booking ambulance tidak ditemukan.', 'danger')
        return redirect(url_for('ambulance'))

    current_status = booking[0]

    if current_status == 'rejected':
        cur.close()
        flash('Booking ambulance ini sudah ditolak sebelumnya.', 'info')
        return redirect(url_for('ambulance'))

    if current_status == 'completed':
        cur.close()
        flash('Booking ambulance yang sudah selesai tidak bisa ditolak.', 'warning')
        return redirect(url_for('ambulance'))

    cur.execute("UPDATE ambulance_bookings SET status='rejected' WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()

    flash('Booking ambulance ditolak.', 'danger')
    return redirect(url_for('ambulance'))


@app.route('/ambulance-complete/<int:id>')
def ambulance_complete(id):
    if 'loggedin' not in session or session['role'] != 'admin':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT status FROM ambulance_bookings WHERE id=%s", (id,))
    booking = cur.fetchone()

    if not booking:
        cur.close()
        flash('Data booking ambulance tidak ditemukan.', 'danger')
        return redirect(url_for('ambulance'))

    current_status = booking[0]

    if current_status != 'approved':
        cur.close()
        flash('Booking ambulance hanya bisa diselesaikan jika sudah approved.', 'warning')
        return redirect(url_for('ambulance'))

    cur.execute("UPDATE ambulance_bookings SET status='completed' WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()

    flash('Booking ambulance ditandai selesai.', 'info')
    return redirect(url_for('ambulance'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Logout berhasil.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)