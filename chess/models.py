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
from chess.game import Game as ChessGame, PieceType, Tile
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
    mm_request = db.relationship("MatchmakerRequest", back_populates="user", uselist=False)

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

class Game(ITimeStampedModel):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    guest_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    state = db.Column(db.Integer, index=True, default = 0)
    AI = db.Column(db.String(32))
    host = db.relationship('User', backref='hostgames', lazy='joined', foreign_keys='Game.host_id')
    guest = db.relationship('User', backref='guestgames', lazy='joined', foreign_keys='Game.guest_id')
    time_limit = db.Column(db.Integer, default=-1)
    is_host_white = db.Column(db.Boolean, default=True)
    game_state = db.relationship('GameState', backref='game', lazy=True)
    show_eval_bar = db.Column(db.Boolean, default=False)

    def add_new_state(self, state):
        self.game_state.append(state)
        db.session.commit()

    def get_current_state(self):
        return self.game_state[-1]


class RecoveryTry(ITimeStampedModel):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ipaddr = db.Column(db.String(64))
    is_confirmed = db.Column(db.Boolean, default=False)

class GameState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    placement = db.Column(db.String(256), default='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')
    turn = db.Column(db.String(1), default = 'w')
    move = db.Column(db.Integer, default=1)
    white_castle_king_side = db.Column(db.Boolean, default=True)
    white_castle_queen_side = db.Column(db.Boolean, default=True)
    black_castle_king_side = db.Column(db.Boolean, default=True)
    black_castle_queen_side = db.Column(db.Boolean, default=True)
    half_move_clock = db.Column(db.Integer, default=0)
    game_id = db.Column(db.Integer, db.ForeignKey(Game.id))
    en_passent = db.Column(db.String(2), default='-')

    def is_white_turn(self)->bool:
        return True if self.turn == 'w' else False

    def is_black_turn(self)->bool:
        return True if self.turn == 'b' else False

    def toggle_turn(self):
        self.turn = 'w' if self.turn == 'b' else 'b'
        db.session.commit()

    def set(self,fen:str):
        print('BEFORE SET:', fen)
        attr = fen.split(' ')
        for a in attr:
            print(a)
        self.placement = attr[0]
        self.turn = attr[1]
        self.white_castle_king_side = True if 'K' in attr[2] else False
        self.white_castle_queen_side = True if 'Q' in attr[2] else False
        self.black_castle_king_side = True if 'k' in attr[2] else False
        self.black_castle_queen_side = True if 'q' in attr[2] else False
        self.en_passent = attr[3]
        self.half_move_clock = int(attr[4])
        self.move = int(attr[5])
        db.session.commit()
        print('SET:', self.placement)


    def to_fen(self)->str:
        result = '' + self.placement + ' ' + self.turn + ' '
        if self.white_castle_king_side: result += 'K'
        if self.white_castle_queen_side: result += 'Q'
        if self.black_castle_king_side: result += 'k'
        if self.black_castle_queen_side: result += 'q'
        result += ' ' + self.en_passent + ' ' + str(self.half_move_clock) + ' ' + str(self.move) 
        return result
        
    def to_list(self)->list:
        result = list()
        print(self.placement)
        rows = self.placement.split('/')
        for r,row in enumerate(reversed(rows)):
            result.append(list())
            for c,t in enumerate(row):
                if t.lower() == 'p':
                    result[r].append(Tile(1,t.isupper()).jsonify())
                elif t.lower() == 'n':
                    result[r].append(Tile(2,t.isupper()).jsonify())
                elif t.lower() == 'b':
                    result[r].append(Tile(3,t.isupper()).jsonify())
                elif t.lower() == 'r':
                    result[r].append(Tile(4,t.isupper()).jsonify())
                elif t.lower() == 'q':
                    result[r].append(Tile(5,t.isupper()).jsonify())
                elif t.lower() == 'k':
                    result[r].append(Tile(6,t.isupper()).jsonify())
                elif t.isnumeric():
                    for x in range(int(t)):
                        result[r].append(Tile(0,False).jsonify())

        return result

class MatchmakerRequest(ITimeStampedModel):
    id = db.Column(db.Integer, primary_key=True)
    ranked = db.Column(db.Boolean)
    min_rank = db.Column(db.Integer)
    max_rank = db.Column(db.Integer)
    time = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='mm_request')

    def __eq__(self,mmrequest):
        return True if self.user_id == mmrequest.user_id else False

    def fulfills_conditions(self,mmrequest):
        user = mmrequest.user
        if self.min_rank <= user.elo <= self.max_rank and mmrequest.min_rank <= self.user.elo <= mmrequest.max_rank and self.ranked == mmrequest.ranked:
            return True
        return False
                    









