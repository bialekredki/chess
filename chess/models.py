from enum import unique
from flask.templating import render_template

from sqlalchemy.orm import backref
from sqlalchemy.sql.schema import ForeignKey
from chess import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from chess import login
from chess.utils import round_datetime

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

friends_table = db.Table('friends', 
    db.Column('user1_id', db.Integer, db.ForeignKey('user.id')), 
    db.Column('user2_id', db.Integer, db.ForeignKey('user.id')))

liked_table = db.Table('liked_posts', 
    db.Column('luser_id', db.Integer, db.ForeignKey('user.id'), primary_key=True), 
    db.Column('blog_post_id', db.Integer, db.ForeignKey('blog_post.id'), primary_key=True))



class ITimeStampedModel(db.Model):
    __abstract__ = True
    timestamp_creation = db.Column(db.DateTime(128), default=datetime.utcnow)

    def get_creation_stamp(self):
        return self.timestamp_creation

    def set_creation_stamp(self,timestamp=datetime.utcnow):
        self.timestamp_creation = timestamp

    def get_human_creation_stamp(self):
        pass

    def get_human_creation_delta(self):
        return round_datetime(self.get_timedelta_creation())

    def get_timedelta_creation(self): 
        return datetime.utcnow() - self.timestamp_creation

class IActivityModel(db.Model):
    __abstract__ = True
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(UserMixin, ITimeStampedModel):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    has_avatar = db.Column(db.Boolean, default=False)
    posts = db.relationship('BlogPost', backref='author', lazy='dynamic')
    messages = db.relationship('Message', backref='receiver', lazy='dynamic')
    recoverytries = db.relationship('RecoveryTry')
    last_active = db.Column(db.DateTime(128), default=datetime.utcnow)
    is_confirmed = db.Column(db.Boolean, default=False)
    elo = db.Column(db.Integer, default=400)
    friends = db.relationship('User', secondary=friends_table,
        primaryjoin=(friends_table.c.user1_id == id),
        secondaryjoin=(friends_table.c.user2_id == id),
        backref=db.backref('friends_table', lazy='dynamic'), lazy='dynamic')
    liked = db.relationship("BlogPost",
                    secondary=liked_table,
                    lazy='dynamic',
                    backref=db.backref('liked_by', lazy='dynamic'))

    def __repr__(self):
        return f'<User {self.username}>'

    def to_html_table_row(self):
        return render_template('user_table_row.html',user=self)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_creation_date(self):
        return self.timestamp_creation

    def update_last_activity(self):
        self.last_active = datetime.utcnow
        db.session.commit()

    def add_friend(self, user):
        if not self.is_friends_with(user): 
            self.friends.append(user)
            user.friends.append(self)
            db.session.commit()

    def remove_friend(self,user):
        if self.is_friends_with(user): 
            self.friends.remove(user)
            db.session.commit()
            user.friends.remove(self)
            db.session.commit()

    def is_friends_with(self,user):
        return self.friends.filter(friends_table.c.user1_id == user.id).count() > 0 or self.friends.filter(friends_table.c.user2_id == user.id).count() > 0

    def is_liking(self,post):
        return self.liked.filter(liked_table.c.blog_post_id == post.id).count() > 0

    def get_posts_count(self):
        return len(self.posts.all())

class BlogPost(ITimeStampedModel):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(32))
    content = db.Column(db.String(4096))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    upvotes = db.Column(db.Integer, default=0)
    comments = db.relationship('BlogPostComment', backref='article', lazy=True)

    def __repr__(self):
        return f'<Post {self.subject}>'

    def get_author_username(self):
        return User.query.filter_by(id=self.user_id).first().username

    def get_comments_count(self):
        return len(self.comments.all())

    def is_liked_by(self,user:User):
        return self.liked_by.filter(liked_table.c.luser_id == user.id).count() > 0

    def like(self, user:User):
        if not self.is_liked_by(user):
            self.liked_by.append(user)
            return True
        return False

    def dislike(self, user:User):
        if self.is_liked_by(user):
            self.liked_by.remove(user)
            return True
        return False

    def add_comment(self,comment):
        pass

    def remove_comment(self, commentid):
        pass

class BlogPostComment(ITimeStampedModel):
    content_max_len = 128
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(content_max_len))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey(BlogPost.id))

    def get_author_username(self):
        return User.query.filter_by(id=self.user_id).first().username

class Message(ITimeStampedModel):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1024))
    timestamp = db.Column(db.DateTime(128), index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Game(ITimeStampedModel):
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

class RecoveryTry(ITimeStampedModel):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ipaddr = db.Column(db.String(64))
    is_confirmed = db.Column(db.Boolean, default=False)




