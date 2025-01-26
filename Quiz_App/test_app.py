import unittest
from app import app, db, User, Score, Feedback
from werkzeug.security import generate_password_hash

class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app = app.test_client()

        # Create the database and tables
        with app.app_context():
            db.create_all()

            # Add a test user
            hashed_password = generate_password_hash('testpassword')
            test_user = User(username='testuser', email='test@example.com', password=hashed_password)
            db.session.add(test_user)
            db.session.commit()

    def tearDown(self):
        # Clean up the database after each test
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # Helper method to log in a test user
    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username_or_email=username,
            password=password
        ), follow_redirects=True)

    # Helper method to log out
    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    # Test home page
    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to the Quiz App!', response.data)

    # Test user registration
    def test_register(self):
        response = self.app.post('/register', data=dict(
            username='newuser',
            email='newuser@example.com',
            password='newpassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful! Please login.', response.data)

    # Test user login
    def test_login(self):
        response = self.login('testuser', 'testpassword')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged in successfully!', response.data)

    # Test invalid login
    def test_invalid_login(self):
        response = self.login('wronguser', 'wrongpassword')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username/email or password', response.data)

    # Test user logout
    def test_logout(self):
        self.login('testuser', 'testpassword')
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged out successfully!', response.data)

    # Test quiz page access
    def test_quiz_page(self):
        self.login('testuser', 'testpassword')
        response = self.app.get('/quiz')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Quiz', response.data)

    # Test quiz submission
    def test_quiz_submission(self):
        self.login('testuser', 'testpassword')
        response = self.app.post('/quiz', data={
            'Which mammal is known to lay eggs?': 'Platypus',
            'Who painted the Mona Lisa?': 'Leonardo da Vinci'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Quiz Results', response.data)

    # Test leaderboard page
    def test_leaderboard_page(self):
        response = self.app.get('/leaderboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Leaderboard', response.data)

    # Test profile page
    def test_profile_page(self):
        self.login('testuser', 'testpassword')
        response = self.app.get('/profile')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Profile', response.data)

    # Test feedback submission
    def test_feedback_submission(self):
        self.login('testuser', 'testpassword')
        response = self.app.post('/feedback', data=dict(
            message='This is a test feedback.'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Thank you for your feedback!', response.data)

    # Test admin panel access (unauthorized)
    def test_admin_panel_unauthorized(self):
        self.login('testuser', 'testpassword')
        response = self.app.get('/admin')
        self.assertEqual(response.status_code, 403)  # Forbidden

    # Test admin panel access (authorized)
    def test_admin_panel_authorized(self):
        # Make the test user an admin
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            user.is_admin = True
            db.session.commit()

        self.login('testuser', 'testpassword')
        response = self.app.get('/admin')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin Panel', response.data)

    # Test password reset request
    def test_password_reset_request(self):
        response = self.app.post('/reset_password', data=dict(
            email='test@example.com'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Password reset link sent to your email.', response.data)

    # Test password reset with token
    def test_password_reset_token(self):
        # Generate a token for the test user
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            token = app.serializer.dumps(user.email, salt=app.config['SECURITY_PASSWORD_SALT'])

        response = self.app.post(f'/reset_password/{token}', data=dict(
            new_password='newpassword123'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Your password has been reset!', response.data)

if __name__ == '__main__':
    unittest.main()