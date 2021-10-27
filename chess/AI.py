import random
from stockfish import Stockfish

AI_INTEGRATIONS_NAMES_LIST=['Stupid', 'Stockfish-1', 'Stockfish-2', 'Stockfish-3', 'Stockfish-4', 'Stockfish-5', 'Stockfish-6', 'Stockfish-7', 'Stockfish-8','Stockfish-9']

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

class StupidAI(AI):
    def make_stupid_move(self,moves:list):
        return moves[random.randint(0,len(moves)-1)]

class StockfishIntegrationAI(AI):
    stockfish_path = '/home/oskar/stockfish/sf/stockfish'

    def __init__(self,FEN:str,level:int=15):
        self.engine = Stockfish(self.stockfish_path)
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