
from chess.models import Game
from chess.game import Game as ChessGame
import enum 
from chess.AI import StockfishIntegrationAI, EvaluationMethod

class ChessMoveClassification(enum.Enum):
    GENIUS = {'id': 0, 'name': 'Genius', 'eval_change': (15, 'inf')}
    GREAT = {'id':1, 'name': 'Great', 'eval_change': (5,15)}
    GOOD = {'id': 2, 'name':'Good', 'eval_change':(1.5,5)}
    NORMAL = {'id': 3, 'name': 'Normal', 'eval_change': (-1.5,1.5)}
    BAD = {'id': 4, 'name':'Bad', 'eval_change':(-5,-1.5)}
    MISTAKE = {'id':5, 'name': 'Great', 'eval_change': (-15,-5)}
    BLUNDER = {'id': 6, 'name': 'Blunder', 'eval_change': ('-inf',15)}

    @classmethod
    def by_change(self, change:int):
        for gmc in self:
            start = gmc.value['eval_change'][0]
            stop = gmc.value['eval_change'][1]
            if stop == 'inf' and change >= start: return gmc
            elif start == '-inf' and change <= stop: return gmc
            elif start <= change <= stop: return gmc

    def name(self) -> str: return self.value.get('name')


def classify_moves(game:Game) -> None:
    evals = list()
    moves_classification = list()
    moves = list()
    all = list()
    for i,state in enumerate(game.game_state):
        engine = StockfishIntegrationAI(state.to_fen(), parameters={"Threads": 3, "Minimum Thinking Time": 60, 'Contempt': 1, 'Ponder': True})
        engine.engine.set_depth(15)
        print(engine.engine.get_parameters())
        print(engine.engine.get_evaluation())
        cp = engine.get_eval(EvaluationMethod.ALL)
        evals.append({'cp': cp[0]/100, 'percentage': cp[1]*100})
        print(evals[-1])
        now = ChessGame(state.to_list(), state.to_fen())
        all.append({'fen': state.to_fen(), 'eval': evals[i], 'tiles': state.to_list()})
        if i == 0: 
            continue
        prev = ChessGame(game.game_state[i-1].to_list(), game.game_state[i-1].to_fen())
        moves.append(now.get_moves_between(prev))
        change:int = evals[i]['cp']-evals[i-1]['cp']
        if game.game_state[i-1].is_black_turn(): change *= -1
        moves_classification.append(ChessMoveClassification.by_change(change))
        all[-1]['colour'] = game.game_state[i-1].is_white_turn()
        all[-1]['move'] = moves[-1]
        all[-1]['classification'] = moves_classification[-1].name()
    return all

    