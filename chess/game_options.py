import enum
class GameOption(enum.Enum):
    EVAL_BAR = {'opt_id':'bar', 'opt_name':'Show evaluation bar', 'opt_type':'checkbox'}
    RANKED = {'opt_id':'ranked', 'opt_name':'Ranked', 'opt_type':'checkbox'}
    MIN_RANK = {'opt_id':'min_rank', 'opt_name':'Minimum rank', 'opt_type':'range'}
    MAX_RANK = {'opt_id':'max_rank', 'opt_name':'Maximum rank', 'opt_type':'range'}

    @classmethod
    def ai_options(self):
        return [GameOption.EVAL_BAR.value]
    
    @classmethod
    def human_options(self):
        return [GameOption.RANKED.value, GameOption.MIN_RANK.value, GameOption.MAX_RANK.value]


    
class GameFormat(enum.Enum):
    BULLET05 = {'format_id': 'bullet_05', 'format_name': "Bullet 30''", 'format_time': 30}
    BULLET1 =  {'format_id': 'bullet_1', 'format_name': "Bullet 1'", 'format_time': 60}
    BULLET2 = {'format_id': 'bullet_2', 'format_name': "Bullet 2'", 'format_time': 120}
    BLITZ3 = {'format_id': 'blitz_3', 'format_name': "Blitz 3'", 'format_time': 180}
    BLITZ5 = {'format_id': 'blitz_5', 'format_name': "Blitz 5'", 'format_time': 60*5}
    BLITZ10 = {'format_id': 'blitz_10', 'format_name': "Blitz 10'", 'format_time': 60*10}
    RAPID20 = {'format_id': 'rapid_20', 'format_name': "Rapid 20'", 'format_time': 60*20}
    RAPID30 = {'format_id': 'rapid_30', 'format_name': "Rapid 30'", 'format_time': 60*30}
    STANDARD1 = {'format_id': 'standard_1', 'format_name': "Standard 1h'", 'format_time': 60*60}
    STANDARD2 = {'format_id': 'standard_2', 'format_name': "Standard 2h'", 'format_time': 60*60*2}

    @classmethod
    def all(self):
        return [f.value for f in GameFormat]

