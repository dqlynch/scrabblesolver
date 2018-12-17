import numpy as np
import os
import sys
from pprint import pprint
import time

from dawg import CompletionDAWG
from scrabble_dawg import ScrabbleDAWG

from board import *

NUM_BEST_WORDS = 10


def score_sorter(elt):
    """Scores word with (word, (starti, startj), score)"""
    return elt[-1]


def save_lex_dawg(dictionary_files=('dictionaries/sowpods.txt',),
                  outfile='dawgs/sowpods.dawg'):
    words = []
    for dictionary_file in dictionary_files:
        with open(dictionary_file, 'r') as f:
            for line in f.readlines():
                word = line.strip()
                words.append(word)

    completion_dawg = CompletionDAWG(words)
    completion_dawg.save(outfile)


def load_lex_dawg(dictionary_files=('dictionaries/sowpods.txt',), dawg_file='dawgs/tmp.dawg'):
    if not os.path.isfile(dawg_file):
        # Create dawg file
        save_lex_dawg(dictionary_files, dawg_file)

    return ScrabbleDAWG().load(dawg_file)


def gen_adjacent_spots(i, j):
    dirs = [-1, 1]
    for d in dirs:
        if i+d >= 0 and i+d < BOARD_LEN:
            yield i+d, j
        if j+d >= 0 and j+d < BOARD_LEN:
            yield i, j+d


def get_anchors(board):
    anchors = []
    for i, row in enumerate(board.board):
        for j, letter in enumerate(row):
            if not board.board[i,j]:
                for adj_i, adj_j in gen_adjacent_spots(i, j):
                    if board.board[adj_i, adj_j]:
                        anchors.append((i,j))
                        break
    return anchors


def generate_moves(board, rack, lex_dawg, anchor, best_words):
    """Generate all possible moves from a given anchor point"""
    # Calculate valid placements for row
    i, j = anchor
    row_valid_letters = board.get_row_valid_letters(lex_dawg, i)

    # Calculate all valid left prefixes
    prefixes = [prefix for prefix, _ in lex_dawg.gen_valid_prefixes(
        rack.letters,
        board.board[i,:j],
        row_valid_letters[:j])]

    for prefix, remaining_left in lex_dawg.gen_valid_prefixes(
            rack.letters,
            board.board[i,:j],
            row_valid_letters[:j]):
        #print(f'prefix: "{prefix}"')

        # Calculate right extensions for all left prefixes
        #print(f'\nextending {prefix} with letters: {remaining_left}')
        for word, remaining in lex_dawg.gen_right_extensions(
                prefix,
                remaining_left,
                board.board[i,j:],
                row_valid_letters[j:]):

            score = board.score_word(word, (i, j-len(prefix)))
            wordpack = (word, (i, j-len(prefix)), score)

            if len(best_words) == NUM_BEST_WORDS:
                best_words.sort(key=score_sorter)
                if score > best_words[0][-1]:
                    best_words.pop(0)
                    best_words.append(wordpack)
            else:
                best_words.append(wordpack)

    return best_words


def solve_board(board, rack, lex_dawg):
    best_hwords = []
    for i, j in get_anchors(board):
        generate_moves(board, rack, lex_dawg, (i, j), best_hwords)

    best_vwords = []
    for i, j in get_anchors(board.transpose()):
        generate_moves(board.transpose(), rack, lex_dawg, (i, j), best_vwords)

    best_words = [(False,) + word for word in best_hwords]
    best_words.extend([(True,) + word for word in best_vwords])
    best_words.sort(key=score_sorter)

    #best_words = best_words[-NUM_BEST_WORDS:]

    for transposed, word, startpos, score in best_words:
        new_board = None
        if transposed:
            new_board = board.add_v_word(word, startpos)
        else:
            new_board = board.add_word(word, startpos)

        print(f'\n-----{word}: {score}-----')
        print(new_board)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('USAGE: python3 solver.py <board_file> <letters>')
    board_file = sys.argv[1].strip()
    rack_ls = sys.argv[2].strip()

    board = Board()
    board.load(board_file)
    print(board)

    rack = Rack(rack_ls)

    #lex_dawg = load_lex_dawg()
    lex_dawg = load_lex_dawg(
        ('dictionaries/enable2k.txt', 'dictionaries/wwf_additions.txt'),
        'dawgs/wwf.dawg')
    #lex_dawg = load_lex_dawg(
    #    ('dictionaries/enable2k.txt',
    #     'dictionaries/wwf_additions.txt',
    #     'dictionaries/sowpods.txt'),
    #    'dawgs/combined.dawg')
    solve_board(board, rack, lex_dawg)

    # XXX Testing only
    #best_hwords = []
    #i,j = 2, 7
    #generate_moves(board, rack, lex_dawg, (i, j), best_hwords)
    #print(best_hwords)
