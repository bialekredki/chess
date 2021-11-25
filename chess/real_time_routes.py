from chess import app, db, socketio
from chess.models import User, Game, GameState
from chess.game_options import PlayerMovePermission
from chess.AI import EvaluationMethod, StockfishIntegrationAI, get_ai
from chess.game import Game as ChessGame, Move, PieceType
from flask_login import current_user

@socketio.on('getgame')
def set_game(js,methods='GET'):
    game:Game = Game.query.filter_by(id=js['id']).first()
    app.logger.info('[SOCKET] %s received', str(js))
    result = dict()
    result['tiles'] = game.get_current_state().to_list()
    sf = StockfishIntegrationAI(game.get_current_state().to_fen())
    if game.show_eval_bar:  result['eval'] = sf.get_eval(EvaluationMethod.PERCENTAGE)
    result['ended'] = sf.has_ended()
    socketio.emit('setgame', result, namespace=f'/game-{game.id}')

@socketio.on('getcolour')
def set_colour(js,methods='GET'):
    game:Game = Game.query.filter_by(id=js['id']).first()
    user:User = User.query.filter_by(id=js['player_id']).first()
    if not user.is_in_game(game): return
    socketio.emit('setcolour',{'colour':user.plays_as_white(game)})

@socketio.on('getpossiblemoves')
def get_possible_moves(js, methods=['GET']):
    id = js['gameid']
    game:Game = Game.query.filter_by(id=id).first()
    sf = StockfishIntegrationAI(game.get_current_state().to_fen())
    if sf.has_ended():   
        gs = game.get_current_state().turn
        game.state = 1 if gs == 'b' else 2
        print(game.state)
        db.session.commit()
        socketio.emit('setpossiblemoves', {'moves': [], 'to':current_user.id}, namespace=f'/game-{game.id}')
        return
    chess_game = ChessGame(game.game_state[-1].to_list(), game.game_state[-1].to_fen())
    if current_user.id != game.host_id and current_user.id != game.guest_id:
        return #TODO: Handle discrepancies on server-client
    socketio.emit('setpossiblemoves', {'moves': [move.jsonify()['to'] for move in chess_game.get_moves(js['from'])], 'to':current_user.id}, namespace=f'/game-{game.id}')


@socketio.on('confirmmove')
def confirm_move(js, methods='GET'):
    response_object = dict()
    app.logger.info("Move request\n%s", str(js))
    id = js['gameid']
    game:Game = Game.query.filter_by(id=id).first()
    current_state = game.get_current_state()
    permission = game.can_player_move(current_user)
    if permission != PlayerMovePermission.YES:
        app.logger.info("%s submitted a move without permission[%s]", current_user.username, permission.reason())
        return
    move = Move(js['from'], js['to']).algebraic()
    cg = ChessGame(current_state.to_list(), current_state.to_fen())
    if js['to'][0] == 7 and cg.at(js['from']).piece == PieceType.PAWN.value and cg.at(js['from']).colour or js['to'][0] == 0 and cg.at(js['from']).piece == PieceType.PAWN.value and not cg.at(js['from']).colour:
        move += 'Q'
    if not game.move(move, game.get_current_state().is_white_turn()): return
    if game.AI is not None:
        ai = get_ai(game.AI, game.get_current_state().to_fen())
        game.move(ai.best_move(), game.get_current_state().to_fen())
    if game.show_eval_bar:
        response_object['eval'] = game.evaluate()
    print('STATE ', game.state)
    response_object['tiles'] = game.get_current_state().to_list()
    db.session.commit()
    socketio.emit('setgame', response_object, namespace=f'/game-{game.id}')

"""@socketio.on('confirmmove')
def confirm_move(js, methods='GET'):
    app.logger.info("Move request\n%s", str(js))
    id = js['gameid']
    game:Game = Game.query.filter_by(id=id).first()
    current_state = game.get_current_state()
    permission = game.can_player_move(current_user)
    if permission != PlayerMovePermission.YES:
        app.logger.info("%s submitted a move without permission[%s]", current_user.username, permission.reason())
        return
    sf = StockfishIntegrationAI(current_state.to_fen())
    move = Move(js['from'], js['to'])
    move = move.algebraic()
    cg = ChessGame(current_state.to_list(), current_state.to_fen())
    if js['to'][0] == 7 and cg.at(js['from']).piece == PieceType.PAWN.value and cg.at(js['from']).colour or js['to'][0] == 0 and cg.at(js['from']).piece == PieceType.PAWN.value and not cg.at(js['from']).colour:
        move += 'Q'
    if not sf.is_possible(move):
        app.logger.info('%s submitted impossible move', current_user.username)
        return
    fen = sf.move(move)
    new_state = GameState()
    game.game_state.append(new_state)
    new_state.set(fen)
    if game.AI is not None and ((current_user.plays_as_white(game) and new_state.is_black_turn()) or (current_user.plays_as_black(game) and new_state.is_white_turn())):
        ai = get_ai(game.AI, new_state.to_fen())
        print(ai.engine.get_board_visual())
        move = ai.best_move()
        fen = ai.move(move)
        new_state = GameState()
        new_state.set(fen)
        game.game_state.append(new_state)
        print(str(new_state))
        move = Move.from_algebraic(move)
        if game.show_eval_bar:
            eval = sf.get_eval()
            if eval < -2000: eval = -2000
            if eval > 2000: eval = 2000
            eval = ((eval + 2000)/(4000))*100
            socketio.emit('setgame', {'tiles': game.game_state[-1].to_list(), 'eval': eval}, namespace=f'/game-{game.id}')
        else:
            socketio.emit('setgame', {'tiles': game.game_state[-1].to_list()}, namespace=f'/game-{game.id}')
    else:
            if game.show_eval_bar:
                eval = sf.get_eval()
                if eval < -2000: eval = -2000
                if eval > 2000: eval = 2000
                eval = ((eval + 2000)/(4000))*100
                socketio.emit('setgame', {'tiles': game.game_state[-1].to_list(), 'eval': eval}, namespace=f'/game-{game.id}')
            else:
                socketio.emit('setgame', {'tiles': game.game_state[-1].to_list()}, namespace=f'/game-{game.id}')
    db.session.commit()"""