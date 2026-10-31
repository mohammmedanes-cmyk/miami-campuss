import os
import socket
import functools
import io
import qrcode
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g, jsonify, abort, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, close_db, init_db, db_exists, db_has_tables

app = Flask(__name__)
app.config['SECRET_KEY'] = 'miami-campus-secure-student-portal-2026'
app.teardown_appcontext(close_db)

APP_NAME = "Miami Campus"

POPULAR_SPECIALTIES = [
    "Computer Science & IT",
    "Software Engineering",
    "Artificial Intelligence & Data Science",
    "Medicine & Healthcare",
    "Pharmacy & Biomedical Science",
    "Electrical Engineering",
    "Mechanical Engineering",
    "Civil & Architectural Engineering",
    "Business Administration & Management",
    "Finance & Economics",
    "Law & International Studies",
    "Biology & Marine Science",
    "Chemistry & Biochemistry",
    "Physics & Applied Mathematics",
    "Psychology & Neuroscience",
    "Communications & Journalism",
    "Graphic Design & Interactive Media"
]

POPULAR_COUNTRIES = [
    "United States", "Algeria", "France", "Egypt", "Morocco", 
    "Canada", "Germany", "United Kingdom", "Spain", "Italy",
    "Tunisia", "Saudi Arabia", "United Arab Emirates", "Jordan", "Lebanon",
    "Turkey", "India", "Pakistan", "Brazil", "Mexico",
    "Nigeria", "South Africa", "Japan", "South Korea", "Australia"
]

# University Red & Blue themed avatar palette
AVATAR_COLORS = [
    "#1E3A8A",  # Dark Navy Blue
    "#DC2626",  # Crimson Red
    "#2563EB",  # Royal Blue
    "#991B1B",  # Deep Burgundy Red
    "#1D4ED8",  # Bold Blue
    "#B91C1C",  # University Scarlet
    "#0F172A",  # Midnight Blue
    "#EF4444"   # Bright Red
]


# -------------------------------------------------------------
# Embedded Self-Healing Assets (Templates & Static files)
# Ensures templates work immediately on Render even if folders were not uploaded
# -------------------------------------------------------------
ASSETS_ZIP_B64 = "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"

def ensure_templates_and_static():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tpl_file = os.path.join(base_dir, 'templates', 'base.html')
    if not os.path.exists(tpl_file):
        try:
            print("[*] Cloud environment detected missing templates. Unpacking bundled templates & static assets...")
            import base64, zipfile, io
            raw = base64.b64decode(ASSETS_ZIP_B64)
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                z.extractall(base_dir)
            print("[*] Successfully restored all templates and static assets!")
        except Exception as err:
            print(f"[!] Could not unpack bundled assets: {err}")

ensure_templates_and_static()

def ensure_db_initialized():
    """Guarantees database and tables exist even when deployed to ephemeral cloud (Render/Gunicorn)."""
    if not db_has_tables():
        try:
            from seed_data import seed_database
            print("[*] Database tables missing. Auto-initializing Miami Campus database...")
            seed_database()
        except Exception as e:
            print(f"[!] Error seeding database: {e}")

# Run immediately when app.py is loaded by any WSGI server (Gunicorn, Waitress, Flask)
ensure_db_initialized()

def get_network_ip():
    """Finds the local LAN IP of this computer on the university network/Wi-Fi."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def is_university_email(email):
    """
    Validates that the email belongs to the Miami Campus university network.
    Accepts @miami.edu, @student.miami.edu, @miamioh.edu, @campus.miami.edu, or test @univ.edu
    """
    if '@' not in email:
        return False
    domain = email.split('@')[-1].lower()
    allowed_domains = ('miami.edu', 'student.miami.edu', 'miamioh.edu', 'campus.miami.edu', 'univ.edu')
    return any(domain == d or domain.endswith('.' + d) for d in allowed_domains)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            if request.is_json:
                return jsonify({'error': 'Unauthorized. Please sign in.'}), 401
            flash("Miami Campus is private. Please sign in with your student account to view this content.", "info")
            return redirect(url_for('login', next=request.path))
        return view(**kwargs)
    return wrapped_view

@app.before_request
def load_logged_in_user():
    ensure_db_initialized()
    user_id = session.get('user_id')
    client_user_id = request.headers.get('X-Student-Id')
    if not user_id and client_user_id and client_user_id.isdigit():
        user_id = int(client_user_id)

    if user_id is None:
        g.user = None
    else:
        try:
            db = get_db()
            g.user = db.execute(
                "SELECT id, full_name, email, specialty, country, bio, avatar_color, created_at FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
        except Exception:
            g.user = None

@app.context_processor
def inject_globals():
    lan_ip = get_network_ip()
    host_url = request.host_url.rstrip('/')
    if 'onrender.com' in host_url or not host_url.startswith('http://127.0.0.1'):
        current_mobile_url = host_url
    else:
        current_mobile_url = f"http://{lan_ip}:5000"

    return {
        'app_name': APP_NAME,
        'popular_specialties': POPULAR_SPECIALTIES,
        'popular_countries': POPULAR_COUNTRIES,
        'lan_ip': lan_ip,
        'mobile_url': current_mobile_url
    }

# -------------------------------------------------------------
# Mobile QR Code Endpoint (Instant Phone Connection)
# -------------------------------------------------------------

@app.route('/qr.png')
def qr_image():
    """Generates an instant offline QR Code PNG for phone cameras to scan."""
    host_url = request.host_url.rstrip('/')
    if 'onrender.com' in host_url or not host_url.startswith('http://127.0.0.1'):
        target_url = host_url
    else:
        lan_ip = get_network_ip()
        target_url = f"http://{lan_ip}:5000"
    img = qrcode.make(target_url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/mobile')
def mobile_page():
    """Direct mobile instructions and QR code page."""
    host_url = request.host_url.rstrip('/')
    if 'onrender.com' in host_url or not host_url.startswith('http://127.0.0.1'):
        target_url = host_url
    else:
        lan_ip = get_network_ip()
        target_url = f"http://{lan_ip}:5000"
    return render_template('mobile.html', mobile_url=target_url, lan_ip=get_network_ip())

# -------------------------------------------------------------
# Authentication Routes (Private Campus)
# -------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        specialty = request.form.get('specialty', '').strip()
        custom_specialty = request.form.get('custom_specialty', '').strip()
        country = request.form.get('country', '').strip()
        custom_country = request.form.get('custom_country', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        bio = request.form.get('bio', '').strip()

        if specialty == "Other" and custom_specialty:
            specialty = custom_specialty
        if country == "Other" and custom_country:
            country = custom_country

        error = None

        if not full_name:
            error = "Full Name is required."
        elif not specialty:
            error = "Specialty / Academic Major is required."
        elif not country:
            error = "Country is required."
        elif not email:
            error = "University email is required."
        elif not is_university_email(email):
            error = "This platform is private to our university. Please use your official Miami Campus email (e.g. name@student.miami.edu or @miami.edu)."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        elif password != confirm_password:
            error = "Passwords do not match."

        db = get_db()
        if error is None:
            existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                error = f"An account with university email '{email}' already exists. Please sign in."

        if error is None:
            color_index = len(full_name) % len(AVATAR_COLORS)
            avatar_color = AVATAR_COLORS[color_index]
            pwd_hash = generate_password_hash(password)

            cursor = db.execute(
                """INSERT INTO users (full_name, email, password_hash, specialty, country, bio, avatar_color)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (full_name, email, pwd_hash, specialty, country, bio, avatar_color)
            )
            db.commit()
            session.clear()
            session['user_id'] = cursor.lastrowid
            flash(f"Welcome to Miami Campus, {full_name}! You are registered in the '{specialty}' department.", "success")
            return redirect(url_for('index'))

        flash(error, "error")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        error = None

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user is None:
            error = "No student account found with this university email."
        elif not check_password_hash(user['password_hash'], password):
            error = "Incorrect password. Please try again."

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            flash(f"Welcome back to Miami Campus, {user['full_name']}! Viewing '{user['specialty']}' discussions.", "success")
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))

        flash(error, "error")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have safely signed out of Miami Campus.", "info")
    return redirect(url_for('login'))

# -------------------------------------------------------------
# Discussion & Feed Routes (STRICT SPECIALTY ISOLATION)
# -------------------------------------------------------------

@app.route('/')
def index():
    db = get_db()

    # Unauthenticated visitors see the Private Campus Gateway
    if not g.user:
        total_students = db.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
        total_posts = db.execute("SELECT COUNT(*) as count FROM posts").fetchone()['count']
        return render_template(
            'index.html',
            is_guest=True,
            total_students=total_students,
            total_posts=total_posts
        )

    # ---------------------------------------------------------
    # RULE: Students can ONLY see discussions from their specialty!
    # ---------------------------------------------------------
    student_specialty = g.user['specialty']
    current_country = request.args.get('country', '').strip()
    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'latest')

    query = """
        SELECT p.id, p.title, p.content, p.specialty, p.created_at,
               u.id as user_id, u.full_name, u.specialty as user_specialty,
               u.country, u.avatar_color,
               COUNT(DISTINCT c.id) as comment_count,
               COUNT(DISTINCT l.id) as like_count,
               EXISTS(SELECT 1 FROM likes WHERE post_id = p.id AND user_id = ?) as user_has_liked
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN comments c ON c.post_id = p.id
        LEFT JOIN likes l ON l.post_id = p.id
        WHERE p.specialty = ?
    """
    params = [g.user['id'], student_specialty]

    if current_country:
        query += " AND u.country = ?"
        params.append(current_country)

    if search_query:
        query += " AND (p.title LIKE ? OR p.content LIKE ? OR u.full_name LIKE ?)"
        like_pattern = f"%{search_query}%"
        params.extend([like_pattern, like_pattern, like_pattern])

    query += " GROUP BY p.id"

    if sort_by == 'popular':
        query += " ORDER BY like_count DESC, p.created_at DESC"
    elif sort_by == 'discussed':
        query += " ORDER BY comment_count DESC, p.created_at DESC"
    else:
        query += " ORDER BY p.created_at DESC"

    posts = db.execute(query, params).fetchall()

    peer_countries = db.execute("""
        SELECT country, COUNT(*) as count
        FROM users
        WHERE specialty = ?
        GROUP BY country
        ORDER BY count DESC
    """, (student_specialty,)).fetchall()

    total_specialty_students = db.execute(
        "SELECT COUNT(*) as count FROM users WHERE specialty = ?",
        (student_specialty,)
    ).fetchone()['count']

    total_specialty_posts = db.execute(
        "SELECT COUNT(*) as count FROM posts WHERE specialty = ?",
        (student_specialty,)
    ).fetchone()['count']

    return render_template(
        'index.html',
        is_guest=False,
        posts=posts,
        student_specialty=student_specialty,
        current_country=current_country,
        search_query=search_query,
        sort_by=sort_by,
        peer_countries=peer_countries,
        total_specialty_students=total_specialty_students,
        total_specialty_posts=total_specialty_posts
    )

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    student_specialty = g.user['specialty']

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        error = None
        if not title:
            error = "Discussion title is required."
        elif not content:
            error = "Discussion content cannot be empty."

        if error:
            flash(error, "error")
        else:
            db = get_db()
            cursor = db.execute(
                """INSERT INTO posts (user_id, title, content, specialty)
                   VALUES (?, ?, ?, ?)""",
                (g.user['id'], title, content, student_specialty)
            )
            db.commit()
            flash(f"Your discussion was posted to the {student_specialty} department feed!", "success")
            return redirect(url_for('post_detail', post_id=cursor.lastrowid))

    return render_template('new_post.html', student_specialty=student_specialty)

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def post_detail(post_id):
    db = get_db()

    user_id = g.user['id']
    post = db.execute("""
        SELECT p.id, p.title, p.content, p.specialty, p.created_at,
               u.id as user_id, u.full_name, u.specialty as user_specialty,
               u.country, u.avatar_color, u.bio,
               COUNT(DISTINCT l.id) as like_count,
               EXISTS(SELECT 1 FROM likes WHERE post_id = p.id AND user_id = ?) as user_has_liked
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN likes l ON l.post_id = p.id
        WHERE p.id = ?
        GROUP BY p.id
    """, (user_id, post_id)).fetchone()

    if post is None:
        abort(404)

    # ---------------------------------------------------------
    # RULE: Block student from viewing posts from other specialties
    # ---------------------------------------------------------
    if post['specialty'] != g.user['specialty']:
        flash(f"🔒 Access Restricted: This discussion belongs to '{post['specialty']}'. You are enrolled in '{g.user['specialty']}'.", "error")
        return redirect(url_for('index'))

    # Handle adding a reply
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if not content:
            flash("Reply cannot be empty.", "error")
        else:
            db.execute(
                """INSERT INTO comments (post_id, user_id, content)
                   VALUES (?, ?, ?)""",
                (post_id, g.user['id'], content)
            )
            db.commit()
            flash("Your response has been published!", "success")
            return redirect(url_for('post_detail', post_id=post_id))

    comments = db.execute("""
        SELECT c.id, c.content, c.created_at,
               u.id as user_id, u.full_name, u.specialty, u.country, u.avatar_color
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
    """, (post_id,)).fetchall()

    return render_template('post_detail.html', post=post, comments=comments)

@app.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def toggle_like(post_id):
    db = get_db()
    user_id = g.user['id']

    post = db.execute("SELECT specialty FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        abort(404)
    if post['specialty'] != g.user['specialty']:
        return jsonify({'error': 'Unauthorized to like posts outside your specialty'}), 403

    existing = db.execute(
        "SELECT id FROM likes WHERE user_id = ? AND post_id = ?",
        (user_id, post_id)
    ).fetchone()

    if existing:
        db.execute("DELETE FROM likes WHERE id = ?", (existing['id'],))
        liked = False
    else:
        db.execute(
            "INSERT INTO likes (user_id, post_id) VALUES (?, ?)",
            (user_id, post_id)
        )
        liked = True
    db.commit()

    like_count = db.execute(
        "SELECT COUNT(*) as count FROM likes WHERE post_id = ?",
        (post_id,)
    ).fetchone()['count']

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'liked': liked, 'like_count': like_count})

    return redirect(request.referrer or url_for('post_detail', post_id=post_id))

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    db = get_db()
    post = db.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        abort(404)

    if post['user_id'] != g.user['id']:
        abort(403)

    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
    flash("Discussion post has been removed.", "info")
    return redirect(url_for('index'))

# -------------------------------------------------------------
# Student Profile Routes (Private Campus)
# -------------------------------------------------------------

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    db = get_db()
    student = db.execute("""
        SELECT id, full_name, email, specialty, country, bio, avatar_color, created_at
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if student is None:
        abort(404)

    # RULE: Can view own profile or peers within the same specialty
    if student['id'] != g.user['id'] and student['specialty'] != g.user['specialty']:
        flash(f"🔒 Access Restricted: Student {student['full_name']} belongs to '{student['specialty']}'. You are in '{g.user['specialty']}'.", "error")
        return redirect(url_for('index'))

    posts = db.execute("""
        SELECT p.id, p.title, p.content, p.specialty, p.created_at,
               COUNT(DISTINCT c.id) as comment_count,
               COUNT(DISTINCT l.id) as like_count
        FROM posts p
        LEFT JOIN comments c ON c.post_id = p.id
        LEFT JOIN likes l ON l.post_id = p.id
        WHERE p.user_id = ?
        GROUP BY p.id
        ORDER BY p.created_at DESC
    """, (user_id,)).fetchall()

    comments_count = db.execute(
        "SELECT COUNT(*) as count FROM comments WHERE user_id = ?",
        (user_id,)
    ).fetchone()['count']

    total_likes_received = db.execute("""
        SELECT COUNT(l.id) as count
        FROM likes l
        JOIN posts p ON l.post_id = p.id
        WHERE p.user_id = ?
    """, (user_id,)).fetchone()['count']

    return render_template(
        'profile.html',
        student=student,
        posts=posts,
        comments_count=comments_count,
        total_likes_received=total_likes_received
    )

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    db = get_db()
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        country = request.form.get('country', '').strip()
        custom_country = request.form.get('custom_country', '').strip()
        bio = request.form.get('bio', '').strip()

        if country == "Other" and custom_country:
            country = custom_country

        error = None
        if not full_name:
            error = "Full Name cannot be empty."
        elif not country:
            error = "Country is required."

        if error:
            flash(error, "error")
        else:
            db.execute("""
                UPDATE users
                SET full_name = ?, country = ?, bio = ?
                WHERE id = ?
            """, (full_name, country, bio, g.user['id']))
            db.commit()
            flash("Your Miami Campus profile has been updated!", "success")
            return redirect(url_for('profile', user_id=g.user['id']))

    return render_template('edit_profile.html')

# -------------------------------------------------------------
# CLIENT-SERVER REST API (With Specialty Isolation)
# -------------------------------------------------------------

@app.route('/api/status', methods=['GET'])
def api_status():
    db = get_db()
    total_students = db.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
    total_posts = db.execute("SELECT COUNT(*) as count FROM posts").fetchone()['count']
    lan_ip = get_network_ip()
    return jsonify({
        'status': 'online',
        'server': 'Miami Campus Central Server',
        'architecture': 'Client-Server (خادم - زبون)',
        'network_access': f'http://{lan_ip}:5000',
        'specialty_isolation': 'Strict (Students see only their specialty)',
        'total_students': total_students,
        'total_discussions': total_posts,
        'accepted_domains': ['@miami.edu', '@student.miami.edu']
    })

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    specialty = data.get('specialty', '').strip()
    country = data.get('country', '').strip()
    password = data.get('password', '')
    bio = data.get('bio', '').strip()

    if not full_name or not specialty or not country or not email or not password:
        return jsonify({'success': False, 'error': 'Missing required fields (full_name, email, specialty, country, password)'}), 400

    if not is_university_email(email):
        return jsonify({'success': False, 'error': 'Private network. Only official Miami Campus emails (@student.miami.edu) are accepted.'}), 403

    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters.'}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        return jsonify({'success': False, 'error': 'An account with this email already exists.'}), 409

    color_index = len(full_name) % len(AVATAR_COLORS)
    avatar_color = AVATAR_COLORS[color_index]
    pwd_hash = generate_password_hash(password)

    cursor = db.execute(
        """INSERT INTO users (full_name, email, password_hash, specialty, country, bio, avatar_color)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (full_name, email, pwd_hash, specialty, country, bio, avatar_color)
    )
    db.commit()
    user_id = cursor.lastrowid
    return jsonify({
        'success': True,
        'message': f'Student account created for {full_name} in {specialty}',
        'student': {
            'id': user_id,
            'full_name': full_name,
            'email': email,
            'specialty': specialty,
            'country': country
        }
    }), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if user is None or not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'error': 'Invalid university email or password.'}), 401

    session['user_id'] = user['id']
    return jsonify({
        'success': True,
        'student': {
            'id': user['id'],
            'full_name': user['full_name'],
            'email': user['email'],
            'specialty': user['specialty'],
            'country': user['country']
        }
    })

@app.route('/api/discussions', methods=['GET', 'POST'])
def api_discussions():
    db = get_db()

    if not g.user:
        return jsonify({'success': False, 'error': 'Authentication required. Please sign in.'}), 401

    student_specialty = g.user['specialty']

    if request.method == 'POST':
        data = request.get_json() or {}
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()

        if not title or not content:
            return jsonify({'success': False, 'error': 'Title and content are required.'}), 400

        cursor = db.execute(
            """INSERT INTO posts (user_id, title, content, specialty)
               VALUES (?, ?, ?, ?)""",
            (g.user['id'], title, content, student_specialty)
        )
        db.commit()
        return jsonify({'success': True, 'post_id': cursor.lastrowid, 'specialty': student_specialty}), 201

    country_filter = request.args.get('country')
    query = """
        SELECT p.id, p.title, p.content, p.specialty, p.created_at,
               u.id as user_id, u.full_name, u.specialty as user_specialty, u.country,
               COUNT(DISTINCT c.id) as comment_count,
               COUNT(DISTINCT l.id) as like_count
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN comments c ON c.post_id = p.id
        LEFT JOIN likes l ON l.post_id = p.id
        WHERE p.specialty = ?
    """
    params = [student_specialty]
    if country_filter:
        query += " AND u.country = ?"
        params.append(country_filter)
    
    query += " GROUP BY p.id ORDER BY p.created_at DESC"
    rows = db.execute(query, params).fetchall()
    
    discussions = []
    for r in rows:
        discussions.append({
            'id': r['id'],
            'title': r['title'],
            'content': r['content'],
            'specialty': r['specialty'],
            'created_at': r['created_at'],
            'author': {
                'id': r['user_id'],
                'full_name': r['full_name'],
                'specialty': r['user_specialty'],
                'country': r['country']
            },
            'comment_count': r['comment_count'],
            'like_count': r['like_count']
        })
    return jsonify({
        'success': True,
        'specialty_channel': student_specialty,
        'count': len(discussions),
        'discussions': discussions
    })

@app.route('/api/discussions/<int:post_id>', methods=['GET'])
def api_discussion_detail(post_id):
    db = get_db()
    if not g.user:
        return jsonify({'success': False, 'error': 'Authentication required.'}), 401

    post = db.execute("""
        SELECT p.id, p.title, p.content, p.specialty, p.created_at,
               u.id as user_id, u.full_name, u.specialty as user_specialty, u.country
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = ?
    """, (post_id,)).fetchone()

    if not post:
        return jsonify({'success': False, 'error': 'Discussion not found'}), 404

    if post['specialty'] != g.user['specialty']:
        return jsonify({
            'success': False,
            'error': f'Access restricted: Post belongs to {post["specialty"]}. Your specialty is {g.user["specialty"]}.'
        }), 403

    comments = db.execute("""
        SELECT c.id, c.content, c.created_at,
               u.id as user_id, u.full_name, u.specialty, u.country
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
    """, (post_id,)).fetchall()

    return jsonify({
        'success': True,
        'discussion': {
            'id': post['id'],
            'title': post['title'],
            'content': post['content'],
            'specialty': post['specialty'],
            'created_at': post['created_at'],
            'author': {
                'id': post['user_id'],
                'full_name': post['full_name'],
                'specialty': post['user_specialty'],
                'country': post['country']
            },
            'replies': [
                {
                    'id': c['id'],
                    'content': c['content'],
                    'created_at': c['created_at'],
                    'author': {
                        'id': c['user_id'],
                        'full_name': c['full_name'],
                        'specialty': c['specialty'],
                        'country': c['country']
                    }
                } for c in comments
            ]
        }
    })

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    # Pass through HTTP exceptions (e.g. 404, 401)
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return e
    return f"""
    <div style="font-family:sans-serif; max-width:800px; margin:40px auto; padding:24px; background:#FEF2F2; color:#991B1B; border:2px solid #F87171; border-radius:12px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);">
        <h2 style="margin-top:0;">🏛️ Miami Campus - Server Diagnostic</h2>
        <p><b>Error:</b> {str(e)}</p>
        <pre style="background:#FFFFFF; color:#1F2937; padding:16px; border-radius:8px; overflow:auto; font-size:13px; border:1px solid #E5E7EB;">{traceback.format_exc()}</pre>
    </div>
    """, 500

# -------------------------------------------------------------
# Initialization & Entry point
# -------------------------------------------------------------

def start_server():
    ensure_db_initialized()

if __name__ == '__main__':
    start_server()
    lan_ip = get_network_ip()
    port = int(os.environ.get('PORT', 5000))
    print("=========================================================")
    print(" 🏛️  Miami Campus - Private University Discussion Portal  ")
    print(f" Local URL  : http://127.0.0.1:{port}                   ")
    print(f" Network URL: http://{lan_ip}:{port}                    ")
    print(" Red & Blue University Edition                           ")
    print("=========================================================")
    app.run(debug=True, port=port, host='0.0.0.0')
