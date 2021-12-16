import random
from enum import Enum
from typing import Union
from stockfish import Stockfish

AI_INTEGRATIONS_NAMES_LIST=['Stupid', 'Stockfish-1', 'Stockfish-2', 'Stockfish-3', 'Stockfish-4', 'Stockfish-5', 'Stockfish-6', 'Stockfish-7', 'Stockfish-8','Stockfish-9']
PREFERRED_INTEGRATION = 'Stockfish-9'

class EvaluationMethod(Enum):
    CENTIPAWN = 0
    PERCENTAGE = 1
    MATE = 2
    ALL = 3

def get_ai(name:str,fen:str=None):
    if name == 'Stupid':
        return StupidAI()
    else:
        ai = name.split('-')
        return StockfishIntegrationAI(fen,int(ai[1]))

class AI():
    __abstract__=True
    def make_move(self):
        pass
    def is_possible(self,move:str) -> bool:
        pass

    def eval_mate_to_centipawns(self, mate:int) -> int:
        return 10000-(100*mate) if mate >= 0 else 10000

    def eval_to_percent(self, eval:dict) -> float:
        if eval['type'] == 'cp': val = eval['value']
        else: val = self.eval_mate_to_centipawns(eval['value'])
        return 1 / (1+10**(-(val/100)/4))

class StupidAI(AI):
    def make_stupid_move(self,moves:list):
        return moves[random.randint(0,len(moves)-1)]

class StockfishIntegrationAI(AI):
    stockfish_path = './ai/bin/stockfish'

    def __init__(self,FEN:str,level:int=15, parameters:dict=None):
        self.engine = Stockfish(self.stockfish_path, parameters=parameters)
        self.engine.set_fen_position(FEN, False)
        self.engine.set_skill_level(level)

    def make_move(self, FEN:str, level:int):
        pass

    def best_move(self):
        return self.engine.get_best_move()

    def move(self, move:str)->str:
        self.engine.make_moves_from_current_position([move])
        return self.engine.get_fen_position()

    def is_possible(self,move:str)->bool:
        return self.engine.is_move_correct(move)

    def has_ended(self)->bool:
        return True if self.engine.get_best_move() is None else False

    def get_eval(self,method:EvaluationMethod=EvaluationMethod.PERCENTAGE)->'Union[float,int]':
        eval = self.engine.get_evaluation()
        if method == EvaluationMethod.PERCENTAGE:
            return eval['value']/100 if eval['type'] == 'cp' else 100
        elif method == EvaluationMethod.PERCENTAGE:
            return self.eval_to_percent(eval) * 100
        elif method == EvaluationMethod.MATE:
            return eval['value'] if eval['type'] == 'mate' else None
        else:
            return {'cp': eval['value']/100 if eval['type'] == 'cp' else self.eval_mate_to_centipawns(eval['value']),
                'percentage': self.eval_to_percent(eval) * 100,
                'mate': eval['value'] if eval['type'] == 'mate' else None
            }