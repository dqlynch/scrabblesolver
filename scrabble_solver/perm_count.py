import os
import sys
from pprint import pprint

from .solver import (
    load_lex_dawg,
    get_words,
    DICTS_PATH,
    DAWGS_PATH,
)

def get_words_of_len(n, dictionary_files):
    words = []
    for dictionary_file in dictionary_files:
        with open(dictionary_file) as f:
            for line in f.readlines():
                word = line.strip()
                if len(word) == n:
                    words.append(word)
    return list(set(words))


def _get_highest_nperms(n, words, dawg):
    """
    Get the permutations for the set of letters of length n with the
    highest number of valid word permutations.
    """
    best = (None, 0, [])    # word, num perms, nperms

    words_counted = 0
    total_perms_counted = 0

    for word in words:
        words_counted += 1
        # Generate all n-length permutations of word
        nperms = [w for w in dawg.gen_completions('', word)]
        total_perms_counted += len(nperms)

        nperms = [w for w in nperms if len(w) == n]

        for nperm in nperms:
            try:
                words.remove(nperm)
            except ValueError:
                pass

        nperms = list(set(nperms))

        if len(nperms) > best[1]:
            best = (word, len(nperms), nperms)

    print(f'words permuted: {words_counted}')
    print(f'total permutations: {total_perms_counted}')
    return best

def sort_word_by_len_lex(word):
    # TODO make lex sort secondary
    return len(word)


def _get_hardest_wordcube(n, words, dawg):
    """
    Get the permutations for the set of letters of length n with the
    highest number of valid word permutations.
    """
    best = (None, None, 0, [])    # word, num perms, nperms

    words_counted = 0
    total_perms_counted = 0

    for word in words:
        words_counted += 1
        # Generate all n-length permutations of word
        perms = [w for w in dawg.gen_completions('', word)]
        total_perms_counted += len(perms)
        perms = set(perms)

        # generate perm sets with required letter
        letters = set(word)
        for letter in letters:
            req_perms = [perm for perm in perms if len(perm) > 3 and letter in perm]
            if len(req_perms) > best[2]:
                best = (word, letter, len(req_perms), req_perms)

        # remove nperms for this word
        nperms = [w for w in perms if len(w) == n]
        for nperm in nperms:
            try:
                words.remove(nperm)
            except ValueError:
                pass

        #nperms = list(set(nperms))

        #if len(nperms) > best[1]:
        #    best = (word, len(nperms), nperms)

    print(f'words permuted: {words_counted}')
    print(f'total perms counted: {total_perms_counted}')

    # sort words
    best[-1].sort(key=sort_word_by_len_lex, reverse=True)

    return best


def get_highest_nperms(n, dictionary_files, dawg_file):
    dawg = load_lex_dawg(dictionary_files, dawg_file)
    words = get_words_of_len(n, dictionary_files)


def get_hardest_wordcube(n, dictionary_files, dawg_file):
    dawg = load_lex_dawg(dictionary_files, dawg_file)
    words = get_words_of_len(n, dictionary_files)
    words.sort()
    print(f'Generating wordcube for length {n}: checking {len(words)} words.')

    return _get_hardest_wordcube(n, words, dawg)


def main():
    if len(sys.argv) < 2:
        print('USAGE: perm_count word_length [dictionary]')
        exit()

    n = int(sys.argv[1].strip())

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


    #print(get_highest_nperms(n, dictionary_files, dawg_file))
    print(get_hardest_wordcube(n, dictionary_files, dawg_file))


if __name__ == '__main__':
    main()
