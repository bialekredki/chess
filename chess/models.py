from enum import unique

from sqlalchemy.orm import backref
from chess import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from chess import login

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    has_avatar = db.Column(db.Boolean, default=False)
    joined = db.Column(db.DateTime(128),default=datetime.utcnow)
    posts = db.relationship('BlogPost', backref='author', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime(128), index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Post {self.body}>'

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(128), index=True, default=datetime.utcnow)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    guest_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    state = db.Column(db.Integer, index=True, default = 0)
    host = db.relationship('User', backref='hostgames', lazy='joined', foreign_keys='Game.host_id')
    guest = db.relationship('User', backref='guestgames', lazy='joined', foreign_keys='Game.guest_id')

    def __init__(self, host, guest):
        self.host = host
        self.guest = guest

    def __repr__(self):
        return f'<Game at={self.timestamp} state={self.state} between {self.host}{self.guest}>'
