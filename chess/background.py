from datetime import time

from celery.app.base import Celery
from chess import app, db, socketio, celery
from chess.game_options import GameConclusionFlag
from chess.models import MatchmakerRequest, User, Game, GameState
from chess.AI import StockfishIntegrationAI, get_ai
from chess.game import Game as ChessGame, Move, PieceType
from flask_login import current_user
from celery.utils.log import get_task_logger
from celery.schedules import crontab

logger = get_task_logger(__name__)

def on_raw_message(body):
    app.logger.info(body)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender:Celery, **kwargs):
    pass
    logger.info('Starting periodic tasks configuration on %s', sender)
    logger.info('[BACKGROUND][PERIODIC] starting periodic %s', sender.add_periodic_task(.02, check_expired_games.s()))

@celery.task(bind=True)
def matchmaker_task(self, r:dict,requests:'list[dict]'):
    r = MatchmakerRequest.from_json(r)
    print(r.user_id)
    u:User = User.query.filter_by(id=r.user_id).first()
    print(u)
    possible_requests = list()
    while len(possible_requests) == 0:
        for request in requests:
            request = MatchmakerRequest.from_json(request)
            print(request.jsonify())
            if request == r: continue
            print(request.jsonify())
            if r.fulfills_conditions(request): possible_requests.append(request)
    possible_requests.sort(key=lambda x: abs(u.elo - x.user.elo ))
    return possible_requests[0].jsonify()

@celery.task
def check_expired_games():
    games:list[Game] = Game.query.filter(Game.time_limit != - 1).all()
    for game in games:
        if game.get_time_left(False) <= 0:
            game.state = GameConclusionFlag.WHITE_WON.id()
        if game.get_time_left(True) <= 0:
            game.state = GameConclusionFlag.BLACK_WON.id()
        db.session.commit()


@celery.task
def check_expired_game_inviations():
    pass

@celery.task
def game_tick(id:int): 
    pass