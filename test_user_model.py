"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from flask import url_for
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

# db.create_all()


app.config['WTF_CSRF_ENABLED'] = False

            


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.create_all()
        # db.session.rollback()
        
        # with app.app_context():
        #     db.create_all()
        
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        
        
        
    def test_followers(self):
        """Tests if a follower can be added"""
        with self.client:
            user1 = User(username = 'user1', email = 'test1@example.com', password = 'password1')
            user2 = User(username = 'user2', email = 'test2@example.com', password = 'password2')
        
            db.session.add_all([user1,user2])
            db.session.commit()
        
            user1.following.append(user2)
        
            db.session.commit()
        
            followers_of_user2 = user2.followers
        
            self.assertEqual(len(followers_of_user2),1)
            self.assertNotIn(user2,followers_of_user2)
            self.assertIn(user1,followers_of_user2)

    
    def test_following(self):
        """Tests if a user can follow another user"""
        with self.client:
            user1 = User(username = 'user1', email = 'test1@example.com', password = 'password1')
            user2 = User(username = 'user2', email = 'test2@example.com', password = 'password2')
        
            db.session.add_all([user1,user2])
            db.session.commit()
        
            user1.following.append(user2)
        
            db.session.commit()
            
            following_of_user1 = user1.following
            self.assertEqual(len(following_of_user1),1)
            self.assertNotIn(user1,following_of_user1)
            self.assertIn(user2,following_of_user1)
            
    
    def test_successful_authenticate(self):
        """Tests if the authentication works properly"""
        with self.client:
            user1 = User.signup(username = 'user1', email = 'test1@example.com', password = 'password1',image_url=None)
            db.session.add(user1)
            db.session.commit()
        
            res = user1.authenticate('user1','password1')
            
            self.assertEqual('test1@example.com', res.email,)
            self.assertEqual(1, res.id,)
            
            
    def test_invalid_username(self):
        """Tests if the authentication returns false with an invalid username"""
        with self.client:
            user1 = User.signup(username = 'user1', email = 'test1@example.com', password = 'password1',image_url=None)
            db.session.add(user1)
            db.session.commit()
        
            res = user1.authenticate('user2','password1')
            
            self.assertFalse(res)
            
            
    def test_invalid_password(self):
        """Tests if the authentication works properly with an invalid password"""
        with self.client:
            user1 = User.signup(username = 'user1', email = 'test1@example.com', password = 'password1',image_url=None)
            db.session.add(user1)
            db.session.commit()
        
            response = self.client.post('/login', data={'username': 'user1', 'password': 'wrongpassword'})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, url_for('login', _external=True))
            
            
            
    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
        db.drop_all()