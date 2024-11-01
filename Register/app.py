import cv2
import uuid
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from deepface import DeepFace
import numpy as np
from functools import wraps
from datetime import datetime, timedelta, timezone
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')

app = Flask(__name__, instance_path=instance_path)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'MbullGendutBoyot200kg'
CORS(app)
hashed_password = generate_password_hash("adminpassword")

db = SQLAlchemy(app)

# Definisikan model pengguna
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    user_id = db.Column(db.String(36), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    nik = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    photo_filename = db.Column(db.String(200), nullable=False)
    
class VerificationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    user_id = db.Column(db.String(36), nullable=False)
    verification_status = db.Column(db.String(50), nullable=False)
    check_in = db.Column(db.Boolean, default=False)
    check_out = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))))


    
def __repr__(self):
        return f'<VerificationLog user_id={self.user_id} status={self.verification_status} timestamp={self.timestamp}>'
# Buat database
with app.app_context():
    db.create_all()
def capture_photo(user_id):
    # Buat direktori untuk menyimpan foto jika belum ada
    photos_dir = os.path.join(app.static_folder, "photos")
    if not os.path.exists(photos_dir):
        os.makedirs(photos_dir)

    # Buka kamera
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Tidak dapat mengakses kamera")
        return None

    print("Tekan tombol 'Space' untuk mengambil foto, dan 'Esc' untuk keluar.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Gagal menangkap gambar")
            break

        # Tampilkan frame saat ini
        cv2.imshow('Capture Photo', frame)

        # Tunggu input dari pengguna
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Tombol Esc untuk keluar
            break
        elif key == 32:  # Tombol Space untuk menangkap gambar
            # Buat nama file untuk menyimpan gambar (hanya nama file, bukan path lengkap)
            photo_filename = f"{user_id}.jpg"
            photo_path = os.path.join(photos_dir, photo_filename)
            cv2.imwrite(photo_path, frame)
            print(f"Foto berhasil disimpan dengan nama: {photo_path}")
            cap.release()
            cv2.destroyAllWindows()
            return photo_filename

    cap.release()
    cv2.destroyAllWindows()
    return None

def generate_unique_id():
    return str(uuid.uuid4())

def verify_face(input_image_path, user_image_path):
    try:
        result = DeepFace.verify(img1_path=input_image_path, img2_path=user_image_path, enforce_detection=False)
        return result['verified']
    except Exception as e:
        print(f"Error in face verification: {e}")
        return False

@app.route('/')
def index():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_user():
    # Input data pengguna
    name = request.form['name']
    nik = request.form['nik']
    address = request.form['address']
    position = request.form['position']
    phone_number = request.form['phone_number']

    # Buat ID unik
    user_id = generate_unique_id()
    print(f"ID Unik Pengguna: {user_id}")

    # Ambil foto dari kamera
    photo_filename = capture_photo(user_id)
    if photo_filename is None:
        return "Registrasi dibatalkan. Tidak dapat mengambil foto."

    # Simpan informasi registrasi pengguna ke database
    new_user = User(
        user_id=user_id,
        name=name,
        nik=nik,
        address=address,
        position=position,
        phone_number=phone_number,
        photo_filename=photo_filename
    )
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Cek kredensial login admin
        if username == 'admin' and check_password_hash(hashed_password, password):
            session['admin'] = True
            return redirect(url_for('list_users'))
        else:
            flash('Username atau password salah', 'danger')

    return render_template('loginadmin.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            flash('Silakan login untuk mengakses halaman ini.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/users')
@login_required
def list_users():
    users = User.query.all()
    logs = VerificationLog.query.order_by(VerificationLog.timestamp.desc()).all() 
    return render_template('users.html', users=users, logs=logs)

@app.route('/delete_user/<int:id>', methods=['GET', 'POST'])
def delete_user(id):
    # Cari pengguna berdasarkan ID
    user = User.query.get_or_404(id)

    try:
        # Hapus pengguna dari database
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('list_users'))
    except:
        return "Terjadi kesalahan saat menghapus data pengguna."

@app.route('/verify_face', methods=['GET', 'POST'])
def verify_face_route():
    if request.method == 'POST':
        # Ambil foto untuk verifikasi
        input_photo_filename = capture_photo("verification")
        if input_photo_filename is None:
            flash('Verifikasi dibatalkan. Tidak dapat mengambil foto.', 'danger')
            return redirect(url_for('login'))

        input_image_path = os.path.join(app.static_folder, "photos", input_photo_filename)

        # Lakukan verifikasi wajah dengan membandingkan dengan setiap pengguna yang ada
        users = User.query.all()
        verified = False
        verified_user = None

        for user in users:
            user_image_path = os.path.join(app.static_folder, "photos", user.photo_filename)
            try:
                # Verifikasi wajah antara foto input dan foto dari database
                is_verified = verify_face(input_image_path, user_image_path)
                if is_verified:
                    verified_user = user
                    verified = True
                    break
            except Exception as e:
                print(f"Error in face verification: {e}")

        if verified:
            log = VerificationLog(user_id=verified_user.user_id, verification_status='Success', timestamp=datetime.now(timezone(timedelta(hours=7))))
            db.session.add(log)
            db.session.commit()
            # Redirect atau lakukan aksi lain sesuai kebutuhan, misalnya akses ke halaman admin
            flash('Verifikasi berhasil. Selamat datang!', 'success')
            return redirect(url_for('list_users'))
        else:
            log = VerificationLog(user_id='unknown', verification_status='Failed', timestamp=datetime.now(timezone(timedelta(hours=7))))
            db.session.add(log)
            db.session.commit()
            flash('Gagal Menemukan wajah,silahkan Coba lagi.', 'danger')
            return redirect(url_for('login'))

    return render_template('verifikasi.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify_user():
    # Logika verifikasi sama persis dengan verify_face_route
    if request.method == 'POST':
        # Ambil foto untuk verifikasi
        input_photo_filename = capture_photo("verification")
        if input_photo_filename is None:
            flash('Verifikasi dibatalkan. Tidak dapat mengambil foto.', 'danger')
            return redirect(url_for('verify_user'))

        input_image_path = os.path.join(app.static_folder, "photos", input_photo_filename)

        # Lakukan verifikasi wajah dengan membandingkan dengan setiap pengguna yang ada
        users = User.query.all()
        verified = False
        verified_user = None

        for user in users:
            user_image_path = os.path.join(app.static_folder, "photos", user.photo_filename)
            try:
                # Verifikasi wajah antara foto input dan foto dari database
                is_verified = verify_face(input_image_path, user_image_path)
                if is_verified:
                    verified_user = user
                    verified = True
                    break
            except Exception as e:
                print(f"Error in face verification: {e}")

        if verified:
            last_log = VerificationLog.query.filter_by(user_id=verified_user.user_id).order_by(VerificationLog.timestamp.desc()).first()
            if last_log and last_log.check_in and not last_log.check_out:
                # Jika sudah check-in, maka sekarang akan check-out
                log = VerificationLog(user_id=verified_user.user_id, verification_status='Success', check_in=False, check_out=True)
                flash('Berhasil Check-Out', 'success')
            else:
                # Jika belum check-in, maka sekarang akan check-in
                log = VerificationLog(user_id=verified_user.user_id, verification_status='Success', check_in=True, check_out=False)
                flash('Berhasil Check-In', 'success')
                
            db.session.add(log)
            db.session.commit()
            return render_template('welcome.html', user=verified_user, log=log)
        else:
            log = VerificationLog(user_id='unknown', verification_status='Failed')
            db.session.add(log)
            db.session.commit()
            flash('Maaf, coba lagi. Wajah tidak dikenali.', 'danger')
            return redirect(url_for('verify_user'))

    return render_template('verifikasiid.html')

@app.route('/logs')
def view_logs():
    logs = VerificationLog.query.order_by(VerificationLog.timestamp.desc()).all()
    return render_template('logs.html', logs=logs)

from flask import Flask, render_template, request, jsonify, session, flash

# tambahkan route ini di app.py pada aplikasi Register
@app.route('/verification_status', methods=['GET'])
def verification_status():
    # Ambil status verifikasi dari database
    last_log = VerificationLog.query.order_by(VerificationLog.timestamp.desc()).first()
    if last_log:
        return jsonify({
            'user_id': last_log.user_id,
            'status': last_log.verification_status,
            'check_in': last_log.check_in,
            'check_out': last_log.check_out,
            'timestamp': last_log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
    else:
        return jsonify({
            'status': 'No logs available'
        })


if __name__ == "__main__":
    app.run(debug=True)