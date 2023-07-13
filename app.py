from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = r'D:\NIUM Internship\Elibrary - Test\uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xls'}
app.secret_key = 'your_secret_key'  # Replace with your own secret key

# PostgreSQL database configuration
app.config['DB_HOST'] = 'localhost'
app.config['DB_PORT'] = 5432
app.config['DB_NAME'] = 'postgres'
app.config['DB_USER'] = 'postgres'
app.config['DB_PASSWORD'] = 'admin'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_uploaded_files():
    files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(file_path):
            files.append(filename)
    return files

def get_db_connection():
    conn = psycopg2.connect(
        host=app.config['DB_HOST'],
        port=app.config['DB_PORT'],
        database=app.config['DB_NAME'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD']
    )
    return conn

def create_files_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS files (id SERIAL PRIMARY KEY, filename VARCHAR(256), uploaded_at TIMESTAMP)")
    conn.commit()
    cur.close()
    conn.close()

def insert_file_to_database(filename):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO files (filename, uploaded_at) VALUES (%s, %s)", (filename, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

def delete_file_from_database(filename):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM files WHERE filename = %s", (filename,))
    conn.commit()
    cur.close()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    create_files_table()
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            insert_file_to_database(filename)
            flash('File uploaded successfully')
            return redirect(url_for('upload_file'))
    files = get_uploaded_files()
    return render_template('upload.html', files=files)

@app.route('/uploads/<filename>')
def view_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete/<filename>')
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        delete_file_from_database(filename)
        flash('File deleted successfully')
    return redirect(url_for('upload_file'))

if __name__ == '__main__':
    app.run(debug=True)
