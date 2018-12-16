import numpy as np

BOARD_LEN = 11

all_letters = [l for l in 'abcdefghijklmnopqrstuvwxyz']

class Board:
    def __init__(self, board=None):
        if board is None:
            self.board = np.full((11, 11), '')
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

        self.tile_scores = {
            'a': 1, 'b': 4,  'c': 4, 'd': 2, 'e': 1,
            'f': 4, 'g': 3,  'h': 3, 'i': 1, 'j': 10,
            'k': 5, 'l': 2,  'm': 4, 'n': 2, 'o': 1,
            'p': 4, 'q': 10, 'r': 1, 's': 1, 't': 1,
            'u': 2, 'v': 5,  'w': 4, 'x': 8, 'y': 3,
            'z': 10
        }

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


    def transpose(self):
        return Board(self.board.T)

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

        return valid_letters

    def add_word(self, word, anchor, offset):
        """Returns a copy of self with the given word added."""
        new_board = Board(self.board)
        i, j = anchor
        j -= offset
        while word:
            new_board.board[i, j + len(word)-1] = word[-1]
            word = word[:-1]
        return new_board

    def add_v_word(self, word, anchor, offset):
        """Same as add_word but for vertical (transposed) words."""
        return self.transpose().add_word(word, anchor, offset)


    def _score_existing_word(self, word):
        return sum([self.tile_scores[letter] for letter in word if letter.islower()])


    def score_word(self, word, anchor, offset):
        orig_word = word
        ai, aj = anchor
        aj -= offset

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
