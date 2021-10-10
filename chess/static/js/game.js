class Tile {
    constructor(piece, colour) {
        this.piece = piece;
        this.colour = colour;
    }

    isWhite() {
        return this.colour;
    }

    isBlack() {
        return !this.colour;
    }

    isEmpty() {
        if (this.piece == 0) return true;
        return false;
    }

    getPiece() {
        return this.piece;
    }

    getPieceString() {
        switch (this.piece) {
            case 1:
                return 'pawn';
            case 2:
                return 'knight';
            case 3:
                return 'bishop';
            case 4:
                return 'rook';
            case 5:
                return 'queen';
            case 6:
                return 'king';
            default:
                return 'empty';
        }
    }

    getPieceSymbol() {
        const str = this.getPieceString()
        if (str != 'knight') return str[0];
        return 'n';
    }

    empty() {
        this.piece = 0;
    }

    setPiece(piece) {
        this.piece = piece;
    }
}

class Game {
    backRowSetup = [4, 2, 3, 5, 6, 3, 2, 4];
    constructor() {
        this.tiles = new Array(8);
        for (let tile = 0; tile < 8; tile++) {
            this.tiles[tile] = new Array(8);
            for (let column = 0; column < 8; column++) {
                this.tiles[tile][column] = new Tile(0, false);
            }
        }
    }

    setRowColour(row, colour) {
        rowObj = this.tiles[row];
        for (let col = 0; col < 8; col++) {
            rowObj[col].colour = colour;
        }
    }

    setBackrowDefault(colour) {
        let backrow = 0;
        if (colour) backrow = this.tiles[0];
        else backrow = this.tiles[7];
        for (let col = 0; col < 8; col++) {
            backrow[col].colour = colour;
            backrow[col].piece = this.backRowSetup[col];
        }
    }
    setFrontrowPawns(colour) {
        let frontrow = 0;
        if (colour) frontrow = this.tiles[1];
        else frontrow = this.tiles[6];
        for (let col = 0; col < 8; col++) {
            frontrow[col].colour = colour;
            frontrow[col].piece = 1;
        }
    }
    isEmpty(x, y) {
        return this.tiles[x][y].isEmpty();
    }

    isWhite(x, y) {
        if (this.isEmpty(x, y)) return null;
        return this.tiles[x][y].isWhite();
    }

    isBlack(x, y) {
        if (this.isEmpty(x, y)) return null;
        return this.tiles[x][y].isBlack();
    }

    getPiece(x, y, type) {
        if (type == 'symbol')
            return this.tiles[x][y].getPieceSymbol();
        if (type == 'string')
            return this.tiles[x][y].getPieceString();
        if (type == 'numeric')
            return this.tiles[x][y].getPiece();
    }

    newGameSetup() {
        this.setBackrowDefault(true);
        this.setBackrowDefault(false);
        this.setFrontrowPawns(false);
        this.setFrontrowPawns(true);
        for (let rows = 0; rows < 8; rows++) {
            if (rows > 1 || rows < 6) continue;
            if (rows < 2) this.setRowColour(rows, true);
            if (rows > 5) this.setRowColour(rows, false);
        }
    }
}