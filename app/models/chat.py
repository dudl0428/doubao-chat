from datetime import datetime
from app import db

class Chat(db.Model):
    """Chat model for storing chat sessions."""
    __tablename__ = 'chats'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, default='新对话')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('Message', backref='chat', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Chat {self.title}>'

class Message(db.Model):
    """Message model for storing chat messages."""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message {self.id} - {self.role}>' 