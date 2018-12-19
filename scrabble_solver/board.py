import numpy as np
import copy

BOARD_LEN = 11
RACK_TILES = 7

all_letters = [l for l in 'abcdefghijklmnopqrstuvwxyz']
WILDCARD = '?'

class Board:
    def __init__(self, board=None, tile_bag=None):
        if board is None:
            self.board = np.full((BOARD_LEN, BOARD_LEN), '')
        else:
            self.board = np.array(board)

        self.letter_multipliers = np.array([
            [3,1,1,1,1,  1,  1,1,1,1,3],
            [1,1,1,1,1,  1,  1,1,1,1,1],
            [1,1,3,1,2,  1,  2,1,3,1,1],
            [1,1,1,3,1,  1,  1,3,1,1,1],
            [1,1,2,1,1,  1,  1,1,2,1,1],

            [1,1,1,1,1,  1,  1,1,1,1,1],

            [1,1,2,1,1,  1,  1,1,2,1,1],
            [1,1,1,3,1,  1,  1,3,1,1,1],
            [1,1,3,1,2,  1,  2,1,3,1,1],
            [1,1,1,1,1,  1,  1,1,1,1,1],
            [3,1,1,1,1,  1,  1,1,1,1,3],
        ])

        self.word_multipliers = np.array([
            [1,1,3,1,1,  1,  1,1,3,1,1],
            [1,2,1,1,1,  2,  1,1,1,2,1],
            [3,1,1,1,1,  1,  1,1,1,1,3],
            [1,1,1,1,1,  1,  1,1,1,1,1],
            [1,1,1,1,1,  1,  1,1,1,1,1],

            [1,2,1,1,1,  1,  1,1,1,2,1],

            [1,1,1,1,1,  1,  1,1,1,1,1],
            [1,1,1,1,1,  1,  1,1,1,1,1],
            [3,1,1,1,1,  1,  1,1,1,1,3],
            [1,2,1,1,1,  2,  1,1,1,2,1],
            [1,1,3,1,1,  1,  1,1,3,1,1],
        ])

        self.row_valid_letters = [[]]*BOARD_LEN

        self.tile_scores = {
            'a': 1, 'b': 4,  'c': 4, 'd': 2, 'e': 1,
            'f': 4, 'g': 3,  'h': 3, 'i': 1, 'j': 10,
            'k': 5, 'l': 2,  'm': 4, 'n': 2, 'o': 1,
            'p': 4, 'q': 10, 'r': 1, 's': 1, 't': 1,
            'u': 2, 'v': 5,  'w': 4, 'x': 8, 'y': 3,
            'z': 10, WILDCARD: 0,
        }

        if tile_bag is None:
            self.tile_bag = {
                'a': 5, 'b': 1, 'c': 1, 'd': 2, 'e': 7,
                'f': 1, 'g': 1, 'h': 1, 'i': 4, 'j': 1,
                'k': 1, 'l': 2, 'm': 1, 'n': 2, 'o': 4,
                'p': 1, 'q': 1, 'r': 2, 's': 4, 't': 2,
                'u': 1, 'v': 1, 'w': 1, 'x': 1, 'y': 1,
                'z': 1, WILDCARD: 2,
            }
        else:
            self.tile_bag = tile_bag
            #print('COPIED TILE BAG')
            #print(f"after copy: {''.join(self.get_remaining_tiles())}")

    def load(self, board_file):
        with open(board_file,'r') as f:
            i = 0
            for line in f.readlines():
                line = line.strip()
                if not line:
                    continue

                for j, letter in enumerate(line.split()):
                    self.board[i,j] = letter.replace('.', '')
                i += 1
        self.set_tile_bag()

    def set_tile_bag(self):
        for row in self.board:
            for letter in row:
                if letter:
                    ch = letter if letter.islower() else WILDCARD
                    self.tile_bag[ch] -= 1
                    if self.tile_bag[ch] < 0:
                        print(f"Too many of '{ch}' on board.")

    def remove_letters(self, letters):
        for letter in letters:
            if letter.isupper():
                letter = WILDCARD
            if self.tile_bag[letter] == 0:
                print(f"Cannot remove '{letter}', no more in tile bag.'")
            else:
                self.tile_bag[letter] -= 1

    def get_remaining_tiles(self):
        remaining_tiles = []
        for letter, num in self.tile_bag.items():
            remaining_tiles.extend([letter]*num)
        return remaining_tiles

    def draw_tiles(self, num_tiles):
        #print(f'DRAWING {num_tiles} TILES')
        remaining_tiles = self.get_remaining_tiles()
        num_tiles = min((len(remaining_tiles), num_tiles))
        if num_tiles == 0:
            return []
        #print(f"bemaining: {''.join(self.get_remaining_tiles())}")
        sel = list(np.random.choice(remaining_tiles, num_tiles,replace=False))
        for letter in sel:
            #print(f'before: {self.tile_bag[letter]}')
            self.tile_bag[letter] -= 1
            #print(f'after: {self.tile_bag[letter]}')
            assert(self.tile_bag[letter] >= 0)
        #print(f"aemaining: {''.join(self.get_remaining_tiles())}")
        return sel

    def transpose(self, recalc=False, dawg=None):
        tboard = Board(board=self.board.T, tile_bag=self.tile_bag)
        if recalc:
            tboard.calc_row_valid_letters(dawg)

        return tboard

    def get_word_below(self, i, j):
        """Return the word below i, j on the board."""
        i += 1
        word = []
        while i < BOARD_LEN and self.board[i,j]:
            word.append(self.board[i,j])
            i += 1
        return ''.join(word)

    def get_word_above(self, i, j):
        """Return the word above i, j on the board."""
        i -= 1
        word = []
        while i > 0 and self.board[i,j]:
            word.insert(0, self.board[i,j])
            i -= 1
        return ''.join(word)


    def get_row_valid_letters(self, lex_dawg, i):
        """
        Return the valid letters for each position on a row, depending on
        the surrounding tiles.
        """
        valid_letters = []
        for j in range(BOARD_LEN):
            valid_letters.append([])

            # Letter on this spot
            if self.board[i,j]:
                valid_letters[j] = [self.board[i,j].lower()]

            # Nothing above or below
            elif (i-1 < 0 or not self.board[i-1,j]) \
               and (i+1 == BOARD_LEN or not self.board[i+1, j]):
                valid_letters[j] = all_letters


            # At top edge or nothing above, consider word below only
            elif i-1 < 0 or not self.board[i-1,j]:
                word = self.get_word_below(i,j).lower()
                for letter in all_letters:
                    if letter + word in lex_dawg:
                        valid_letters[j].append(letter)

            # At bottom edge or nothing below, consider word above only
            elif i+1 == BOARD_LEN or not self.board[i+1, j]:
                word = self.get_word_above(i,j).lower()
                for letter in all_letters:
                    if word + letter in lex_dawg:
                        valid_letters[j].append(letter)

            # Words both above and below
            else:
                above = self.get_word_above(i,j).lower()
                below = self.get_word_below(i,j).lower()
                for letter in all_letters:
                    if above + letter + below in lex_dawg:
                        valid_letters[j].append(letter)

        return [''.join(l) for l in valid_letters]

    def calc_row_valid_letters(self, lex_dawg):
        for i, row in enumerate(self.board):
            self.row_valid_letters[i] = self.get_row_valid_letters(lex_dawg, i)

    def add_word(self, play, rack=None):
        """
        Returns a copy of self with the given word added.
        If rack is given, removes the played letters from rack.
        """
        if play.vertical:
            hplay = copy.copy(play)
            hplay.vertical = False
            return self.transpose().add_word(hplay, rack).transpose()
        played_letters = []

        word = play.word
        i, j = play.i, play.j
        new_board = Board(board=self.board, tile_bag=self.tile_bag)

        while word:
            if not new_board.board[i, j+len(word)-1]:
                played_letters.append(word[-1])

            new_board.board[i, j + len(word)-1] = word[-1]
            word = word[:-1]

        if rack:
            rack.remove_letters(played_letters)

        return new_board

    def _score_existing_word(self, word):
        return sum([self.tile_scores[letter] for letter in word if letter.islower()])


    def score_word(self, word, startpos):
        orig_word = word
        ai, aj = startpos

        score = 0
        myword_score = 0
        myword_multiplier = 1
        tiles_placed = 0

        # "add" word to board, count score
        while word:
            i, j = ai, aj + len(word)-1         # position adding letter to
            letter = word[-1]

            # Get position multipliers
            letter_mult, word_mult = 1, 1
            if not self.board[i,j]:     # only count board multipliers for new
                tiles_placed += 1
                letter_mult = self.letter_multipliers[i,j]
                word_mult = self.word_multipliers[i,j]
            myword_multiplier *= word_mult

            # Score of this individual letter
            letterscore = 0
            if letter.islower():        # only score non-blank tiles
                letterscore = self.tile_scores[letter]*letter_mult

            myword_score += letterscore

            # Get score for adjacent completed words
            if not self.board[i,j]:
                below = self.get_word_below(i, j)
                above = self.get_word_above(i, j)
                if above or below:
                    collat = self._score_existing_word(below) + \
                             self._score_existing_word(above) + \
                             letterscore
                    collat *= word_mult

                    score += collat

            word = word[:-1]

        score += myword_score * myword_multiplier
        if tiles_placed == 7:
            score += 35

        return score

    def __str__(self):
        """String representation. Fills all empty spots for better formatting."""
        board = np.array(
            [[c if c else '.' for c in row] for row in self.board]
        )
        return str(board)


class Rack:
    def __init__(self, letters=''):
        self.letters = [c for c in letters]

    def __str__(self):
        return ''.join(self.letters)

    def remove_letters(self, letters):
        for letter in letters:
            if letter.isupper():
                letter = WILDCARD
            self.letters.remove(letter)

    def draw_from_board(self, board, max_tiles=RACK_TILES):
        self.letters.extend(board.draw_tiles(max_tiles - len(self.letters)))

class Play :
    def __init__(self, word='', i=0, j=0, score=0, vertical=None):
        self.word = word
        self.i = i
        self.j = j
        self.score = score
        self.vertical = vertical

    def __repr__(self):
        return f'"{self.word}": ({self.i},{self.j}), {self.score}pts'

    def __str__(self):
        return f'"{self.word}": ({self.i},{self.j}), {self.score}pts'
