import os
from unittest import TestCase
from flask import url_for,g
from models import db, Message, User


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.create_all()
        # db.session.rollback()
        
        # with app.app_context():
        #     db.create_all()
        
        User.query.delete()
        Message.query.delete()
        
        
        self.client = app.test_client()

        self.testuser1 = User.signup(username="testuser1",
                                email="test1@test.com",
                                password="testuser1",
                                image_url=None)
    
        self.testuser2 = User.signup(username="testuser2",
                                email="test2@test.com",
                                password="testuser2",
                                image_url=None)

        db.session.commit()
        
        self.app = app
        
        
    
    def test_view_following(self):
        """Tests if a user can view the messages that he follows"""
        with self.client:
            self.client.post("/login", data={'username': 'testuser1', 'password': 'testuser1'})
            
            followed_user = User.query.get_or_404(self.testuser2.id)
            self.testuser1.following.append(followed_user)
            db.session.commit()
            print(self.testuser1.following)
            response = self.client.get(f'/users/{self.testuser1.id}/following')
            print(response)
            
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'<title>Warbler',response.data)
            
            
    def test_view_followers(self):
        """Tests if a user can view his followers"""
        with self.client:
            self.client.post("/login", data={'username': 'testuser1', 'password': 'testuser1'})         
            
            followed_user = User.query.get_or_404(self.testuser1.id)
            self.testuser2.following.append(followed_user)
            db.session.commit()
            
            response = self.client.get(f'/users/{self.testuser1.id}/followers')
            
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'<title>Warbler',response.data)
            
            
            
    def test_delete_profile(self):
        """Tests if a user can delete his own profile"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id
                
            print(self.testuser1.id)
            response = c.post(f"/users/{self.testuser1.id}/delete") 
            
            self.assertEqual(response.location, url_for('signup', _external=True))
            
            

    def tearDown(self):
        """Clean up any fouled transaction"""
        db.session.rollback()
        db.session.close()
                