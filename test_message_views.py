"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase
from flask import url_for,g
from models import db, connect_db, Message, User


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app
from app import app, CURR_USER_KEY



# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

# db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

# def tearDown(self):
#         with self.app.app_context():
#             db.session.remove()
#             db.drop_all()


def load_user(user_id):
        return User.query.get(int(user_id))

class MessageViewTestCase(TestCase):
    """Test views for messages."""
    

    def setUp(self):
        """Create test client, add sample data."""
        
        db.session.rollback()
        
        with app.app_context():
            db.create_all()
        
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
        # self.client = app.test_client()
        self.app = app
            

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
            self.assertEqual(msg.user_id,1)
      
      
      
    def test_prohibit_delete_anoter_user_message(self):
        """Test if a user is prohibited to delete another user's message"""
        
        with self.client:
            
            self.client.post('/login', data={'username': 'testuser1', 'password': 'testuser1'})
            # db.session[CURR_USER_KEY] = self.testuser1.id
            
            message = Message(text='This is a test message.', user_id=2)
            db.session.add(message)
            db.session.commit() 
            print(message.user_id)
            print(message.id)
            print(Message.query.all())
            
            response = self.client.post(f'/messages/{message.id}/delete')
            
            messages = Message.query.all()
            
            self.assertEqual(response.status_code, 403)
            self.assertEqual(len(messages),1)
            
            
            
    def test_loggedin_user_delete(self):
        """Tests if a logged in user can delete his message"""
        with self.client:
            
            self.client.post('/login', data={'username': 'testuser1', 'password': 'testuser1'})
            
            message = Message(text='This is a test message.', user_id=self.testuser1.id)
            db.session.add(message)
            db.session.commit() 
            
            
            response = self.client.post(f'/messages/{message.id}/delete')
            messages = Message.query.all()
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(len(messages),0)
            
            
                    
            
    def test_logout_disallow_viewing(self):
        """Tests if a logged out user is prohibited to view messages """
        with self.client:
                
            message = Message(text='This is a test message.', user_id=self.testuser1.id)
            db.session.add(message)
            db.session.commit() 
                
            response = self.client.get(f'/users/{self.testuser1.id}')  
               
            self.assertEqual(response.location, url_for('login', _external=True))
                
                
    def test_login_newmessage_asyourself(self):
        """Tests if a logged in user can create a message as himself"""
        with self.client:
            self.client.post('/login', method='POST', data={'username': 'testuser1', 'password': 'testuser1'})
            
            message = Message(text='Test message', user_id=self.testuser1.id)
            db.session.add(message)
            db.session.commit()
            
            self.assertEqual(message.text, 'Test message')
            self.assertEqual(message.user_id, self.testuser1.id)
            self.assertEqual(message.id, 1)
            
                
    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
        db.drop_all()