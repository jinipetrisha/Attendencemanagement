from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import csv

app = Flask(__name__)
app.secret_key = 'secret123'

# ------------------------- Helper Function -------------------------
def check_student(name, password):
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE name=? AND password=?", (name, password))
    student = cursor.fetchone()
    conn.close()
    return student

# ------------------------- Routes -------------------------
@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        if role == 'student':
            return redirect(url_for('student_login'))
        elif role == 'teacher':
            return redirect(url_for('teacher_login'))
    return render_template('login.html')

# ------------------------- Student Login -------------------------
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        if check_student(name, password):
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password!')
            return redirect(url_for('student_login'))
    return render_template('student_login.html')

# ------------------------- Forgot Password -------------------------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        with open('students.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Name'].strip() == name and row['Email'].strip() == email:
                    password = row['Password']
                    flash(f"Your password is: {password}", 'info')  # For now, showing directly
                    return redirect(url_for('student_login'))

        flash('Name and email do not match our records.', 'error')
        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

# ------------------------- Register Page -------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

# ------------------------- Dashboards -------------------------
@app.route('/student_dashboard')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/teacher_dashboard')
def teacher_dashboard():
    return render_template('teacher_dashboard.html')

@app.route('/dashboard/subject_teacher')
def subject_teacher_dashboard():
    return render_template('subject_teacher_dashboard.html')

@app.route('/dashboard/class_teacher')
def class_teacher_dashboard():
    return render_template('class_teacher_dashboard.html')

# ------------------------- Teacher Login -------------------------
@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        role_type = request.form.get('teacher_type')
        username = request.form['username']
        password = request.form['password']

        # Simple logic, you can later use DB or CSV
        if role_type == 'subject' and username == 'subject1' and password == 'sub123':
            return redirect(url_for('subject_teacher_dashboard'))
        elif role_type == 'class' and username == 'class1' and password == 'cls123':
            return redirect(url_for('class_teacher_dashboard'))
        else:
            flash('Invalid teacher credentials!')
            return redirect(url_for('teacher_login'))

    return render_template('teacher_login.html')

# ------------------------- Run App -------------------------
if __name__ == '__main__':
    app.run(debug=True)
