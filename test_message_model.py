"""Message View tests."""

import os
from unittest import TestCase
from models import db, connect_db, Message, User


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


from app import app, CURR_USER_KEY

# db.create_all()


app.config['WTF_CSRF_ENABLED'] = False



class MessageModelTests(TestCase):
    """Test model for messages."""
    
    def setUp(self):
        """Create test client, add sample data."""

        with app.app_context():
            db.create_all()
            
        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()
            
    def test_message_model(self):
        """Tests if a user can successfully create a message"""
        with self.client:
            
            message = Message(text='This is a test message.', user_id=self.testuser.id)
            db.session.add(message)
            db.session.commit()

            retrieved_message = Message.query.get(message.id)

            self.assertEqual(retrieved_message.text, 'This is a test message.')
            self.assertEqual(retrieved_message.user_id, self.testuser.id)
            self.assertEqual(retrieved_message.id, 1)
            self.assertEqual(retrieved_message.id, 1)
            
            
            
            
    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
        db.drop_all()
        
        

        
    
            
            
    