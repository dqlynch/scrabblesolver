import numpy as np
import os
from pprint import pprint

from dawg import CompletionDAWG
from scrabble_dawg import ScrabbleDAWG

from board import *


def save_lex_dawg(dictionary_file='dictionaries/sowpods.txt',
                  outfile='dawgs/sowpods.dawg'):
    with open(dictionary_file, 'r') as f:
        words = []
        for line in f.readlines():
            word = line.strip()
            words.append(word)

    completion_dawg = CompletionDAWG(words)
    completion_dawg.save(outfile)


def load_lex_dawg(dictionary_file='dictionaries/sowpods.txt'):
    dawg_file = dictionary_file.replace('.txt', '.dawg').replace('dictionaries/', 'dawgs/')
    if not os.path.isfile(dawg_file):
        # Create dawg file
        save_lex_dawg(dictionary_file, dawg_file)

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


def generate_moves(board, rack, lex_dawg, anchor):
    """Generate all possible moves from a given anchor point"""
    # Calculate valid placements for row
    i, j = anchor
    row_valid_letters = board.get_row_valid_letters(lex_dawg, i)

    # Calculate all valid left prefixes
    for prefix, remaining in lex_dawg.gen_valid_prefixes(
            rack.letters,
            board.board[i,:j],
            row_valid_letters[:j]
        ):
        # Calculate right extensions for all left prefixes
        print(f'extending {prefix} with letters: {remaining}')



def solve_board(board, rack):
    lex_dawg = load_lex_dawg('dictionaries/basic.txt')

    # TODO replace with all anchors
    a_i, a_j = 5, 8
    generate_moves(board, rack, lex_dawg, (a_i, a_j))


if __name__ == '__main__':
    # Simple testing board
    board = Board()
    board.board[5,5] = 'c'
    board.board[5,6] = 'a'
    board.board[5,7] = 'r'

    board.board[2,8] = 'c'
    board.board[3,8] = 'a'
    board.board[4,8] = 't'

    board.board[7,0] = 'c'
    board.board[9,0] = 't'
    print(board)

    rack = Rack('atcse?r')

    solve_board(board, rack)

    # XXX testing
    #lex_dawg = load_lex_dawg('dictionaries/basic.txt')
    #for letter in lex_dawg.gen_possible_placements('ca', rack.letters, all_letters):
    #    print(letter)


