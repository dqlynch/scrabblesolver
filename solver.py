import numpy as np
import os
from pprint import pprint
import time

from dawg import CompletionDAWG
from scrabble_dawg import ScrabbleDAWG

from board import *

NUM_BEST_WORDS = 10


def score_sorter(elt):
    return elt[-1]


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


def generate_moves(board, rack, lex_dawg, anchor, best_words):
    """Generate all possible moves from a given anchor point"""
    # Calculate valid placements for row
    i, j = anchor
    row_valid_letters = board.get_row_valid_letters(lex_dawg, i)

    # Calculate all valid left prefixes
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

            score = board.score_word(word, anchor, len(prefix))

            if len(best_words) == NUM_BEST_WORDS:
                print(score)
                best_words.sort(key=score_sorter)
                if score > best_words[0][-1]:
                    best_words.pop(0)
                    board.score_word(word, anchor, len(prefix))
                    best_words.append((word, anchor, prefix, score))
            else:
                best_words.append((word, anchor, prefix, score))

    return best_words


def solve_board(board, rack, dictionary_file):
    lex_dawg = load_lex_dawg(dictionary_file)

    # TODO replace with all anchors
    #generate_moves(board, rack, lex_dawg, (4, 8))   # above O

    best_hwords = []
    for i, j in get_anchors(board):
        generate_moves(board, rack, lex_dawg, (i, j), best_hwords)

    best_vwords = []
    for i, j in get_anchors(board.transpose()):
        generate_moves(board.transpose(), rack, lex_dawg, (i, j), best_vwords)

    best_words = [(False,) + word for word in best_hwords]
    best_words.extend([(True,) + word for word in best_vwords])
    best_words.sort(key=score_sorter)

    best_words = best_words[-NUM_BEST_WORDS:]

    for transposed, word, anchor, prefix, score in best_words:
        new_board = None
        if transposed:
            new_board = board.add_v_word(word, anchor, len(prefix))
        else:
            new_board = board.add_word(word, anchor, len(prefix))

        print(f'\n-----{word}: {score}-----')
        print(new_board)

    #for word, anchor, prefix, score in best_vwords:
    #    new_board = board.transpose().add_word(word, anchor, len(prefix))
    #    print(f'\n-----{word}: {score}-----')
    #    print(new_board.transpose())


if __name__ == '__main__':
    # Simple testing board
    board = Board()
    board.board[5,3] = 'c'
    board.board[5,4] = 'a'
    board.board[5,5] = 't'

    board.board[6,3] = 'a'
    board.board[7,3] = 'r'

    print(board)

    rack = Rack('asc?tog')

    solve_board(board, rack, 'dictionaries/sowpods.txt')

    # XXX testing
    #lex_dawg = load_lex_dawg('dictionaries/basic.txt')
    #for letter in lex_dawg.gen_possible_placements('ca', rack.letters, all_letters):
    #    print(letter)


