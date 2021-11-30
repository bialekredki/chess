from enum import unique
from flask.templating import render_template

from sqlalchemy.orm import backref
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from chess import db, app
import math
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from chess import login
from chess.elo import expected_score, k_factor
from chess.game_options import GameConclusionFlag, GameFormat, PlayerMovePermission, ChessTitle
from chess.geolocation import country_alpha2_to_name
from chess.utils import round_datetime
from chess.game import Game as ChessGame, PieceType, Tile, Move
from chess.AI import StockfishIntegrationAI, AI, PREFERRED_INTEGRATION, get_ai
from typing import Union
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature, SignatureExpired

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

friends_table = db.Table('friends', 
    db.Column('user1_id', db.Integer, db.ForeignKey('user.id')), 
    db.Column('user2_id', db.Integer, db.ForeignKey('user.id')))

liked_table = db.Table('liked_posts', 
    db.Column('luser_id', db.Integer, db.ForeignKey('user.id'), primary_key=True), 
    db.Column('blog_post_id', db.Integer, db.ForeignKey('blog_post.id'), primary_key=True))


class ChessBoardTheme(db.Model):
    __tablename__ = 'chess_board_theme'
    name = db.Column(db.String(32), primary_key=True)
    piece_set = db.Column(db.String(32))
    black_tile_colour = db.Column(db.Integer)
    white_tile_colour = db.Column(db.Integer)

    def jsonify(self):
        return {'name': self.name, 'piece_set': self.piece_set, 'black_tile_colour': self.black_tile_colour, 'white_tile_colour': self.white_tile_colour}



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

    def HTML(self) -> str:
        result = '<p>'
        for k, v in self.__dict__.items():
            result  += f'{k}:{v}\n'
        result += '</p>'
        return result


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
    theme = db.Column(db.String(32), default='Classic')
    name = db.Column(db.String(64))
    private = db.Column(db.Boolean)
    country = db.Column(db.String(8))
    ratings = db.relationship("EloUserRating", back_populates="user")
    title = db.Column(db.Integer)

    def __repr__(self):
        return f'<User {self.username}>'

    def generate_auth_token(self,expiration=6000):
        serializer = TimedJSONWebSignatureSerializer(app.config['SECRET_KEY'], expires_in=expiration)
        return serializer.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = TimedJSONWebSignatureSerializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.query.get(data['id'])
        return user

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

    def set_name(self,name:str):
        self.name = name
        db.session.commit()

    def set_theme(self, theme:str):
        if ChessBoardTheme.query.get(theme) is None: raise ValueError(f'{self}{__name__} There is no {theme} theme')
        self.theme = theme
        db.session.commit()

    def get_theme(self)->'ChessBoardTheme':
        return ChessBoardTheme.query.filter_by(name=self.theme).first()

    def toggle_private(self):
        self.private = not self.private
        db.session.commit()
    
    def set_private(self, private:bool):
        self.private = private
        db.session.commit()

    def countryname(self) -> str:
        return country_alpha2_to_name(self.country)

    def can_access_private(self, user:'User') -> bool:
        if not self.private: return True
        if self.private and (self.id == user.id or self.is_friends_with(user)): return True
        return False

    def get_current_rating(self) -> 'EloUserRating':
        return self.ratings[-1]

    def add_rating(self, timestamp:datetime=datetime.utcnow()):
        if len(self.ratings) == 0:
            e = EloUserRating(timestamp_creation=timestamp, user_id=self.id)
        else:
            current = self.get_current_rating()
            e = EloUserRating(timestamp_creation=timestamp, user_id=self.id, rapid=current.rapid, blitz=current.blitz, bullet=current.bullet, puzzles=current.puzzles, standard=current.standard)
        e.user_id = self.id
        db.session.add(e)
        db.session.commit()

    def get_rating(self, format_name:str='rapid'):
        rating:'EloUserRating' = self.get_current_rating()
        if format_name == 'rapid': return rating.rapid
        elif format_name == 'blitz': return rating.blitz
        elif format_name == 'bullet': return rating.bullet
        elif format_name == 'standard': return rating.standard
        elif format_name == 'puzzles': return rating.puzzles

    def update_rating(self, rating:int, format_name:str='rapid'):
        self.get_current_rating().update(format_name, rating)

    def get_title(self) -> ChessTitle:
        return ChessTitle.by_id(self.title)

    def get_title_name(self) -> str:
        return self.get_title().name()
    
    def get_title_short(self) -> str:
        return self.get_title().short()

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
    ranked = db.Column(db.Boolean, default=False)

    def add_new_state(self, state):
        self.game_state.append(state)
        db.session.commit()

    def get_current_state(self) -> 'GameState':
        return self.game_state[-1]

    def ended(self) -> bool:
        return self.state != GameConclusionFlag.NONE.id()

    def is_draw(self) -> bool:
        return self.state in GameConclusionFlag.draws_ids()

    def white_won(self) -> bool:
        return self.state == GameConclusionFlag.WHITE_WON.id()

    def black_won(self) -> bool:
        return self.state == GameConclusionFlag.BLACK_WON.id()

    def is_ai_game(self) -> bool:
        return True if self.guest_id == -1 or self.host_id == -1 else False

    def is_expired(self) -> bool:
        return True if (datetime.utcnow() - self.timestamp_creation).total_seconds() > self.time_limit else False

    def white_player(self) -> User:
        if self.host.plays_as_white(self): return self.host
        return self.guest 

    def black_player(self) -> User:
        if self.host.plays_as_black(self): return self.host
        return self.guest

    def player_by_colour(self, colour:bool) -> User:
        if colour: return self.white_player()
        return self.black_player()

    def get_game_format(self) -> GameFormat:
        return GameFormat.by_time(self.time_limit)

    def get_game_format_model(self) -> str:
        return self.get_game_format().model_name()

    def is_rapid_or_blitz(self) -> bool:
        game_format = GameFormat.by_time(self.time_limit)
        if game_format is None: return False
        if 'rapid' in game_format.value['id'] or 'blitz' in game_format.value['id']: return True
        return False

    def _get_elo_changes(self, colour:bool) -> dict:
        if self.host_id == -1 or self.guest_id == -1: return {'win': 0, 'draw':0, 'lose': 0}
        user:User = self.player_by_colour(colour)
        opponent:User = self.player_by_colour(not colour)
        format_model = self.get_game_format_model()
        exp = expected_score(user.get_rating(format_model), opponent.get_rating(format_model))
        k = k_factor(user.get_rating(format_model), rapid=self.is_rapid_or_blitz(), games_number=len(user.hostgames)+len(user.guestgames))
        return {'win': math.floor(k*(1-exp)), 'draw': math.floor(k*(0.5-exp)), 'lose': math.floor(k*(0-exp))}

    def is_ai_game(self) -> bool:
        return True if self.guest_id == -1 else False


    def _apply_elo_changes(self):
        if not self.ended(): return
        model = self.get_game_format_model()
        white_changes = self._get_elo_changes(True)
        black_changes = self._get_elo_changes(False)
        print(white_changes)
        white_rating = self.white_player().get_rating(model)
        black_rating = self.black_player().get_rating(model)
        print(white_rating)
        if self.is_draw():
            white_rating = white_rating + white_changes['draw']
            black_rating = black_rating + black_changes['draw']
        if self.black_won():
            white_rating = white_rating+white_changes['lose']
            white_rating = black_rating + black_changes['win']
        if self.white_won():
            white_rating = white_rating+white_changes['win']
            black_rating = black_rating + black_changes['lose']
        self.white_player().update_rating(white_rating, model)
        self.black_player().update_rating(black_rating, model)

    def set_state_flag(self, state:GameConclusionFlag):
        self.state = state.id()
        db.session.commit()

    def conclude(self):
        if not self.check_for_endgame(): return
        print('CHECK FOR ENDGAME ',self.check_for_endgame())
        game:ChessGame = ChessGame(self.get_current_state().to_list(), self.get_current_state().to_fen())
        new_state = GameConclusionFlag.NONE
        if self.check_draw(False,game): new_state = GameConclusionFlag.DRAW
        elif self.check_for_repetition(): new_state = GameConclusionFlag.DRAW_BY_REPETITION
        elif self.fifty_move_draw(): new_state = GameConclusionFlag.DRAW_BY_50_MOVES
        elif self.check_black_win(False, game): new_state = GameConclusionFlag.BLACK_WON
        elif self.check_white_win(False, game): new_state = GameConclusionFlag.WHITE_WON
        self.set_state_flag(new_state)
        if self.ranked: self._apply_elo_changes()
        print('SELF>STATE ', self.state)

    def can_player_move(self, user:User) -> PlayerMovePermission:
        print(user.id, self.host.id)
        if not user.is_in_game(self): return PlayerMovePermission.GUEST
        if user.plays_as_black(self) and self.get_current_state().is_white_turn() or user.plays_as_white(self) and self.get_current_state().is_black_turn(): return PlayerMovePermission.NO
        return PlayerMovePermission.YES

    def new_game_state(self, fen:str=None):
        new_state = GameState()
        self.game_state.append(new_state)
        if fen is not None: new_state.set(fen)
        db.session.add(new_state)
        db.session.commit()

    def is_move_possible(self, move:str, engine_integration:AI) -> bool: 
        return engine_integration.is_possible(move)

    def move(self,move:Union[Move,str],colour:bool) -> bool:
        if type(move) == Move: algebraic = move.algebraic()
        else: algebraic = move
        engine = get_ai(PREFERRED_INTEGRATION, self.get_current_state().to_fen())
        chess_game = ChessGame(self.get_current_state().to_list(), self.get_current_state().to_fen())
        if not self.is_move_possible(algebraic, engine):
            app.logger.info('%s submitted impossible move', 'White' if colour else 'Black')
            return False
        self.new_game_state(engine.move(algebraic))
        self.conclude()
        return True

    def evaluate(self, state_rindex:int=0):
        if state_rindex > len(self.game_state) - 1: raise ValueError(f"{self}{__name__} state_rindex{state_rindex} cannot be larger than {len(self.game_state)-1}.")
        engine = StockfishIntegrationAI(self.game_state[-1-state_rindex].to_fen())
        return engine.get_eval()

    def check_for_repetition(self) -> bool:
        current:GameState = self.get_current_state()
        counter:int = 0
        for position in self.game_state[0:len(self.game_state)-1]:
            if position == current: counter += 1
        if counter >= 3: return True
        return False

    def fifty_move_draw(self) -> bool:
        if self.get_current_state().half_move_clock == 50: return True
        return False

    def check_for_endgame(self) -> bool:
        return StockfishIntegrationAI(self.get_current_state().to_fen()).best_move() == None

    def check_draw(self, check_for_endgame:bool=True, game:ChessGame=None) -> bool:
        if check_for_endgame and not self.check_for_endgame(): return False
        if game is None: game:ChessGame = ChessGame(self.get_current_state().to_list(), self.get_current_state().to_fen())
        for colour in [True, False]:
            if game.is_check(colour): return False
        return True

    def check_white_win(self, check_for_endgame:bool=True, game:ChessGame=None) -> bool:
        if check_for_endgame and not self.check_for_endgame(): return False
        if game is None: game:ChessGame = ChessGame(self.get_current_state().to_list(), self.get_current_state().to_fen())
        return game.is_check(False)
    
    def check_black_win(self, check_for_endgame:bool=True, game:ChessGame=None) -> bool:
        if check_for_endgame and not self.check_for_endgame(): return False
        if game is None: game:ChessGame = ChessGame(self.get_current_state().to_list(), self.get_current_state().to_fen())
        return game.is_check(True)

    def state_flag(self, set:bool=False) -> GameConclusionFlag:
        flag:GameConclusionFlag = GameConclusionFlag.NONE
        if not self.check_for_endgame():
            game:ChessGame = ChessGame(self.get_current_state().to_list(), self.get_current_state().to_fen())
            if self.check_draw(False,game): flag =  GameConclusionFlag.DRAW
            if self.check_black_win(False,game): flag = GameConclusionFlag.BLACK_WON
            if self.check_white_win(False,game): flag =  GameConclusionFlag.WHITE_WON
            if self.check_for_repetition(): flag = GameConclusionFlag.DRAW_BY_REPETITION
            if self.fifty_move_draw(): flag = GameConclusionFlag.DRAW_BY_50_MOVES
        if set: self.state = flag.id()
        return flag

    def get_moves_count(self) -> int: return len(self.game_state)//2

    def is_timed(self) -> bool: return self.time_limit != -1


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

    def __eq__(self, other:'GameState'):
        if (self.placement == other.placement and self.turn == other.turn and
        self.white_castle_queen_side == other.white_castle_queen_side and
        self.black_castle_queen_side == other.black_castle_queen_side and
        self.black_castle_king_side == other.black_castle_king_side and
        self.white_castle_king_side == other.black_castle_king_side and
        self.turn == other.turn): return True
        return False

    def is_white_turn(self)->bool:
        return True if self.turn == 'w' else False

    def is_black_turn(self)->bool:
        return True if self.turn == 'b' else False

    def ended(self)->bool:
        if StockfishIntegrationAI(self.to_fen()).best_move is None: return True
        return False

    def is_draw(self)->bool:
        if not self.ended(): return False
        game:ChessGame = ChessGame(self.to_list(), self.to_fen())
        if game.is_check(True) or game.is_check(False): return False
        return True

    def black_won(self)->bool:
        if not self.ended() or self.is_draw(): return False
        if self.turn == 'w': return True
        return False

    def white_won(self)->bool:
        if not self.ended() or self.is_draw(): return False
        if self.turn == 'b': return True
        return False

    def toggle_turn(self):
        self.turn = 'w' if self.turn == 'b' else 'b'
        db.session.commit()

    def set(self,fen:str):
        attr = fen.split(' ')
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

    def __str__(self) -> str:
        return f"""{self.placement} {self.turn} {'K' if self.white_castle_king_side else ''}{'Q' if self.white_castle_queen_side else ''}{'k' if self.black_castle_king_side else ''}{'q' if self.black_castle_queen_side else ''} {self.en_passent} {self.half_move_clock} {self.move}
        """


    def to_fen(self)->str:
        result = '' + self.placement + ' ' + self.turn + ' '
        if self.white_castle_king_side: result += 'K'
        if self.white_castle_queen_side: result += 'Q'
        if self.black_castle_king_side: result += 'k'
        if self.black_castle_queen_side: result += 'q'
        if not self.white_castle_king_side and not self.white_castle_queen_side and not self.black_castle_king_side and not self.black_castle_queen_side: result += '-'
        result += ' ' + self.en_passent + ' ' + str(self.half_move_clock) + ' ' + str(self.move) 
        return result
        
    def to_list(self)->list:
        result = list()
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
        print(user)
        if self.min_rank <= user.elo <= self.max_rank and mmrequest.min_rank <= self.user.elo <= mmrequest.max_rank and self.ranked == mmrequest.ranked:
            return True
        return False

    def jsonify(self):
        return {'id': self.id, 'ranked': self.ranked, 'min_rank': self.min_rank, 'max_rank': self.max_rank, 'time': self.time, 'user_id':self.user_id}

    @classmethod
    def from_json(self, obj:dict):
        return MatchmakerRequest.query.filter_by(id=obj.get('id')).first()




class EloUserRating(ITimeStampedModel):
    id = db.Column(db.Integer, primary_key=True)
    rapid = db.Column(db.Integer, default=400)
    blitz = db.Column(db.Integer, default=400)
    standard = db.Column(db.Integer, default=400)
    bullet = db.Column(db.Integer, default=400)
    puzzles = db.Column(db.Integer, default=400)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='ratings')

    def by_name(self, name:str) -> int:
        return self.jsonify().get(name) 

    def update(self, name:str, new_val:int):
        print(new_val)
        print(name)
        if new_val < 0: return
        if name == 'rapid': self.rapid = new_val 
        elif name == 'blitz': self.blitz = new_val 
        elif name == 'bullet': self.blitz = new_val 
        elif name == 'standard': self.blitz = new_val 
        elif name == 'puzzles': self.blitz = new_val 
        db.session.commit()
        print(self.jsonify())

    @staticmethod
    def names() -> list:
        return ['rapid', 'blitz', 'standard', 'bullet', 'puzzles']

    def jsonify(self) -> dict:
        return {'created':self.timestamp_creation,
            'rapid': self.rapid,
            'blitz': self.blitz,
            'standard' : self.standard,
            'bullet' : self.bullet,
            'puzzles' : self.puzzles
        }
                    









