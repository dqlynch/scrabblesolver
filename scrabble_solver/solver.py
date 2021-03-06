import copy
import numpy as np
import cProfile
import os
import sys
from pprint import pprint
import time

import itertools
from multiprocessing import Pool

from dawg import CompletionDAWG
from .scrabble_dawg import ScrabbleDAWG

from .board import *

NUM_BEST_WORDS = 10
ENDGAME_WORDS = 7
MAX_DEPTH = 3

import os
dirname = os.path.dirname(__file__)
DICTS_PATH = os.path.join(dirname, 'dictionaries')
DAWGS_PATH = os.path.join(dirname, 'dawgs')


def play_sorter(play):
    """Sorts plays by score"""
    return play.score

def get_words(dictionary_files):
    words = []
    for dictionary_file in dictionary_files:
        with open(dictionary_file, 'r') as f:
            for line in f.readlines():
                word = line.strip()
                words.append(word)
    return list(set(words))



def save_lex_dawg(dictionary_files=('dictionaries/sowpods.txt',),
                  outfile=DAWGS_PATH + 'sowpods.dawg'):

    completion_dawg = CompletionDAWG(get_words(dictionary_files))
    completion_dawg.save(outfile)


def load_lex_dawg(dictionary_files=('dictionaries/sowpods.txt',), dawg_file=DAWGS_PATH + 'tmp.dawg'):
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
    for prefix, remaining_left in lex_dawg.gen_valid_prefixes(
            rack.letters,
            board.board[i,:j],
            row_valid_letters[:j]):

        # Calculate right extensions for all left prefixes
        #print(f'\nextending {prefix} with letters: {remaining_left}')
        for word, remaining in lex_dawg.gen_right_extensions(
                prefix,
                remaining_left,
                board.board[i,j:],
                row_valid_letters[j:]):

            score = board.score_word(word, (i, j-len(prefix)))
            play = Play(word=word, i=i, j=j-len(prefix), score=score, remaining=remaining)

            if len(best_words) == NUM_BEST_WORDS:
                best_words.sort(key=play_sorter)
                if score > best_words[0].score:
                    best_words.pop(0)
                    best_words.append(play)
            else:
                best_words.append(play)


    return best_words


def remove_duplicates(ls):
    out = []
    for l in ls:
        if l not in out:
            out.append(l)
    return out



def solve_board(board, rack, lex_dawg, print_words=False):
    pool = Pool()

    board.calc_row_valid_letters(lex_dawg)

    # Horizontal plays
    hargs = []
    for anchor in get_anchors(board):
        hargs.append(
            (board, rack, lex_dawg, anchor, [])
        )

    best_hwords = [Play()]
    best_hanchor_plays = pool.starmap(generate_moves, hargs, chunksize=1)

    # Vertical plays
    tboard = board.transpose(recalc=True, dawg=lex_dawg)
    vargs = []
    for anchor in get_anchors(tboard):
        vargs.append(
            (tboard, rack, lex_dawg, anchor, [])
        )
    best_vwords = [Play()]
    best_vanchor_plays = pool.starmap(generate_moves, vargs, chunksize=1)


    # Flatten plays
    for best_plays in best_hanchor_plays:
        best_hwords.extend(best_plays)
    for best_plays in best_vanchor_plays:
        best_vwords.extend(best_plays)


    # Concat plays
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

    best_words = remove_duplicates(best_words)
    return best_words

def _get_ending_plays(plays):
    endings = [play for play in plays if play.remaining == '']

    # remove endings from plays
    for end in endings:
        plays.remove(end)
    return endings


def _end_sorter(seq):
    return seq[0][-1]


def _eval_endgame(lex_dawg, board, rack, opp_rack, depth):
    #print(f'***evaluating endgame depth {depth}')
    # No letters, no score possible
    if not opp_rack.letters:
        assert False, 'opp rack should return if empty, not get here'
        #return [(Play(), -1*board._score_existing_word(rack.letters))]
    if depth == MAX_DEPTH:
        return [(Play(), 0)]

    # Return the score differential of best play - their best play diff
    board = copy.copy(board)
    rack = copy.copy(rack)

    plays = solve_board(board, rack, lex_dawg, print_words=False)

    best_seqs = []

    # Consider highest scoring ending play
    ending_plays = _get_ending_plays(plays)
    if ending_plays:
        ending_plays.sort(key=play_sorter, reverse=True)
        ending = ending_plays[0]
        end_bonus = 2*board._score_existing_word(opp_rack.letters)
        ending_seq = [
            (ending, ending.score + end_bonus),
            (Play(), -end_bonus)
        ]
        best_seqs.append(ending_seq)

    plays.sort(key=play_sorter, reverse=True)
    plays = plays[:ENDGAME_WORDS]

    for i, play in enumerate(plays):
        if depth < 1:
            print(f'Evaluating depth {depth}: play {i+1} of {len(plays)}')
        # Subtract differential of opponents best play
        scorediff = play.score

        next_rack = Rack(rack.letters)
        next_board = board.add_word(play, next_rack)

        opp_best_seq = _eval_endgame(lex_dawg, next_board,
                                      opp_rack, next_rack, depth+1)

        scorediff -= opp_best_seq[0][-1]
        best_seqs.append([(play, scorediff)] + opp_best_seq)

    # TODO make this shit not hideous
    best_seqs.sort(key=_end_sorter, reverse=True)
    if depth == 0:
        return best_seqs
    return best_seqs[0]



def eval_endgame(board, rack, lex_dawg, print_words=False):
    """
    Perform a 2-ply adversarial search for the highest score
    score differential over the X highest scoring words.
    """
    print('All tiles known, evaluating endgame...')

    opp_rack = Rack()
    opp_rack.draw_from_board(board)
    print(f'Oppenent rack: {opp_rack}')
    assert(not board.get_remaining_tiles())

    best_plays = _eval_endgame(lex_dawg, board, rack, opp_rack, 0)
    for plays in best_plays:
        print()
        print(plays)



def play_urself(lex_dawg):
    highest_word = Play(0, 0, 0, 0)
    while True:
        board = Board()
        rack0 = Rack()
        rack1 = Rack()
        rack0.draw_from_board(board)

        rack1.draw_from_board(board)

        scores = [0, 0]

        played_last_turn = True
        turn = 0
        while rack0.letters and rack1.letters:

            rack = rack1 if turn else rack0
            print(f'\n\nPLAYER {turn+1}: {"".join(rack.letters)}')

            # just pick highest word as test
            play = solve_board(board, rack, lex_dawg)[-1]
            scores[turn] += play.score

            if not played_last_turn and not play.word:
                break

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
        return
        time.sleep(1)


def solve_board_cli():
    if len(sys.argv) < 3:
        print('USAGE: wwfsolve <board_file> <letters> [<dictionary>]')
        print(' - Available dictionaries: enable (default), sowpods, comb')
        exit(0)

    board_file = sys.argv[1].strip()
    rack_ls = sys.argv[2].strip()
    dictionary_files = (os.path.join(DICTS_PATH, 'enable2k.txt'),
                        os.path.join(DICTS_PATH, 'wwf_additions.txt'))
    dawg_file = os.path.join(DAWGS_PATH, 'wwf.dawg')
    try:
        dictionary = sys.argv[3]
        if dictionary == 'sowpods':
            dictionary_files = (os.path.join(DICTS_PATH, 'sowpods.txt'),)
            dawg_file = os.path.join(DAWGS_PATH, 'sowpods.dawg')
        if dictionary == 'comb':
            dictionary_files += (os.path.join(DICTS_PATH, 'sowpods.txt'),)
            dawg_file = os.path.join(DAWGS_PATH, 'combined.dawg')
    except:
        pass

    lex_dawg = load_lex_dawg(dictionary_files, dawg_file)

    board = Board()
    board.load(board_file)

    rack = Rack(rack_ls)

    board.remove_letters(rack.letters)
    print(board)
    print(f'Solving board with letters: {rack}...')


    # TODO XXX fix/redo this
    if len(board.get_remaining_tiles()) <= RACK_TILES:
        eval_endgame(board, rack, lex_dawg, print_words=False)
        return

    best_words = solve_board(board, rack, lex_dawg, print_words=True)


def main():
    dictionary_files = (os.path.join(DICTS_PATH, 'enable2k.txt'),
                        os.path.join(DICTS_PATH, 'wwf_additions.txt'))
    dawg_file = os.path.join(DAWGS_PATH + 'wwf.dawg')

    # sowpods
    #dictionary_files = (os.path.join(DICTS_PATH, 'sowpods.txt'),)
    #dawg_file = os.path.join(DAWGS_PATH, 'sowpods.dawg')

    # combined
    #dictionary_files += (os.path.join(DICTS_PATH, 'sowpods.txt'),)
    #dawg_file = os.path.join(DAWGS_PATH, 'combined.dawg')

    lex_dawg = load_lex_dawg(dictionary_files, dawg_file)

    play_urself(lex_dawg)

    # XXX Testing only
    #best_hwords = []
    #i,j = 2, 7
    #generate_moves(board, rack, lex_dawg, (i, j), best_hwords)
    #print(best_hwords)
