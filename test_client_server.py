import unittest
import json
from app import app
from seed_data import seed_database

class ClientServerApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database()

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_api_status(self):
        """Client connects and verifies server status"""
        res = self.client.get('/api/status')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'online')
        self.assertEqual(data['server'], 'Miami Campus Central Server')
        self.assertIn('Client-Server', data['architecture'])
        self.assertIn('Strict', data['specialty_isolation'])

    def test_02_api_client_registration(self):
        """Client registers student with full name, specialty, country, and university email"""
        payload = {
            'full_name': 'Zackary Taylor',
            'email': 'zackary.t@student.miami.edu',
            'specialty': 'Civil & Architectural Engineering',
            'country': 'Canada',
            'password': 'password123',
            'bio': 'Civil engineering student interested in smart city design.'
        }
        res = self.client.post('/api/register', json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['student']['full_name'], 'Zackary Taylor')
        self.assertEqual(data['student']['specialty'], 'Civil & Architectural Engineering')
        self.assertEqual(data['student']['country'], 'Canada')

    def test_03_api_client_registration_rejects_outsiders(self):
        """Client registration is blocked for non-university domains"""
        payload = {
            'full_name': 'External Person',
            'email': 'hacker@yahoo.com',
            'specialty': 'Computer Science & IT',
            'country': 'USA',
            'password': 'password123'
        }
        res = self.client.post('/api/register', json=payload)
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertFalse(data['success'])

    def test_04_api_client_login(self):
        """Client authenticates with server credentials"""
        payload = {
            'email': 'sarah.m@student.miami.edu',
            'password': 'password123'
        }
        res = self.client.post('/api/login', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['student']['full_name'], 'Sarah Mansouri')
        self.assertEqual(data['student']['specialty'], 'Computer Science & IT')

    def test_05_api_specialty_isolated_discussions(self):
        """Client retrieves discussions strictly isolated to their registered specialty"""
        # Authenticate as Sarah (CS, User ID 1)
        headers = {'X-Student-Id': '1'}
        res = self.client.get('/api/discussions', headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['specialty_channel'], 'Computer Science & IT')
        # All discussions in data must belong to Computer Science & IT
        for d in data['discussions']:
            self.assertEqual(d['specialty'], 'Computer Science & IT')

    def test_06_api_post_discussion_locked_to_specialty(self):
        """When Sarah posts, it is automatically published into Computer Science & IT"""
        headers = {'X-Student-Id': '1'}  # Sarah Mansouri (CS)
        payload = {
            'title': 'Autonomous Robotics Simulation Workshop on Campus',
            'content': 'We are hosting a ROS2 simulation session in McArthur Hall this Saturday.'
        }
        res = self.client.post('/api/discussions', json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['specialty'], 'Computer Science & IT')

    def test_07_api_blocks_cross_specialty_detail(self):
        """Client is blocked from retrieving details of a discussion from another specialty"""
        headers = {'X-Student-Id': '1'}  # Sarah Mansouri (CS)
        # Post 3 is Clinical Anatomy (Medicine)
        res = self.client.get('/api/discussions/3', headers=headers)
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertIn('Access restricted', data['error'])

if __name__ == '__main__':
    unittest.main()
