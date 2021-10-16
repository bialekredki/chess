
def game_check_empty(game:list,t:list):
    r = game[t[0]]
    tile = r[t[1]]
    if tile['piece'] == 0: return True
    return False

def game_check_for_opponents(game:list, t:list, colour:bool):
    r = game[t[0]]
    tile = r[t[1]]
    if game_check_empty(game, t) or tile['colour'] == colour: return False
    return True

def game_get_possible_moves(game:list,location:list)->list:
    r = game[location[0]]
    source = r[location[1]]
    if source['piece'] == 0: return None
    moves = list()
    if source['piece'] == 1:
        direction = 1 if source['colour'] else -1
        if not source['moved'] and game_check_empty(game, [location[0]+2*direction, location[1]]):
            moves.append([location[0]+2*direction, location[1]])
        if game_check_empty(game, [location[0]+1*direction, location[1]]):
            moves.append([location[0]+1*direction, location[1]])
        for tile in [[location[0]+1*direction, location[1]+a] for a in [-1,1]]:
            print(tile)
            if not 0<=tile[0]<=7 or not 0<=tile[1]<=7: continue
            if game_check_for_opponents(game,tile,source['colour']):
                moves.append(tile)
        
    print(moves)
    print(source)