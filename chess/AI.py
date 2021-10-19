import random

def get_ai(name:str):
    if name == 'Stupid':
        return StupidAI()

class StupidAI:
    def make_stupid_move(self,moves:list):
        return moves[random.randint(0,len(moves)-1)]