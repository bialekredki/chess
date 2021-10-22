import unittest
from chess.models import Game
from chess.game import PieceType, Game as ChessGame
from chess import db

class TestChessSetup(unittest.TestCase):
    def test_setup(self):
        game = Game(1,2)
        db.session.add(game)
        db.session.commit()
        proper = [ChessGame.backRowSetup,
            [1 for x in  range(8)],
            [0 for x in  range(8)],
            [0 for x in  range(8)],
            [0 for x in  range(8)],
            [0 for x in  range(8)],
            [1 for x in  range(8)],
            ChessGame.backRowSetup]
        for x in range(8):
            for y in range(8):
                self.assertEqual(proper[x][y], game.at((x,y)).piece)

if __name__ == '__main__':
    unittest.main()