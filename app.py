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
from database import get_db, close_db, init_db, db_exists

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
    user_id = session.get('user_id')
    client_user_id = request.headers.get('X-Student-Id')
    if not user_id and client_user_id and client_user_id.isdigit():
        user_id = int(client_user_id)

    if user_id is None:
        g.user = None
    else:
        db = get_db()
        g.user = db.execute(
            "SELECT id, full_name, email, specialty, country, bio, avatar_color, created_at FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

@app.context_processor
def inject_globals():
    lan_ip = get_network_ip()
    return {
        'app_name': APP_NAME,
        'popular_specialties': POPULAR_SPECIALTIES,
        'popular_countries': POPULAR_COUNTRIES,
        'lan_ip': lan_ip,
        'mobile_url': f"http://{lan_ip}:5000"
    }

# -------------------------------------------------------------
# Mobile QR Code Endpoint (Instant Phone Connection)
# -------------------------------------------------------------

@app.route('/qr.png')
def qr_image():
    """Generates an instant offline QR Code PNG for phone cameras to scan."""
    lan_ip = get_network_ip()
    mobile_url = f"http://{lan_ip}:5000"
    img = qrcode.make(mobile_url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/mobile')
def mobile_page():
    """Direct mobile instructions and QR code page."""
    lan_ip = get_network_ip()
    return render_template('mobile.html', mobile_url=f"http://{lan_ip}:5000", lan_ip=lan_ip)

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

    # Active countries of peers in the same specialty
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
    # Discussion is automatically restricted to student's registered specialty
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
            # Specialty is locked once registered to maintain strict department isolation
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

    # Client must be authenticated to interact with private specialty discussions
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

    # GET request: STRICTLY filtered to student's own specialty
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

    # Enforce specialty isolation
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

# -------------------------------------------------------------
# Initialization & Entry point
# -------------------------------------------------------------

def start_server():
    if not db_exists():
        from seed_data import seed_database
        print("Database not found. Initializing Miami Campus private portal...")
        seed_database()

if __name__ == '__main__':
    start_server()
    lan_ip = get_network_ip()
    print("=========================================================")
    print(" 🏛️  Miami Campus - Private University Discussion Portal  ")
    print(f" Local URL  : http://127.0.0.1:5000                     ")
    print(f" Network URL: http://{lan_ip}:5000                      ")
    print(" Red & Blue University Edition                           ")
    print("=========================================================")
    app.run(debug=True, port=5000, host='0.0.0.0')
