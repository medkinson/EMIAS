import sqlite3
from flask import Flask, request, jsonify, render_template, session, make_response, redirect, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, current_user, LoginManager, login_user
import os


app = Flask(__name__, static_folder='/var/www/mishland.ru')
login_manager = LoginManager()
login_manager.init_app(app)
app.secret_key = 'think_a_little'


def create_table():
    with sqlite3.connect('database.db') as conn:
       c = conn.cursor()
       c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, account_type TEXT CHECK(account_type IN ("ВРАЧ", "ПАЦИЕНТ")));')
       c.execute('CREATE TABLE IF NOT EXISTS appointments (name TEXT, specialization TEXT, time TEXT, doctor TEXT, username TEXT DEFAULT "NA", id INTEGER, doctor_id INTEGER, FOREIGN KEY(id) REFERENCES users(id), FOREIGN KEY(doctor_id) REFERENCES users(id))')  


class User:
    def __init__(self, id, username, password_hash, account_type):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.account_type = account_type

    

    def is_authenticated(self):
        
        return True

    def is_active(self):
     
        return True

    def is_anonymous(self):
        
        return False

    def get_id(self):
        
        return str(self.id)


@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_data = c.fetchone()
    conn.close()
    if user_data:
        return User(*user_data)
    return None

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user_data = c.fetchone()
    conn.close()

    if user_data and check_password_hash(user_data[2], password):
        user = User(*user_data)
        login_user(user)
        return jsonify({'message': 'Вход выполнен успешно', 'account_type': user_data[3]}), 200

    return jsonify({'message': 'Неверное имя пользователя или пароль'}), 400

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    account_type = data.get('account_type', 'ПАЦИЕНТ')
    hashed_password = generate_password_hash(password)

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password, account_type) VALUES (?, ?, ?)', (username, hashed_password, account_type))
    conn.commit()

    return jsonify({'message': 'Регистрация выполнена успешно'}), 200


@app.route('/get_user_info', methods=['GET'])
def get_user_info():
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('SELECT id, username FROM users WHERE logged_in = 1')
        user = c.fetchone()
        if user is None:
            return jsonify({'username': 'MD', 'id': 'MD'})
        else:
            user_id, username = user
            return jsonify({'username': username, 'id': id})

@app.route('/appointment', methods=['POST'])
def appointment():
    data = request.get_json()
    name = data.get('name')
    specialization = data.get('specialization')
    time = data.get('time')
    doctor_id = data.get('doctor_id')  
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('SELECT id, username FROM users WHERE username = ?', (data.get('username'),))
        user = c.fetchone()
        if user is None:
            username = 'MD'
            user_id = 'MD'
        else:
            user_id, username = user

       
        c.execute('SELECT username FROM users WHERE id = ?', (doctor_id,))
        fetch_result = c.fetchone()
        if fetch_result is None:
            return jsonify({'message': 'Врач с таким идентификатором не найден.'}), 400
        else:
            doctor = fetch_result[0]

        
        c.execute('SELECT * FROM appointments WHERE time = ? AND doctor_id = ?', (time, doctor_id))
        if c.fetchone() is not None:
            return '', 204  

        c.execute('INSERT INTO appointments (name, specialization, time, doctor, username, id, doctor_id) VALUES (?, ?, ?, ?, ?, ?, ?)', (name, specialization, time, doctor, username, user_id, doctor_id))
        conn.commit()

    return jsonify({'message': 'Талон создан! Не забудьте прийти в указанное время к указанному врачу.'}), 200


@app.route('/view_appointments', methods=['POST'])
def view_appointments():
    data = request.get_json()
    username = data.get('username')

    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        doctor_id = c.fetchone()[0]

       
        c.execute('SELECT * FROM appointments WHERE doctor_id = ?', (doctor_id,))
        appointments = c.fetchall()

    
    appointments_list = [{'id': appointment[5], 'name': appointment[0], 'specialization': appointment[1], 'time': appointment[2]} for appointment in appointments]

    return jsonify({'appointments': appointments_list}), 200

@app.route('/finish_appointment', methods=['POST'])
def finish_appointment():
    data = request.get_json()
    appointment_id = data.get('appointment_id')

    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        
        c.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
        conn.commit()

    return jsonify({'message': 'Прием завершен.'}), 200

@app.route('/get_appointments1', methods=['POST'])
def get_appointments1():
    data = request.get_json()
    username = data.get('username')

    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM appointments WHERE username = ?', (username,))
        appointments = c.fetchall()

    return jsonify({'appointments': appointments})


@app.route('/register_appointment', methods=['POST'])
def register_appointment():
    data = request.get_json()
    name = data.get('name')

    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('INSERT INTO appointments (name) VALUES (?)', (name,))
        conn.commit()

    return jsonify({'message': 'Талон создан! Не забудьте прийти в указанное время.'}), 200

@app.route('/bookedTimes/<doctor_id>', methods=['GET'])
def get_booked_times(doctor_id):
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('SELECT time FROM appointments WHERE doctor_id = ?', (doctor_id,))
        booked_times = [row[0] for row in c.fetchall()]
    return jsonify(booked_times), 200


@app.route('/get_appointments', methods=['GET'])
def get_appointments():
    id = request.args.get('id')

    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('SELECT specialization, doctor, time, name FROM appointments WHERE id = ?', (user_id,))
        appointments = c.fetchall()

    return jsonify({'appointments': appointments}), 200


if __name__ == '__main__':
    create_table()
    app.run(host="0.0.0.0", debug = False)

