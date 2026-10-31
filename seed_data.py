import sqlite3
from werkzeug.security import generate_password_hash
from database import DATABASE, init_db

SAMPLE_USERS = [
    {
        "full_name": "Sarah Mansouri",
        "email": "sarah.m@student.philadelphia.edu",
        "password": "password123",
        "specialty": "Computer Science & IT",
        "country": "Algeria",
        "bio": "Junior CS student at Philadelphia Campus. Working on artificial intelligence, distributed systems, and campus hackathons.",
        "avatar_color": "#1E3A8A"  # Navy Blue
    },
    {
        "full_name": "Lucas Dubois",
        "email": "lucas.d@student.philadelphia.edu",
        "password": "password123",
        "specialty": "Medicine & Healthcare",
        "country": "France",
        "bio": "Pre-med student at Philadelphia Campus researching clinical diagnostics and human anatomy.",
        "avatar_color": "#DC2626"  # Crimson Red
    },
    {
        "full_name": "Amina El-Sayed",
        "email": "amina.e@student.philadelphia.edu",
        "password": "password123",
        "specialty": "Business Administration & Management",
        "country": "Egypt",
        "bio": "Senior business student at Philadelphia Campus. Lead coordinator at the campus entrepreneurship incubator.",
        "avatar_color": "#B91C1C"  # Dark Red
    },
    {
        "full_name": "Marcus Vance",
        "email": "marcus.v@student.philadelphia.edu",
        "password": "password123",
        "specialty": "Mechanical Engineering",
        "country": "United States",
        "bio": "Philadelphia Campus engineering senior. President of the University Robotics & Autonomous Vehicles Society.",
        "avatar_color": "#2563EB"  # Royal Blue
    },
    {
        "full_name": "Elena Weber",
        "email": "elena.w@student.philadelphia.edu",
        "password": "password123",
        "specialty": "Law & International Relations",
        "country": "Germany",
        "bio": "Exchange student at Philadelphia Campus focusing on constitutional law and international trade regulation.",
        "avatar_color": "#172554"  # Deep Navy
    },
    {
        "full_name": "Omar Kaci",
        "email": "omar.k@student.philadelphia.edu",
        "password": "password123",
        "specialty": "Computer Science & IT",
        "country": "Algeria",
        "bio": "Sophomore CS student passionate about mobile development, algorithms, and cloud infrastructure.",
        "avatar_color": "#1D4ED8"
    }
]

SAMPLE_POSTS = [
    {
        "user_index": 0,  # Sarah Mansouri (CS, Algeria)
        "title": "Philadelphia Campus Midterm Revision: Algorithm Analysis & Dynamic Programming study group",
        "content": "Hey everyone! For the upcoming CS 317 exam next Thursday, we have booked study room 304 in Van Pelt Library on Wednesday from 4 PM to 7 PM. We'll be reviewing graph traversal algorithms, Bellman-Ford, and dynamic programming memoization. All Philadelphia Campus CS students are welcome to drop by!",
        "specialty": "Computer Science & IT"
    },
    {
        "user_index": 5,  # Omar Kaci (CS, Algeria)
        "title": "Best IDE setup and debugging tools for Operating Systems (CS 421)",
        "content": "Hello fellow CS classmates! What debugger or Linux environment are you using for the multi-threading and semaphore assignment? Looking for recommendations between VS Code Remote SSH and CLion.",
        "specialty": "Computer Science & IT"
    },
    {
        "user_index": 1,  # Lucas Dubois (Medicine, France)
        "title": "Clinical Anatomy flashcards and clinical case discussions for Term 2",
        "content": "Hi fellow pre-med and healthcare students! We've compiled high-yield visual notes for cardiovascular pathology and organ systems. If anyone wants to cross-verify answers for Dr. Miller's weekly lab assignment, let's share notes here.",
        "specialty": "Medicine & Healthcare"
    },
    {
        "user_index": 2,  # Amina El-Sayed (Business, Egypt)
        "title": "Philadelphia Campus Venture Challenge 2026 - Looking for team members!",
        "content": "The annual Philadelphia Campus Venture Challenge submissions open in 3 weeks. Our team is developing an intelligent student notes sharing and peer tutoring app. We are looking for business and marketing students to collaborate on the pitch deck.",
        "specialty": "Business Administration & Management"
    },
    {
        "user_index": 3,  # Marcus Vance (Engineering, USA)
        "title": "3D Printers access in the Engineering Innovation Lab over the weekend",
        "content": "Quick reminder for mechanical engineering students: the makerspace in Towne Hall will have extended open hours this Saturday from 10 AM to 6 PM for capstone project prototyping. Make sure to bring your STL files pre-sliced.",
        "specialty": "Mechanical Engineering"
    },
    {
        "user_index": 4,  # Elena Weber (Law, Germany)
        "title": "Constitutional Law & International Moot Court competition prep",
        "content": "For our constitutional and international law seminar, we are staging a mock appellate hearing next month. Law students who want to practice oral arguments and treaty citations, let's form a practice bench!",
        "specialty": "Law & International Relations"
    }
]

SAMPLE_COMMENTS = [
    {
        "post_index": 0,
        "user_index": 5,  # Omar replies to Sarah (both CS)
        "content": "I'll definitely be there Sarah! I have some practice problems on Dijkstra and Bellman-Ford that we can solve together."
    },
    {
        "post_index": 0,
        "user_index": 0,
        "content": "Awesome Omar! Bring those along, that will be super helpful for everyone in our CS class."
    },
    {
        "post_index": 1,
        "user_index": 0,
        "content": "I recommend VS Code Remote SSH with the GDB debugging extension. Works smoothly with campus lab servers!"
    }
]

def seed_database():
    print("Initializing Philadelphia Campus private database...")
    init_db()
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    user_ids = []
    print("Creating verified Philadelphia Campus student accounts...")
    for user in SAMPLE_USERS:
        pwd_hash = generate_password_hash(user["password"])
        cursor.execute(
            """INSERT INTO users (full_name, email, password_hash, specialty, country, bio, avatar_color)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user["full_name"], user["email"], pwd_hash, user["specialty"], user["country"], user["bio"], user["avatar_color"])
        )
        user_ids.append(cursor.lastrowid)

    post_ids = []
    print("Creating Philadelphia Campus specialty discussions...")
    for post in SAMPLE_POSTS:
        author_id = user_ids[post["user_index"]]
        cursor.execute(
            """INSERT INTO posts (user_id, title, content, specialty)
               VALUES (?, ?, ?, ?)""",
            (author_id, post["title"], post["content"], post["specialty"])
        )
        post_ids.append(cursor.lastrowid)

    print("Adding student replies...")
    for comment in SAMPLE_COMMENTS:
        post_id = post_ids[comment["post_index"]]
        author_id = user_ids[comment["user_index"]]
        cursor.execute(
            """INSERT INTO comments (post_id, user_id, content)
               VALUES (?, ?, ?)""",
            (post_id, author_id, comment["content"])
        )

    # Add sample likes
    cursor.execute("INSERT OR IGNORE INTO likes (user_id, post_id) VALUES (?, ?)", (user_ids[5], post_ids[0]))
    cursor.execute("INSERT OR IGNORE INTO likes (user_id, post_id) VALUES (?, ?)", (user_ids[0], post_ids[1]))

    conn.commit()
    conn.close()
    print("Philadelphia Campus private database seeded successfully!")

if __name__ == '__main__':
    seed_database()
