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
            [1,2,1,1,1,  2,  1,2,1,1,1],
            [3,1,1,1,1,  1,  3,1,1,1,1],
            [1,1,1,1,1,  1,  1,1,1,1,1],
            [1,1,1,1,1,  1,  1,1,1,1,1],

            [1,2,1,1,1,  1,  1,1,1,2,1],

            [1,1,1,1,1,  1,  1,1,1,1,1],
            [1,1,1,1,1,  1,  1,1,1,1,1],
            [3,1,1,1,1,  1,  3,1,1,1,1],
            [1,2,1,1,1,  2,  1,2,1,1,1],
            [1,1,3,1,1,  1,  1,1,3,1,1],
        ])

        tile_scores = []


    def transpose(self):
        return Board(self.board.T)

    def get_word_below(self, i, j):
        """Return the word below i, j on the board."""
        i += 1
        word = []
        while self.board[i,j]:
            word.append(self.board[i,j])
            i += 1
        return ''.join(word)

    def get_word_above(self, i, j):
        """Return the word above i, j on the board."""
        i -= 1
        word = []
        while self.board[i,j]:
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
                valid_letters[j] = [self.board[i,j]]

            # Nothing above or below
            elif (i-1 < 0 or not self.board[i-1,j]) \
               and (i+1 == BOARD_LEN or not self.board[i+1, j]):
                valid_letters[j] = all_letters


            # At top edge or nothing above, consider word below only
            elif i-1 < 0 or not self.board[i-1,j]:
                word = self.get_word_below(i,j)
                for letter in all_letters:
                    if letter + word in lex_dawg:
                        valid_letters[j].append(letter)

            # At bottom edge or nothing below, consider word above only
            elif i+1 == BOARD_LEN or not self.board[i+1, j]:
                word = self.get_word_above(i,j)
                for letter in all_letters:
                    if word + letter in lex_dawg:
                        valid_letters[j].append(letter)

            # Words both above and below
            else:
                above = self.get_word_above(i,j)
                below = self.get_word_below(i,j)
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

    def score_word(self, word, anchor, offset):
        score = 0

        return score

    def __str__(self):
        """String representation. Fills all empty spots for better formatting."""
        board = np.array(
            [[c.upper() if c else '.' for c in row] for row in self.board]
        )
        return str(board)



class Rack:
    def __init__(self, letters=''):
        self.letters = [c for c in letters]

    def __str__(self):
        return ''.join(self.letters)
