
from typing import Union
import enum
import json
from chess.AI import StupidAI

class Tile:
    def __init__(self):
        self.piece = 0 
        self.colour = False
        self.moved = False

    def __repr__(self) -> str:
        return f'<Tile {[self.piece,self.colour,self.moved]}>'

    def jsonify(self) -> dict:
        return {'piece':self.piece, 'colour': self.colour, 'moved': self.moved}

    def is_empty(self)->bool:
        return True if self.piece == 0 else False


class MovesOrdering(enum.Enum):
        BY_NONE = 0
        BY_SOURCE = 1
        BY_DESTINATION = 2

class PieceType(enum.Enum):
    NONE = 0
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6

class Game:
    backRowSetup = [PieceType.ROOK.value, PieceType.KNIGHT.value, PieceType.BISHOP.value, PieceType.QUEEN.value, PieceType.KING.value, PieceType.BISHOP.value, PieceType.KNIGHT.value, PieceType.ROOK.value]
    def at(self, t:list)->Tile:
        return self.tiles[t[0]][t[1]]
    def is_tile_empty(self, t:list)->bool:
        return True if self.at(t).is_empty() else False
    def is_tile_oponent(self,t:list,colour:bool)->bool:
        return True if not self.is_tile_empty(t) and self.at(t).colour != colour else False
    def is_tile_own(self,t:list,colour:bool)->bool:
        return True if not self.is_tile_empty(t) and self.at(t).colour == colour else False
    def is_tile_inbounds(self,t:list)->bool:
        return True if 0<=t[0]<=7 and 0<=t[1]<=7 else False 
    def add_vectors(self,t:list,v:list)->list:
        return [t[0]+v[0], t[1]+v[1]]

    def get_moves(self,source:list, collision:bool=True)->list:
        if self.is_tile_empty(source): return []
        tile = self.at(source)
        if tile.piece == 1: return self.get_pawn_moves(tile, source, collision=collision)
        if tile.piece == 2: return self.get_horsie_moves(tile, source, collision=collision)
        if tile.piece == 3: return self.get_bishop_moves(tile,source, collision=collision)
        if tile.piece == 4: return self.get_rook_moves(tile,source, collision=collision)
        if tile.piece == 5: return self.get_queen_moves(tile,source, collision=collision)
        if tile.piece == 6: return self.get_king_moves(tile,source, collision=collision)

    def get_all_moves(self,colour:bool=None, order_by:MovesOrdering=MovesOrdering.BY_NONE, depth:bool=True, collision:bool=True)->Union[dict,list]:
        if order_by == MovesOrdering.BY_NONE:
            moves = list()
        else:
            moves = dict()

        if self.check and self.turn == colour:
            print('Check detected for ', colour)
            king = self.find_king(colour)
            king_xy = king['xy']
            king = king['tile']
            print('King on ', king_xy, ' ', king)
            print('King can run to', self.get_king_moves(king, king_xy))
            for move in self.get_king_moves(king, king_xy):
                print((king_xy, move))
                moves.append((king_xy, move))
            self.check = False
            mo = self.get_all_moves(colour=not colour, order_by=MovesOrdering.BY_DESTINATION)
            m = self.get_all_moves(colour=colour, order_by=MovesOrdering.BY_DESTINATION)
            self.check = True
            print('King is endangered by ',mo.get(king_xy))
            print('Danger can be neutralised by', [m.get(tuple(x)) for x in mo.get(tuple(king_xy))])
            for opo in mo.get(tuple(king_xy)):
                if tuple(opo) not in m: continue
                for my in m.get(tuple(opo)):
                    print((my, opo))
                    moves.append((my, opo))
            return moves
            

        for r,row in enumerate(self.rows):
            for c,tile in enumerate(row.tiles):
                if  tile.is_empty() or colour is not None and tile.colour != colour: continue
                if not depth and tile.piece == 6: continue
                tile_moves = self.get_moves([r,c], collision=collision)
                if tile_moves is None: continue
                if order_by == MovesOrdering.BY_SOURCE:
                    moves[(r,c)] = tile_moves
                    continue
                for move in tile_moves:
                    if order_by == MovesOrdering.BY_NONE:
                        moves.append(([r,c], move))
                    if order_by == MovesOrdering.BY_DESTINATION:
                        key = tuple(move)
                        if moves.get(key) is None:
                            moves[key] = list()
                        moves[key].append([r,c])
        return moves

    def row(self,r:int,start:int=0,step:int=1)->list:
        if not 0<=r<=7 and 0<=start<=7 and -7<=step<=7 and step != 0: return list()
        if step < 0: stop = -8
        else: stop = 8
        return self.rows[r].tiles[start:stop:step]

    def row_xy(self,r:int,start:int=0,step:int=1)->list:
        return [t.xy() for t in self.row()]

    def col(self,c:int,start:int=0,step:int=1)->list:
        if not 0<=c<=7 and 0<=start<=7 and -7<=step<=7 and step != 0: return list()
        if step < 0: stop = -8
        else: stop = 8
        res = list()
        for x in range(start,stop,step):
            res.append(self.rows[x].tiles[c])
        return res

    def col_xy(self,c:int,start:int=0,step:int=1)->list:
        return [t.xy() for t in self.col()]

    def diagonal(self,start:Union[list,tuple],direction:list=None)->list:
        if direction is None: direction = ['up','left']
        ranges = list()
        if 'up' in direction:
            ranges.append(range(1,8))
        elif 'down' in direction:
            ranges.append(range(-1,-8,-1))
        else: return list()
        if 'right' in direction:
            ranges.append(range(1,8))
        elif 'left' in direction:
            ranges.append(range(-1,-8,-1))
        else: return list()
        tiles = list()
        for x in range(7):
            tile = self.add_vectors(start,[ranges[0][x],ranges[1][x]])
            if not self.is_tile_inbounds(tile): continue
            tiles.append(tile)
        return tiles

                

    def compare_with_js(self,js:list)->bool:
        for row in range(8):
            for col in range(8):
                server_tile = self.at([row,col])
                client_tile = js[row][col]
                if server_tile.piece != client_tile['piece'] or server_tile.colour != client_tile['colour'] or server_tile.moved != client_tile['moved']: 
                    print(f'{server_tile}\t{client_tile}')
                    return False
        return True

    def get_pawn_moves(self,pawn:Tile,source:list, collision:bool=True)->list:
        moves = list()
        direction = 1 if pawn.colour else -1
        after_vector = self.add_vectors(source,[2*direction,0])
        if not pawn.moved and self.is_tile_empty(after_vector):
            moves.append(after_vector)
        after_vector = self.add_vectors(source,[direction,0])
        if self.is_tile_empty(after_vector):
            moves.append(after_vector)
        for tile in [[source[0]+1*direction, source[1]+a] for a in [-1,1]]:
            if not self.is_tile_inbounds(tile): continue
            if self.is_tile_oponent(tile, pawn.colour) or not collision and self.is_tile_own(tile, pawn.colour):
                moves.append(tile)
        return moves

    def get_horsie_moves(self,horsie:Tile,source:list, collision:bool=True)->list:
        moves = list()
        vectors = list()
        for x in [-2,-1,1,2]:
            for y in [-2,-1,1,2]:
                if x % 2 != y % 2:
                    vectors.append([x,y])
        for vector in vectors:
            after_vector = self.add_vectors(source,vector)
            if  not self.is_tile_inbounds(after_vector): continue
            if  not collision and self.is_tile_own(after_vector, horsie.colour) or  not self.is_tile_own(after_vector, horsie.colour):
                moves.append(after_vector)
        return moves

    def get_bishop_moves(self,bishop:Tile,source:list, collision:bool=True)->list:
        moves = list()
        diagonals = [self.diagonal(source,d) for d in [['up','left'], ['up', 'right'], ['down', 'right'], ['down', 'left']]]
        for diagonal in diagonals:
            for tile in diagonal:
                if self.is_tile_own(tile, bishop.colour) and collision: break
                moves.append(tile)
                if self.is_tile_oponent(tile, bishop.colour) or self.is_tile_own(tile, bishop.colour): break
        return moves

    def get_rook_moves(self,rook:Tile,source:list, collision:bool=True)->list:
        moves = list()
        for x in [-1,1]:
            for r in range(1*x,8*x,x):
                tile = self.add_vectors(source, [0,r])
                if not self.is_tile_inbounds(tile): break
                if self.is_tile_own(tile, rook.colour) and collision: break
                moves.append(tile)
                if self.is_tile_oponent(tile, rook.colour) or self.is_tile_own(tile, rook.colour) : break
        for x in [-1,1]:
            for r in range(1*x,8*x,x):
                tile = self.add_vectors(source, [r,0])
                if not self.is_tile_inbounds(tile): break
                if self.is_tile_own(tile, rook.colour) and collision: break
                moves.append(tile)
                if self.is_tile_oponent(tile, rook.colour) or self.is_tile_own(tile, rook.colour) : break
        return moves

        

    def get_queen_moves(self,queen:Tile, source:list, collision:bool=True)->list:
        return self.get_bishop_moves(queen, source,collision) + self.get_rook_moves(queen, source,collision)

    def get_king_moves(self, king:Tile, source:list, depth:bool=True, collision:bool=True)->list:
        moves = list()
        if depth:
            opponents_moves = self.get_all_moves(colour=not king.colour, order_by=MovesOrdering.BY_DESTINATION, depth=False, collision=False)
        else:
            opponents_moves = []
        for x in [-1,0,1]:
            for y in [-1,0,1]:
                if x == 0 and y == 0: continue
                tile = self.add_vectors(source, [x,y])
                if not self.is_tile_inbounds(tile) or tuple(tile) in opponents_moves.keys(): continue
                if collision and self.is_tile_own(tile, king.colour): continue
                moves.append(tile)
        return moves

    def move(self,src:list,dest:list):
        tsrc = self.at(src)
        tdest = self.at(dest)
        tdest.piece = tsrc.piece
        tdest.colour = tsrc.colour
        tdest.moved = True
        tsrc.piece = 0
        tsrc.colour = False
        tsrc.moved = False
        self.check = False

    def find_king(self,colour:bool):
        return None

    def is_check(self,colour:bool)->bool:
        if self.find_king(colour)['xy'] in self.get_all_moves(colour=not colour, order_by=MovesOrdering.BY_DESTINATION, depth=False, collision=False).keys(): return True
        return False

    def set_check(self,colour:bool):
        self.check = self.is_check(colour)

