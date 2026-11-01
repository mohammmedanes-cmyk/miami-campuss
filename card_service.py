import io
import base64
import qrcode

# Code 39 barcode encoding table (Industry standard for ID cards & student badges)
CODE39_PATTERNS = {
    '0': '000110100', '1': '100100001', '2': '001100001', '3': '101100000',
    '4': '000110001', '5': '100110000', '6': '001110000', '7': '000100101',
    '8': '100100100', '9': '001100100', 'A': '100001001', 'B': '001001001',
    'C': '101001000', 'D': '000011001', 'E': '100011000', 'F': '001011000',
    'G': '000001101', 'H': '100001100', 'I': '001001100', 'J': '000011100',
    'K': '100000011', 'L': '001000011', 'M': '101000010', 'N': '000010011',
    'O': '100010010', 'P': '001010010', 'Q': '000000111', 'R': '100000110',
    'S': '001000110', 'T': '000010110', 'U': '110000001', 'V': '011000001',
    'W': '111000000', 'X': '010010001', 'Y': '110010000', 'Z': '011010000',
    '-': '010000101', '.': '110000100', ' ': '011000100', '*': '010010100',
    '$': '010101000', '/': '010100010', '+': '010001010', '%': '000101010'
}

def generate_barcode_svg(code_text, height=36, narrow=1.6, wide=3.8):
    """
    Renders a crisp vector Code-39 Barcode in pure SVG.
    Scales cleanly without quality loss for high-resolution printing.
    """
    raw = '*' + str(code_text).strip().upper() + '*'
    bars = []
    x = 0.0
    for char in raw:
        pattern = CODE39_PATTERNS.get(char, CODE39_PATTERNS[' '])
        for idx, bit in enumerate(pattern):
            is_bar = (idx % 2 == 0)
            width = wide if bit == '1' else narrow
            if is_bar:
                bars.append(f'<rect x="{x:.1f}" y="0" width="{width:.1f}" height="{height}" fill="#0A192F" />')
            x += width
        x += narrow  # Inter-character spacing

    total_width = int(x + narrow)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_width} {height}" width="100%" height="{height}" preserveAspectRatio="none">{"".join(bars)}</svg>'
    return svg

def generate_qr_base64(url):
    """Generates a high-contrast QR code as a base64 Data URI."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0A192F", back_color="#FFFFFF")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64_str = base64.b64encode(buf.getvalue()).decode('ascii')
    return f"data:image/png;base64,{b64_str}"

def get_student_transcript(student):
    """
    Generates verified academic grade transcript records tailored to the student's major.
    """
    specialty = student.get('specialty', '')
    
    courses_map = {
        'Computer Science & IT': [
            {'code': 'CSC 101', 'title': 'Introduction to Computer Science & Python', 'credits': 4, 'grade': 'A', 'points': 4.0},
            {'code': 'CSC 210', 'title': 'Data Structures & Algorithms in C++', 'credits': 4, 'grade': 'A', 'points': 4.0},
            {'code': 'CSC 317', 'title': 'Computer Systems & Architecture', 'credits': 3, 'grade': 'A-', 'points': 3.7},
            {'code': 'CSC 340', 'title': 'Database Management Systems & SQL', 'credits': 3, 'grade': 'A', 'points': 4.0},
            {'code': 'CSC 421', 'title': 'Operating Systems & Concurrency', 'credits': 4, 'grade': 'A-', 'points': 3.7},
            {'code': 'CSC 470', 'title': 'Artificial Intelligence & Neural Networks', 'credits': 4, 'grade': 'A', 'points': 4.0},
        ],
        'Medicine & Healthcare': [
            {'code': 'MED 105', 'title': 'Human Anatomy & Clinical Embryology', 'credits': 5, 'grade': 'A', 'points': 4.0},
            {'code': 'MED 120', 'title': 'Medical Biochemistry & Molecular Genetics', 'credits': 4, 'grade': 'A', 'points': 4.0},
            {'code': 'MED 210', 'title': 'Systemic Physiology & Homeostasis', 'credits': 4, 'grade': 'A-', 'points': 3.7},
            {'code': 'MED 235', 'title': 'General Pathology & Disease Mechanisms', 'credits': 4, 'grade': 'B+', 'points': 3.3},
            {'code': 'MED 301', 'title': 'Medical Microbiology & Immunology', 'credits': 3, 'grade': 'A', 'points': 4.0},
            {'code': 'MED 340', 'title': 'Clinical Pharmacology & Therapeutics', 'credits': 4, 'grade': 'A', 'points': 4.0},
        ],
        'Business Administration & Management': [
            {'code': 'BUS 101', 'title': 'Financial Accounting & Managerial Reporting', 'credits': 3, 'grade': 'A', 'points': 4.0},
            {'code': 'BUS 205', 'title': 'Micro & Macro Economic Analysis', 'credits': 3, 'grade': 'A-', 'points': 3.7},
            {'code': 'BUS 240', 'title': 'Corporate Finance & Investment Portfolios', 'credits': 3, 'grade': 'A', 'points': 4.0},
            {'code': 'BUS 315', 'title': 'Strategic Marketing & Consumer Psychology', 'credits': 3, 'grade': 'A', 'points': 4.0},
            {'code': 'BUS 360', 'title': 'Global Supply Chain & Logistics', 'credits': 3, 'grade': 'B+', 'points': 3.3},
            {'code': 'BUS 450', 'title': 'Entrepreneurial Venture Development', 'credits': 4, 'grade': 'A', 'points': 4.0},
        ],
        'Mechanical Engineering': [
            {'code': 'ENG 102', 'title': 'Advanced Engineering Calculus & ODEs', 'credits': 4, 'grade': 'A', 'points': 4.0},
            {'code': 'ENG 201', 'title': 'Engineering Statics & Dynamics', 'credits': 4, 'grade': 'A-', 'points': 3.7},
            {'code': 'ENG 220', 'title': 'Thermodynamics & Energy Transfer', 'credits': 3, 'grade': 'B+', 'points': 3.3},
            {'code': 'ENG 315', 'title': 'Fluid Mechanics & Aerodynamics', 'credits': 3, 'grade': 'A', 'points': 4.0},
            {'code': 'ENG 350', 'title': 'Computer Aided Design (CAD) & FEA', 'credits': 3, 'grade': 'A', 'points': 4.0},
            {'code': 'ENG 440', 'title': 'Robotics & Autonomous Control Systems', 'credits': 4, 'grade': 'A', 'points': 4.0},
        ],
        'Law & International Relations': [
            {'code': 'LAW 101', 'title': 'Constitutional Law & Civil Liberties', 'credits': 4, 'grade': 'A', 'points': 4.0},
            {'code': 'LAW 210', 'title': 'Contract Law & Commercial Transactions', 'credits': 4, 'grade': 'A', 'points': 4.0},
            {'code': 'LAW 250', 'title': 'Criminal Law & Judicial Evidence', 'credits': 3, 'grade': 'A-', 'points': 3.7},
            {'code': 'LAW 320', 'title': 'Public International Law & Treaties', 'credits': 3, 'grade': 'A', 'points': 4.0},
            {'code': 'LAW 380', 'title': 'Appellate Oral Advocacy & Moot Court', 'credits': 3, 'grade': 'A', 'points': 4.0},
            {'code': 'LAW 430', 'title': 'International Trade & Arbitration', 'credits': 4, 'grade': 'A', 'points': 4.0},
        ]
    }

    # Fallback for other majors
    default_courses = [
        {'code': 'UNIV 101', 'title': f'Foundations of {specialty}', 'credits': 4, 'grade': 'A', 'points': 4.0},
        {'code': 'UNIV 205', 'title': 'Research Methodologies & Data Analysis', 'credits': 3, 'grade': 'A', 'points': 4.0},
        {'code': 'UNIV 240', 'title': 'Critical Reasoning & Seminar Discussions', 'credits': 3, 'grade': 'A-', 'points': 3.7},
        {'code': 'UNIV 310', 'title': f'Advanced Studies in {specialty}', 'credits': 4, 'grade': 'A', 'points': 4.0},
        {'code': 'UNIV 375', 'title': 'Applied Practicum & Field Case Studies', 'credits': 3, 'grade': 'A', 'points': 4.0},
        {'code': 'UNIV 490', 'title': 'Senior Honors Capstone Project', 'credits': 4, 'grade': 'A', 'points': 4.0},
    ]

    courses = courses_map.get(specialty, default_courses)
    total_credits = sum(c['credits'] for c in courses)
    total_points = sum(c['credits'] * c['points'] for c in courses)
    gpa = round(total_points / total_credits, 2)

    return {
        'academic_year': '2025 - 2026',
        'semester': 'Spring Semester (Final)',
        'courses': courses,
        'total_credits': total_credits,
        'cumulative_gpa': f"{gpa:.2f}",
        'max_gpa': '4.00',
        'academic_standing': "Dean's Honors List &bull; Summa Cum Laude",
        'status': 'Officially Verified &bull; Active Enrolled',
        'registrar': 'Office of the University Registrar - Philadelphia Campus',
        'seal_code': f"REG-PC-{student.get('id', 1):04d}-VERIFIED"
    }
