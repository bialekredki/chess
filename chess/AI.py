import random

AI_INTEGRATIONS_NAMES_LIST=['Stupid', 'Stockfish-1', 'Stockfish-2', 'Stockfish-3', 'Stockfish-4', 'Stockfish-5', 'Stockfish-6', 'Stockfish-7', 'Stockfish-8','Stockfish-9']

def get_ai(name:str):
    if name == 'Stupid':
        return StupidAI()

class AI():
    __abstract__=True
    def make_move(self):
        pass

class StupidAI(AI):
    def make_stupid_move(self,moves:list):
        return moves[random.randint(0,len(moves)-1)]

class StockfishIntegrationAI(AI):
    pass