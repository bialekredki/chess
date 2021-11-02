import enum
class GameOption(enum.Enum):
    EVAL_BAR = {'id':'bar', 'name':'Show evaluation bar', 'type':'checkbox'}
    RANKED = {'id':'ranked', 'name':'Ranked', 'type':'checkbox'}
    MIN_RANK = {'id':'min_rank', 'name':'Minimum rank', 'type':'range', 'upper_limit':'max_rank'}
    MAX_RANK = {'id':'max_rank', 'name':'Maximum rank', 'type':'range', 'lower_limit':'min_rank'}

    @classmethod
    def ai_options(self):
        return [GameOption.EVAL_BAR.value]
    
    @classmethod
    def human_options(self):
        return [GameOption.RANKED.value, GameOption.MIN_RANK.value, GameOption.MAX_RANK.value]

    @classmethod
    def getbyname(self,name:str):
        for option in list(self):
            if option.value['id'] == name: return option


    
class GameFormat(enum.Enum):
    BULLET05 = {'id': 'bullet_05', 'name': "Bullet 30''", 'time': 30, 'type':'btn'}
    BULLET1 =  {'id': 'bullet_1', 'name': "Bullet 1'", 'time': 60, 'type':'btn'}
    BULLET2 = {'id': 'bullet_2', 'name': "Bullet 2'", 'time': 120, 'type':'btn'}
    BLITZ3 = {'id': 'blitz_3', 'name': "Blitz 3'", 'time': 180, 'type':'btn'}
    BLITZ5 = {'id': 'blitz_5', 'name': "Blitz 5'", 'time': 60*5, 'type':'btn'}
    BLITZ10 = {'id': 'blitz_10', 'name': "Blitz 10'", 'time': 60*10, 'type':'btn'}
    RAPID20 = {'id': 'rapid_20', 'name': "Rapid 20'", 'time': 60*20, 'type':'btn'}
    RAPID30 = {'id': 'rapid_30', 'name': "Rapid 30'", 'time': 60*30, 'type':'btn'}
    STANDARD1 = {'id': 'standard_1', 'name': "Standard 1h'", 'time': 60*60, 'type':'btn'}
    STANDARD2 = {'id': 'standard_2', 'name': "Standard 2h'", 'time': 60*60*2, 'type':'btn'}

    @classmethod
    def all(self):
        return [f.value for f in GameFormat]

    @classmethod
    def by_id(self,id:str):
        for f in GameFormat:
            if id == f.value.get('id'): return f

