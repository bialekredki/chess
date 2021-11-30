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

    def model_name(self) -> str:
        return self.value['id'].split('_')[0]

    def is_bullet(self) -> bool:
        return self.value['id'].split('_')[0] == 'bullet'

    def is_blitz(self) -> bool:
        return self.value['id'].split('_')[0] == 'blitz'

    def is_rapid(self) -> bool:
        return self.value['id'].split('_')[0] == 'rapid'

    def is_standard(self) -> bool:
        return self.value['id'].split('_')[0] == 'standard'

    @classmethod
    def all(self):
        return [f.value for f in GameFormat]

    @classmethod
    def by_id(self,id:str):
        for f in GameFormat:
            if id == f.value.get('id'): return f

    @classmethod
    def by_name(self,name:str):
        for f in GameFormat:
            print(name, f.value.get('name'))
            if name == f.value.get('name'): return f

    @classmethod
    def by_time(self, time:int):
        for f in GameFormat:
            if f.value.get('time') == time: return f


class PlayerMovePermission(enum.Enum):
    GUEST = (False, 'guest')
    NO = (False, 'other turn')
    YES = (True, 'yes')

    def reason(self): return self.value[1]
    def permission(self): return self.value[0]


class GameConclusionFlag(enum.Enum):
    NONE = {'id': 0, 'str': None}
    DRAW = {'id': 1, 'str': 'Draw'}
    DRAW_BY_REPETITION = {'id': 2, 'str': 'Draw by repetion'}
    DRAW_BY_50_MOVES = {'id': 3, 'str': 'Draw by 50 moves rule'} 
    WHITE_WON = {'id': 4, 'str': 'White won'}
    BLACK_WON = {'id': 5, 'str': 'Black won'}


    def id(self) -> int: return self.value['id']

    def text(self) -> str: return self.value['str']

    @classmethod
    def draws_ids(self) -> 'list[int]':
        return [x.id() for x in [GameConclusionFlag.DRAW, GameConclusionFlag.DRAW_BY_50_MOVES, GameConclusionFlag.DRAW_BY_REPETITION]]
    @classmethod
    def ids(self):
        return [flag['id'] for flag in GameConclusionFlag]

class ChessTitle(enum.Enum):
    NONE = {'id': 0, 'name': 'Grandmaster', 'short': ''}
    GRANDMASTER = {'id': 1, 'name': 'Grandmaster', 'short': 'GM'}
    INTERNATIONAL_MASTER = {'id': 2, 'name': 'International Master', 'short': 'IM'}
    FIDE_MASTER = {'id':3, 'name': 'FIDE Master', 'short': 'FM'}
    CANDIDATE_MASTER = {'id': 4, 'name': 'Candidate Master', 'short': 'CM'}
    W_GRANDMASTER = {'id': 5, 'name': 'Woman Grandmaster', 'short': 'WGM'}
    W_INTERNATIONAL_MASTER = {'id': 6, 'name':'Woman International Master', 'short':'WIM'}
    W_FIDE_MASTER = {'id':7, 'name': 'Woman FIDE Master', 'short': 'WFM'}
    W_CANDIDATE_MASTER = {'id': 8, 'name': 'Woman Candidate Master', 'short': 'WCM'}

    @classmethod
    def by_id(self, id:int):
        for e in self:
            if id == e.value.get('id'): return e 

    def id(self) -> int: return self.value.get('id')
    def name(self) -> str: return self.value.get('name')
    def short(self) -> str: return self.value.get('short')

