from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class User(UserMixin, db.Model):
    """User model for storing user related details."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    chats = db.relationship('Chat', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def password(self):
        """Prevent password from being accessed."""
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        """Set password to a hashed password."""
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """Check if password matches the hashed password."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.query.get(int(user_id)) 