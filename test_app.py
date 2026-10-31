import os
import unittest
from app import app
from seed_data import seed_database

class MiamiCampusSpecialtyAndMobileTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize test database with Miami Campus sample data
        seed_database()

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_qr_code_image_endpoint(self):
        """Phone connection endpoint /qr.png delivers a valid PNG image"""
        response = self.client.get('/qr.png')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'image/png')
        self.assertGreater(len(response.data), 100)

    def test_02_mobile_page(self):
        """Mobile instructions page loads with QR code and instructions"""
        response = self.client.get('/mobile')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Connect from Your Phone', response.data)
        self.assertIn(b'/qr.png', response.data)

    def test_03_strict_specialty_isolation_feed(self):
        """
        Sarah (CS) only sees CS discussions; she does NOT see Medicine or Law discussions.
        """
        # Login as Sarah (Computer Science & IT)
        self.client.post('/login', data={
            'email': 'sarah.m@student.miami.edu',
            'password': 'password123'
        }, follow_redirects=True)

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Should see her own specialty discussions
        self.assertIn(b'Computer Science &amp; IT', response.data)
        self.assertIn(b'Algorithm Analysis', response.data)
        # MUST NOT see discussions from other specialties
        self.assertNotIn(b'Clinical Anatomy flashcards', response.data)
        self.assertNotIn(b'International Moot Court', response.data)

    def test_04_lucas_only_sees_medicine(self):
        """
        Lucas (Medicine) only sees Medicine discussions; he does NOT see Computer Science discussions.
        """
        # Login as Lucas (Medicine & Healthcare)
        self.client.post('/login', data={
            'email': 'lucas.d@student.miami.edu',
            'password': 'password123'
        }, follow_redirects=True)

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Should see Medicine discussions
        self.assertIn(b'Medicine &amp; Healthcare', response.data)
        self.assertIn(b'Clinical Anatomy flashcards', response.data)
        # MUST NOT see Computer Science discussions
        self.assertNotIn(b'Algorithm Analysis &amp; Dynamic Programming', response.data)

    def test_05_cross_specialty_post_access_blocked(self):
        """
        If a student tries to open a post from another specialty via direct URL,
        they are blocked with an access restriction notice.
        """
        # Login as Sarah (Computer Science)
        self.client.post('/login', data={
            'email': 'sarah.m@student.miami.edu',
            'password': 'password123'
        }, follow_redirects=True)

        # Post 3 is Clinical Anatomy (Medicine)
        response = self.client.get('/post/3', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Redirected back to feed with error notice
        self.assertIn(b'Access Restricted', response.data)

    def test_06_post_automatically_locked_to_student_specialty(self):
        """
        When Sarah creates a discussion, it is automatically posted under Computer Science & IT.
        """
        # Login as Sarah
        self.client.post('/login', data={
            'email': 'sarah.m@student.miami.edu',
            'password': 'password123'
        }, follow_redirects=True)

        response = self.client.post('/post/new', data={
            'title': 'Compiler Design & Lexical Analysis Study Group',
            'content': 'Looking for study partners for the upcoming compiler construction project.'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Compiler Design &amp; Lexical Analysis', response.data)
        self.assertIn(b'Computer Science &amp; IT', response.data)

    def test_07_register_new_student_with_country_and_specialty(self):
        """New student registers with Full Name, Specialty, Country, and university email"""
        response = self.client.post('/register', data={
            'full_name': 'Hassan Mansour',
            'email': 'hassan.m@student.miami.edu',
            'specialty': 'Electrical Engineering',
            'custom_specialty': '',
            'country': 'Algeria',
            'custom_country': '',
            'password': 'password123',
            'confirm_password': 'password123',
            'bio': 'Electrical engineering student specializing in renewable microgrids.'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hassan Mansour', response.data)
        # Feed opens directly into his specialty: Electrical Engineering
        self.assertIn(b'Electrical Engineering', response.data)

    def test_08_profile_access_rules(self):
        """Students can view profiles of peers within their own specialty, but not other departments"""
        # Login as Sarah (CS)
        self.client.post('/login', data={
            'email': 'sarah.m@student.miami.edu',
            'password': 'password123'
        }, follow_redirects=True)

        # Sarah views her own profile (User 1)
        res_self = self.client.get('/profile/1')
        self.assertEqual(res_self.status_code, 200)
        self.assertIn(b'Sarah Mansouri', res_self.data)

        # Sarah tries to view Lucas (User 2, Medicine) -> Blocked
        res_other = self.client.get('/profile/2', follow_redirects=True)
        self.assertEqual(res_other.status_code, 200)
        self.assertIn(b'Access Restricted', res_other.data)

if __name__ == '__main__':
    unittest.main()
