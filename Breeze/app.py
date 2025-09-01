from flask import Flask, render_template, request, redirect, url_for, session
import os, json
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key-12345')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Naseem0811')

# Config
UPLOAD_FOLDER = os.path.join('static', 'uploads')
COVER_FOLDER = os.path.join(UPLOAD_FOLDER, 'covers')
DATA_FILE = "items.json"
COVERS_FILE = "covers.json"

# Ensure folders exist
os.makedirs(COVER_FOLDER, exist_ok=True)

# Helper functions
def load_json(filename, default=None):
    try:
        if os.path.exists(filename):
            with open(filename) as f:
                return json.load(f)
    except:
        pass
    return default if default else {}

def save_json(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except:
        return False

def load_data():
    sections = ["kurtis", "suits", "corsets", "dress_material", "hijabs"]
    return load_json(DATA_FILE, {sec: {"cover": "", "items": []} for sec in sections})

def load_covers():
    return load_json(COVERS_FILE, {})

def get_unique_filename(filename):
    if not filename: return ""
    name, ext = os.path.splitext(secure_filename(filename))
    return f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{ext}"

# Routes
@app.route('/')
def index():
    return render_template('index.html', items=load_data(), covers=load_covers())

@app.route('/section/<section_name>')
def section_page(section_name):
    data = load_data()
    return render_template('section.html', section_name=section_name, items=data.get(section_name, {}).get("items", []))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        return render_template('admin_login.html', error='Invalid password')
    return render_template('admin_login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    data, covers = load_data(), load_covers()
    
    if request.method == 'POST':
        section = request.form['section']
        
        # Handle cover image
        cover = request.files.get('cover')
        if cover and cover.filename:
            cover_filename = get_unique_filename(cover.filename)
            cover.save(os.path.join(COVER_FOLDER, cover_filename))
            covers[section] = data[section]["cover"] = cover_filename
            save_json(COVERS_FILE, covers)
        
        # Handle products
        fabricnames = request.form.getlist('fabricname[]')
        for i, fabricname in enumerate(fabricnames):
            image_file = ""
            if i < len(request.files.getlist('images[]')) and request.files.getlist('images[]')[i].filename:
                image_file = get_unique_filename(request.files.getlist('images[]')[i].filename)
                request.files.getlist('images[]')[i].save(os.path.join(UPLOAD_FOLDER, image_file))
            
            data[section]["items"].append({
                "fabricname": fabricname,
                "color": request.form.getlist('color[]')[i],
                "size": request.form.getlist('size[]')[i],
                "price": request.form.getlist('price[]')[i],
                "image": image_file
            })
        
        save_json(DATA_FILE, data)
        return redirect(url_for('admin'))
    
    return render_template('admin.html', items=data, covers=covers)

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/delete/<section>/<int:index>')
def delete_item(section, index):
    data = load_data()
    if section in data and 0 <= index < len(data[section]["items"]):
        data[section]["items"].pop(index)
        save_json(DATA_FILE, data)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
