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
from chess.game import Game as ChessGame, PieceType
from typing import Union

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

    def is_in_game(self,game):
        return True if game in self.hostgames or game in self.guestgames else False

    def _is_gamehost(self,game):
        return True if game in self.hostgames else False

    def _is_gameguest(self,game):
        return True if game in self.guestgames else False

    def plays_as_white(self,game):
        if not self.is_in_game(game): return False
        if game.is_host_white and self._is_gamehost(game) or not game.is_host_white and self._is_gameguest(game): return True
        return False

    def plays_as_black(self,game):
        if not self.is_in_game(game): return False
        if not game.is_host_white and self._is_gamehost(game) or game.is_host_white and self._is_gameguest(game): return True
        return False

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
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sender = db.relationship('User', backref='sent', lazy='joined', foreign_keys='Message.sender_id')
    receiver = db.relationship('User', backref='received', lazy='joined', foreign_keys='Message.receiver_id')
    sender_seen = db.Column(db.Boolean, default=False)
    receiver_seen = db.Column(db.Boolean, default=False)

    def jsonify(self):
        return {'id': self.id, 'content': self.content, 'timestamp':self.timestamp_creation, 'sender':self.sender.username, 'receiver':self.receiver.username}

    def mark_as_seen(self):
        self.receiver_seen = True
        db.session.commit()

class Game(ITimeStampedModel, ChessGame):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(128), index=True, default=datetime.utcnow)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    guest_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    state = db.Column(db.Integer, index=True, default = 0)
    AI = db.Column(db.String(32))
    host = db.relationship('User', backref='hostgames', lazy='joined', foreign_keys='Game.host_id')
    guest = db.relationship('User', backref='guestgames', lazy='joined', foreign_keys='Game.guest_id')
    is_host_white = db.Column(db.Boolean, default=True)
    turn = db.Column(db.Boolean, default=True)
    check = db.Column(db.Boolean, default=False)

    def __init__(self,host_id,guest_id,is_host_white:bool=True, default_setup:bool=True, AI=None):
        #ChessGame.__init__(self, is_host_white, False, AI)
        self.host_id = host_id
        self.guest_id = guest_id
        self.AI = AI
        self.is_host_white = is_host_white
        for row in range(8):
            self.rows.append(GameRow(row=row))
            for col in range(8):
                self.rows[row].tiles.append(GameTile(column=col))
                if not default_setup: continue
                if 6<=row: self.set_colour((row,col), False)
                elif row < 2: self.set_colour((row,col), True)
                if row == 7 or row == 0:
                    self.set_piece((row,col), self.backRowSetup[col])
                if row == 6 or row == 1:
                    self.set_piece((row,col), 1)

    def __repr__(self):
        return f'<Game at={self.timestamp} state={self.state} between {self.host}{self.guest}> {self.all()}'

    def at(self,pos:Union[list,tuple]):
        return self.rows[pos[0]].get_tile(pos[1])
    def all(self):
        l = list()
        for x in range(8):
            for y in range(8):
                l.append(self.at((x,y)))
        return l
    def set_colour(self, pos:Union[list,tuple], colour:bool):
        self.rows[pos[0]].tiles[pos[1]].colour = colour
    def set_piece(self, pos:Union[list,tuple], piece:int):
        self.rows[pos[0]].tiles[pos[1]].piece = piece
    def move(self,src:list,dest:list):
        ChessGame.move(self, src, dest)
        db.session.commit()

    def find_king(self, colour:bool)->dict:
        for r,row in enumerate(self.rows):
            for t,tile in enumerate(row.tiles):
                if tile.piece == PieceType.KING.value and tile.colour == colour:
                    return {'xy': (r,t), 'tile': tile} 

    def set_check(self, colour: bool):
        super().set_check(colour)
        db.session.commit()


class RecoveryTry(ITimeStampedModel):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ipaddr = db.Column(db.String(64))
    is_confirmed = db.Column(db.Boolean, default=False)

class GameRow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    row = db.Column(db.Integer)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    game = db.relationship('Game', backref='rows', lazy='joined', foreign_keys='GameRow.game_id')

    def get_tile(self, col:int):
        return self.tiles[col]

class GameTile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    row_id = db.Column(db.Integer, db.ForeignKey('game_row.id'))
    row = db.relationship('GameRow', backref='tiles', lazy='joined', foreign_keys='GameTile.row_id')
    piece = db.Column(db.Integer, default=0)
    colour = db.Column(db.Boolean, default=False)
    moved = db.Column(db.Boolean, default=False)
    column = db.Column(db.Integer)

    def __repr__(self) -> str:
        return  f'<GameTile {self.id} {self.xy()}{[self.piece,self.colour,self.moved]}>'

    def toFEN(self)->str:
        p = ''
        if self.piece == 1: p = 'p'
        elif self.piece == 2: p = 'n'
        elif self.piece == 3: p = 'b'
        elif self.piece == 4: p = 'r'
        elif self.piece == 5: p = 'q'
        elif self.piece == 6: p = 'k'
        if self.colour: return p.upper()
        return p

    def xy(self) -> tuple:
        return ({self.row.row, self.column})

    def is_empty(self)->bool:
        return True if self.piece == 0 else False

    def is_white(self)->bool:
        return True if self.colour else False

    def is_black(self)->bool:
        return True if not self.colour else False

    def is_moved(self)->bool:
        return True if self.moved else False

    def jsonify(self)->dict:
        return {'piece':self.piece, 'colour': self.colour, 'moved': self.moved}




