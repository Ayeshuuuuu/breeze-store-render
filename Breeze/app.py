rom flask import Flask, render_template, request, redirect, url_for, session
import os, json
from werkzeug.utils import secure_filename
from datetime import datetime
# ------------------ Flask App Configuration ------------------
app = Flask(__name__)
app.secret_key = 'naseem breeze store 1234'  # For session handling
ADMIN_PASSWORD = 'Naseem0811'  # Admin password
# Folders for uploads
UPLOAD_FOLDER = os.path.join('static', 'uploads')
COVER_FOLDER = os.path.join(UPLOAD_FOLDER, 'covers')
# Create folders if they don't exist
os.makedirs(COVER_FOLDER, exist_ok=True)
app.config.update(UPLOAD_FOLDER=UPLOAD_FOLDER, COVER_FOLDER=COVER_FOLDER)
# Data files
DATA_FILE = "items.json"
COVERS_FILE = "covers.json"
# ------------------ Helper Functions ------------------
# Load items data or initialize default structure
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    sections = ["kurtis", "suits", "corsets", "dress_material", "hijabs"]
    return {sec: {"cover": "", "items": []} for sec in sections}
# Save items data
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
# Load covers or initialize
def load_covers():
    if os.path.exists(COVERS_FILE):
        with open(COVERS_FILE) as f:
            return json.load(f)
    return {sec: "" for sec in load_data().keys()}
# Save covers
def save_covers(covers):
    with open(COVERS_FILE, 'w') as f:
        json.dump(covers, f, indent=4)
# Generate unique filenames to avoid overwriting
def get_unique_filename(filename):
    if not filename:
        return ""
    name, ext = os.path.splitext(secure_filename(filename))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{name}_{timestamp}{ext}"
# ------------------ Routes ------------------
# Home Page
@app.route('/')
def index():
    return render_template('index.html', items=load_data(), covers=load_covers())
# Section Page
@app.route('/section/<section_name>')
def section_page(section_name):
    data = load_data()
    return render_template('section.html', section_name=section_name, items=data.get(section_name, {}).get("items", []))
# Admin Login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        return render_template('admin_login.html', error='Invalid password')
    return render_template('admin_login.html')
# Admin Dashboard
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    data, covers = load_data(), load_covers()
    if request.method == 'POST':
        section = request.form['section']
        # Handle cover image upload
        cover = request.files.get('cover')
        if cover and cover.filename:
            old_cover = covers.get(section)
            if old_cover:
                old_path = os.path.join(COVER_FOLDER, old_cover)
                if os.path.exists(old_path): os.remove(old_path)

            cover_filename = get_unique_filename(cover.filename)
            cover.save(os.path.join(COVER_FOLDER, cover_filename))
            covers[section] = data[section]["cover"] = cover_filename
            save_covers(covers)
        # Handle product details
        fabricnames = request.form.getlist('fabricname[]')
        colors = request.form.getlist('color[]')
        sizes = request.form.getlist('size[]')
        prices = request.form.getlist('price[]')
        images = request.files.getlist('images[]')
        # Validate equal counts
        if not all(len(lst) == len(fabricnames) for lst in [colors, sizes, prices]):
            return "Error: Form data mismatch", 400
        # Add new items
        for i in range(len(fabricnames)):
            image_file = ""
            if i < len(images) and images[i].filename:
                image_file = get_unique_filename(images[i].filename)
                images[i].save(os.path.join(UPLOAD_FOLDER, image_file))

            data[section]["items"].append({
                "fabricname": fabricnames[i],
                "color": colors[i],
                "size": sizes[i],
                "price": prices[i],
                "image": image_file
            })
        save_data(data)
        return redirect(url_for('admin'))
    return render_template('admin.html', items=data, covers=covers)
# Admin Logout
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))
# Delete Item
@app.route('/delete/<section>/<int:index>')
def delete_item(section, index):
    data = load_data()
    if section in data and 0 <= index < len(data[section]["items"]):
        item = data[section]["items"].pop(index)
        if item["image"]:
            path = os.path.join(UPLOAD_FOLDER, item["image"])
            if os.path.exists(path): os.remove(path)
        save_data(data)
    return redirect(url_for('admin'))
# Delete Entire Section
@app.route('/delete_section/<section>', methods=['POST'])
def delete_section(section):
    data, covers = load_data(), load_covers()
    # Delete all images in the section
    for item in data.get(section, {}).get("items", []):
        if item.get("image"):
            path = os.path.join(UPLOAD_FOLDER, item["image"])
            if os.path.exists(path): os.remove(path)
    # Delete cover image
    cover = covers.get(section)
    if cover:
        path = os.path.join(COVER_FOLDER, cover)
        if os.path.exists(path): os.remove(path)
    # Remove section from data and covers
    data.pop(section, None)
    covers.pop(section, None)
    save_data(data)
    save_covers(covers)
    return redirect(url_for('admin'))
# Add New Section
@app.route('/add_section', methods=['POST'])
def add_section():
    data, covers = load_data(), load_covers()
    new_section = request.form['new_section'].strip()
    if new_section and new_section not in data:
        data[new_section] = {"cover": "", "items": []}
        covers[new_section] = ""
        save_data(data)
        save_covers(covers)
    return redirect(url_for('admin'))
# Run App
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
