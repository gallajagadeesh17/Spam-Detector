import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to sys.path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

class TestDashboard(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret'
        self.client = app.test_client()

    @patch('app.get_db_connection')
    def test_dashboard_spam_percent_calculation(self, mock_get_db):
        """Test that spam_percent is calculated correctly (50%) and rendered in the HTML style attribute."""
        # Mock DB connection and cursor
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        
        # Mock user fetch
        mock_user = {'id': 1, 'full name': 'Test User', 'email': 'test@gmail.com'}
        
        # Mock history fetch (1 Spam, 1 Safe = 50%)
        # The app.py logic checks for row['result'] == 'Spam'
        
        # Configure side_effect for execute to handle multiple calls
        def execute_side_effect(query, params):
            cursor = MagicMock()
            if 'SELECT * FROM users' in query:
                cursor.fetchone.return_value = mock_user
            elif 'SELECT COUNT(*) FROM analysis_history' in query:
                if 'score >= 50' in query:
                    cursor.fetchone.return_value = [1]
                else:
                    cursor.fetchone.return_value = [2]
            return cursor

        mock_conn.execute.side_effect = execute_side_effect

        # Simulate logged-in user
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'user'

        response = self.client.get('/dashboard')
        
        self.assertEqual(response.status_code, 200)
        
        # Verify the HTML contains the calculated percentage in the width style
        # 1 spam out of 2 total = 50.0%
        self.assertIn(b'width: 50.0%', response.data)
        self.assertIn(b'50.0%', response.data)

    @patch('app.get_db_connection')
    def test_dashboard_zero_emails(self, mock_get_db):
        """Test that spam_percent is 0 when there is no history."""
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        
        mock_user = {'id': 1, 'full name': 'Test User', 'email': 'test@gmail.com'}
        
        def execute_side_effect(query, params):
            cursor = MagicMock()
            if 'SELECT * FROM users' in query:
                cursor.fetchone.return_value = mock_user
            elif 'SELECT COUNT(*) FROM analysis_history' in query:
                cursor.fetchone.return_value = [0]
            return cursor

        mock_conn.execute.side_effect = execute_side_effect

        with self.client.session_transaction() as sess:
            sess['user_id'] = 1

        response = self.client.get('/dashboard')
        
        self.assertEqual(response.status_code, 200)
        # 0 emails = 0%
        self.assertIn(b'width: 0%', response.data)

    def test_dashboard_redirect_if_not_logged_in(self):
        """Test that accessing dashboard without session redirects to login."""
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

if __name__ == '__main__':
    unittest.main()