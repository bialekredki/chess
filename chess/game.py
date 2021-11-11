
from typing import Union
import enum
import json

from celery.utils.imports import cwd_in_path
from chess.AI import StupidAI, StockfishIntegrationAI

class Tile:
    def __init__(self,piece:int=0,colour:bool=False):
        self.piece = piece
        self.colour = colour

    def __repr__(self) -> str:
        return f'<Tile {[self.piece,self.colour,]}>'

    def __eq__(self, o: 'Tile') -> bool:
        if self.piece == o.piece and self.colour == o.colour: return True
        return False

    def jsonify(self) -> dict:
        return {'piece':self.piece, 'colour': self.colour}

    def is_empty(self)->bool:
        return True if self.piece == 0 else False

    @classmethod
    def algerbraic_to_xy(self, algebraic:str)->Union[list,tuple]:
        if type(algebraic) is not str or len(algebraic) != 2: raise ValueError(f"[{self} {__name__}] Incorrect algebraic {algebraic} coordinate to be converted into xy coordinates.")
        return (int(algebraic[1])-1,  ord(algebraic[0]) - ord('a'))

    @classmethod
    def xy_eq(self, position_1:Union[list,tuple], position_2:Union[list,tuple]):
        return True if position_1[0] == position_2[0] and position_1[1] == position_2[1] else False

def move_list_to_algebraic(move):
    return chr(move[0][0] + ord('a')) + str(move[0][1]+1) + chr(move[1][0] + ord('a')) + str(move[1][1]+1)


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

class Move:
    def __init__(self, src:Union[list,tuple], dest:Union[list,tuple]):
        self.src = src
        self.dest = dest

    # [0,0] -> 
    def algebraic(self)->str:
        return chr(self.src[1] + ord('a')) + str(self.src[0]+1) + chr(self.dest[1] + ord('a')) + str(self.dest[0]+1)

    def jsonify(self)->dict:
        return {'from':self.src, 'to':self.dest}

    @classmethod
    def from_algebraic(self,algebraic:str)->list:
        return [[int(algebraic[1]) - 1, ord(algebraic[0]) - ord('a')] , [int(algebraic[3])-1, ord(algebraic[2]) - ord('a')]]


class Game:
    
    def __init__(self, array:list, FEN:str=None):
        self.tiles = list()
        self.FEN = FEN
        for r,row in enumerate(array):
            self.tiles.append(list())
            for col in row:
                self.tiles[r].append(Tile(col['piece'], col['colour']))
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

    def get_moves(self,source:list, collision:bool=True)->'list[Move]':
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
        for r,row in enumerate(self.tiles):
            for c,tile in enumerate(row):
                if  tile.is_empty() or colour is not None and tile.colour != colour: continue
                if not depth and tile.piece == 6: continue
                tile_moves = self.get_moves([r,c], collision=collision)
                if tile_moves is None: continue
                if order_by == MovesOrdering.BY_SOURCE:
                    moves[(r,c)] = tile_moves
                    continue
                for move in tile_moves:
                    if order_by == MovesOrdering.BY_NONE:
                        moves.append(move)
                    if order_by == MovesOrdering.BY_DESTINATION:
                        key = tuple(move.dest)
                        if moves.get(key) is None:
                            moves[key] = list()
                        moves[key].append([r,c])
        return moves

    def row(self,r:int,start:int=0,step:int=1)->list:
        if not 0<=r<=7 and 0<=start<=7 and -7<=step<=7 and step != 0: return list()
        if step < 0: stop = -8
        else: stop = 8
        return self.tiles[r][start:stop:step]

    def row_xy(self,r:int,start:int=0,step:int=1)->list:
        return [t.xy() for t in self.row()]

    def col(self,c:int,start:int=0,step:int=1)->list:
        if not 0<=c<=7 and 0<=start<=7 and -7<=step<=7 and step != 0: return list()
        if step < 0: stop = -8
        else: stop = 8
        res = list()
        for x in range(start,stop,step):
            res.append(self.tiles[x][c])
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


    def is_en_passant_possible(self):
        return False if self.FEN.split(' ')[3] is None or self.FEN.split(' ')[3] == '-' else True

    def get_en_passant(self):
        return self.FEN.split(' ')[3]

    def en_passant(self):
        if not self.is_en_passant_possible(): return None
        return Tile.algerbraic_to_xy(self.get_en_passant())
                

    def compare_with_js(self,js:list)->bool:
        for row in range(8):
            for col in range(8):
                server_tile = self.at([row,col])
                client_tile = js[row][col]
                if server_tile.piece != client_tile['piece'] or server_tile.colour != client_tile['colour']: 
                    print(f'{server_tile}\t{client_tile}')
                    return False
        return True

    def get_pawn_moves(self,pawn:Tile,source:list, collision:bool=True)->list:
        moves = list()
        direction = 1 if pawn.colour else -1
        after_vector = self.add_vectors(source,[2*direction,0])
        en_passant = self.en_passant()
        if (source[0]==6 or source[0] == 1) and self.is_tile_inbounds(after_vector) and self.is_tile_empty(after_vector):
            moves.append(Move(source, after_vector))
        after_vector = self.add_vectors(source,[direction,0])
        if self.is_tile_empty(after_vector):
            moves.append(Move(source, after_vector))
        for tile in [[source[0]+1*direction, source[1]+a] for a in [-1,1]]:
            if not self.is_tile_inbounds(tile): continue
            if self.is_tile_oponent(tile, pawn.colour) or not collision and self.is_tile_own(tile, pawn.colour) or en_passant is not None and Tile.xy_eq(en_passant, tile):
                moves.append(Move(source, tile))
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
                moves.append(Move(source, after_vector))
        return moves

    def get_bishop_moves(self,bishop:Tile,source:list, collision:bool=True)->list:
        moves = list()
        diagonals = [self.diagonal(source,d) for d in [['up','left'], ['up', 'right'], ['down', 'right'], ['down', 'left']]]
        for diagonal in diagonals:
            for tile in diagonal:
                if self.is_tile_own(tile, bishop.colour) and collision: break
                moves.append(Move(source, tile))
                if self.is_tile_oponent(tile, bishop.colour) or self.is_tile_own(tile, bishop.colour): break
        return moves

    def get_rook_moves(self,rook:Tile,source:list, collision:bool=True)->list:
        moves = list()
        for x in [-1,1]:
            for r in range(1*x,8*x,x):
                tile = self.add_vectors(source, [0,r])
                if not self.is_tile_inbounds(tile): break
                if self.is_tile_own(tile, rook.colour) and collision: break
                moves.append(Move(source, tile))
                if self.is_tile_oponent(tile, rook.colour) or self.is_tile_own(tile, rook.colour) : break
        for x in [-1,1]:
            for r in range(1*x,8*x,x):
                tile = self.add_vectors(source, [r,0])
                if not self.is_tile_inbounds(tile): break
                if self.is_tile_own(tile, rook.colour) and collision: break
                moves.append(Move(source,tile))
                if self.is_tile_oponent(tile, rook.colour) or self.is_tile_own(tile, rook.colour) : break
        return moves

        

    def get_queen_moves(self,queen:Tile, source:list, collision:bool=True)->list:
        return self.get_bishop_moves(queen, source,collision) + self.get_rook_moves(queen, source,collision)

    def get_king_moves(self, king:Tile, source:list, depth:bool=True, collision:bool=True)->list:
        moves = list()
        for x in [-1,0,1]:
            for y in [-1,0,1]:
                if x == 0 and y == 0: continue
                tile = self.add_vectors(source, [x,y])
                if not self.is_tile_inbounds(tile):  continue
                if collision and self.is_tile_own(tile, king.colour): continue
                moves.append(Move(source,tile))
        castling = self.check_for_castling(king.colour)
        if castling[0]: moves.append(Move(source, (source[0], 6)))
        if castling[1]: moves.append(Move(source, (source[0], 1)))
        return moves

    def move(self,src:list,dest:list):
        tsrc = self.at(src)
        tdest = self.at(dest)
        tdest.piece = tsrc.piece
        tdest.colour = tsrc.colour
        tsrc.piece = 0
        tsrc.colour = False
        self.check = False

    def find_king(self,colour:bool):
        return None

    def is_check(self,colour:bool)->bool:
        if self.find_king(colour)['xy'] in self.get_all_moves(colour=not colour, order_by=MovesOrdering.BY_DESTINATION, depth=False, collision=False).keys(): return True
        return False

    def set_check(self,colour:bool):
        self.check = self.is_check(colour)

    def check_for_castling(self, colour:bool)->list:
        return [self.check_for_castling_ks(colour), self.check_for_castling_qs(colour)]

    def check_for_castling_qs(self, colour:bool)->bool:
        fen_castling = self.FEN.split(' ')[2]
        row = 0 if colour else 7
        if colour and 'Q' not in fen_castling or not colour and 'q' not in fen_castling: return False
        possible_moves = self.get_all_moves(not colour, MovesOrdering.BY_DESTINATION, depth=False)
        for col in [1,2,3]:
            if not self.is_tile_empty([row, col]) or (row,col)  in possible_moves.keys():   return False
        return True

    def check_for_castling_ks(self, colour:bool)->bool:
        fen_castling = self.FEN.split(' ')[2]
        row = 0 if colour else 7
        if colour and 'K' not in fen_castling or not colour and 'k' not in fen_castling: return False
        possible_moves = self.get_all_moves(not colour, MovesOrdering.BY_DESTINATION, depth=False)
        for col in [5,6]:
            if not self.is_tile_empty([row, col]) or (row,col)  in possible_moves.keys():   return False
        return True

    def has_ended(self):
        return True if StockfishIntegrationAI(self.FEN).has_ended() else False


    def FENotation(self):
        print('FEN')
        fen = list()
        for row in reversed(self.tiles):
            rowlist = list()
            empty = 0
            for i,tile in enumerate(row):
                x = tile.toFEN()
                if x == '':
                    empty += 1
                else:
                    if empty > 0:
                        rowlist.append(f'{empty}')
                        empty = 0
                    rowlist.append(x)
                if i == len(row) - 1 and empty != 0:
                    rowlist.append(f'{empty}')
            fen.append(''.join(rowlist))
        res = '/'.join(fen)
        if self.turn:
            res = res + ' w '
        else:
            res = res + ' b '
        for colour in [True,False]:
            x = self.check_for_castling(colour)
            if colour and x[0]: res = res + 'K'
            if colour and x[1]: res = res + 'Q'
            if not colour and x[0]: res = res + 'k'
            if not colour and x[1]: res = res + 'q'
        print(res)

    def get_moves_between(self, other:'Game'):
        diffs = dict()
        res = dict()
        for x in range(8):
            for y in range(8):
                if self.at((x,y)) == other.at((x,y)): continue
                #print(self.at((x,y)), other.at((x,y)))
                diffs[(x,y)] = ((self.at((x,y)), other.at((x,y))))
        #print(diffs)
        if len(diffs.keys()) > 2:
            if (0,0) in diffs or (7,0) in diffs: return 'O-O-O'
            else: return 'O-O'
        return Move(tuple(diffs.keys())[0], tuple(diffs.keys())[1]).algebraic()
