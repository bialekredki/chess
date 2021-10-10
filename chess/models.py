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

friends_table = db.Table('friends', 
    db.Column('user1_id', db.Integer, db.ForeignKey('user.id')), 
    db.Column('user2_id', db.Integer, db.ForeignKey('user.id')))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    has_avatar = db.Column(db.Boolean, default=False)
    joined = db.Column(db.DateTime(128),default=datetime.utcnow)
    posts = db.relationship('BlogPost', backref='author', lazy='dynamic')
    messages = db.relationship('Message', backref='receiver', lazy='dynamic')
    friends = db.relationship('User', secondary=friends_table,
        primaryjoin=(friends_table.c.user1_id == id),
        secondaryjoin=(friends_table.c.user2_id == id),
        backref=db.backref('friends_table', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def add_friend(self, user):
        if not self.is_friends_with(user): self.friends.append(user)

    def remove_friend(self,user):
        if self.is_friends_with(user): self.friends.remove(user)

    def is_friends_with(self,user):
        return self.friends.filter(friends_table.c.user1_id == user.id).count > 0 or self.friends.filter(friends_table.c.user2_id == user.id).count > 0

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime(128), index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Post {self.body}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1024))
    timestamp = db.Column(db.DateTime(128), index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

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


