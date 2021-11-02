from chess import app, db, socketio
from chess.models import User, Game, GameState
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
    print(game.get_current_state().to_fen())
    chess_game = ChessGame(game.game_state[-1].to_list(), game.game_state[-1].to_fen())
    if current_user.id != game.host_id and current_user.id != game.guest_id:
        return #TODO: Handle discrepancies on server-client
    print([move.jsonify()['to'] for move in chess_game.get_moves(js['from'])])
    socketio.emit('setpossiblemoves', {'moves': [move.jsonify()['to'] for move in chess_game.get_moves(js['from'])], 'to':current_user.id}, namespace=f'/game-{game.id}')
    

@socketio.on('confirmmove')
def confirm_move(js, methods='GET'):
    app.logger.info("Move request\n%s", str(js))
    id = js['gameid']
    game:Game = Game.query.filter_by(id=id).first()
    current_state = game.get_current_state()
    print(current_state.to_fen())
    if not current_user.is_in_game(game):
        app.logger.info("%s submitted a move without permission[guest]", current_user.username)
        return
    if current_user.plays_as_black(game) and current_state.is_white_turn():
        app.logger.info("%s submitted a move outside his turn[white]", current_user.username)
        return
    if current_user.plays_as_white(game) and current_state.is_black_turn():
        app.logger.info("%s submitted a move outside his turn[black]", current_user.username)
        return
    sf = StockfishIntegrationAI(current_state.to_fen())
    print(current_state.to_fen())
    print(sf.engine.get_board_visual())
    move = Move(js['from'], js['to'])
    move = move.algebraic()
    cg = ChessGame(current_state.to_list(), current_state.to_fen())
    if js['to'][0] == 7 and cg.at(js['from']).piece == PieceType.PAWN.value and cg.at(js['from']).colour or js['to'][0] == 0 and cg.at(js['from']).piece == PieceType.PAWN.value and not cg.at(js['from']).colour:
        move += 'Q'
    if not sf.is_possible(move):
        app.logger.info('%s submitted impossible move', current_user.username)
        return
    print(sf.engine.get_board_visual())
    fen = sf.move(move)
    print(sf.engine.get_board_visual())
    new_state = GameState()
    game.game_state.append(new_state)
    new_state.set(fen)
    print('MOVE PLAYER', new_state.to_fen())
    if game.AI is not None and ((current_user.plays_as_white(game) and new_state.is_black_turn()) or (current_user.plays_as_black(game) and new_state.is_white_turn())):
        ai = get_ai(game.AI, new_state.to_fen())
        move = ai.best_move()
        fen = ai.move(move)
        new_state = GameState()
        new_state.set(fen)
        game.game_state.append(new_state)
        print(new_state.to_fen())
        move = Move.from_algebraic(move)
        if game.show_eval_bar:
            eval = StockfishIntegrationAI(game.get_current_state().to_fen(), 15).engine.get_evaluation()
            eval = eval['value']
            print(eval)
            if eval < -2000: eval = -2000
            if eval > 2000: eval = 2000
            print(eval)
            eval = ((eval + 2000)/(4000))*100
            print(eval)
            socketio.emit('setgame', {'tiles': game.game_state[-1].to_list(), 'eval': eval}, namespace=f'/game-{game.id}')
        else:
            socketio.emit('setgame', {'tiles': game.game_state[-1].to_list()}, namespace=f'/game-{game.id}')
            print('Second')
    else:
            if game.show_eval_bar:
                eval = StockfishIntegrationAI(game.get_current_state().to_fen(), 15).engine.get_evaluation()
                eval = eval['value']
                print(eval)
                if eval < -2000: eval = -2000
                if eval > 2000: eval = 2000
                print(eval)
                eval = ((eval + 2000)/(4000))*100
                print(eval)
                socketio.emit('setgame', {'tiles': game.game_state[-1].to_list(), 'eval': eval}, namespace=f'/game-{game.id}')
            else:
                socketio.emit('setgame', {'tiles': game.game_state[-1].to_list()}, namespace=f'/game-{game.id}')
    db.session.commit()