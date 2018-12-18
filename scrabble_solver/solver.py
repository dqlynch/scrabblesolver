import numpy as np
import os
import sys
from pprint import pprint
import time

from dawg import CompletionDAWG
from scrabble_dawg import ScrabbleDAWG

from board import *

NUM_BEST_WORDS = 10


def play_sorter(play):
    """Sorts plays by score"""
    return play.score


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

    # Add center tile as anchor if board empty
    if not anchors:
        anchors.append((BOARD_LEN//2, BOARD_LEN//2))
    return anchors


def generate_moves(board, rack, lex_dawg, anchor, best_words):
    """Generate all possible moves from a given anchor point"""
    # Calculate valid placements for row
    i, j = anchor
    row_valid_letters = board.row_valid_letters[i]

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
            play = Play(word=word, i=i, j=j-len(prefix), score=score)

            if len(best_words) == NUM_BEST_WORDS:
                best_words.sort(key=play_sorter)
                if score > best_words[0].score:
                    best_words.pop(0)
                    best_words.append(play)
            else:
                best_words.append(play)


    return best_words


def solve_board(board, rack, lex_dawg, print_words=False):
    board.calc_row_valid_letters(lex_dawg)

    best_hwords = [Play('', 0, 0, 0)]   # in case no plays available
    for i, j in get_anchors(board):
        generate_moves(board, rack, lex_dawg, (i, j), best_hwords)

    best_vwords = [Play('', 0, 0, 0)]   # in case no plays available
    tboard = board.transpose(recalc=True, dawg=lex_dawg)
    for i, j in get_anchors(tboard):
        generate_moves(tboard, rack, lex_dawg, (i, j), best_vwords)

    for play in best_hwords:
        play.vertical = False
    for play in best_vwords:
        play.vertical = True

    best_words = best_hwords + best_vwords
    best_words.sort(key=play_sorter)

    #best_words = best_words[-NUM_BEST_WORDS:]

    if print_words:
        for play in best_words:
            new_board = board.add_word(play)

            print(f'\n-----{play.word}: {play.score}-----')
            print(new_board)

    return best_words


def play_urself(lex_dawg):
    highest_word = Play(0, 0, 0, 0)
    while True:
        board = Board()
        rack0 = Rack()
        rack1 = Rack()
        rack0.draw_from_board(board)

        rack1.draw_from_board(board)

        scores = [0, 0]

        turn = 0
        while rack0.letters and rack1.letters:

            rack = rack1 if turn else rack0
            print(f'\n\nPLAYER {turn+1}: {"".join(rack.letters)}')

            # just pick highest word as test
            play = solve_board(board, rack, lex_dawg)[-1]
            scores[turn] += play.score

            if play.score > highest_word.score:
                highest_word = play

            # place and print word
            board = board.add_word(play, rack=rack)
            board.calc_row_valid_letters(lex_dawg)  # recalculate checksums

            print(f'-----{play.word}: {play.score}-----')
            print(board)
            print(f"remaining: {''.join(board.get_remaining_tiles())}")

            # draw new tiles
            rack.draw_from_board(board)
            turn = (turn + 1) % 2

        scores[0] += board._score_existing_word(rack1.letters)
        scores[1] += board._score_existing_word(rack0.letters)

        print(f'PLAYER 1: {scores[0]}, PLAYER 2: {scores[1]}')
        print(f'PLAYER {np.argmax(scores)+1} WINS!!!')
        print(f'Highest word: {highest_word}')
        time.sleep(1)



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
    #solve_board(board, rack, lex_dawg, print_words=True)
    play_urself(lex_dawg)

    # XXX Testing only
    #best_hwords = []
    #i,j = 2, 7
    #generate_moves(board, rack, lex_dawg, (i, j), best_hwords)
    #print(best_hwords)
