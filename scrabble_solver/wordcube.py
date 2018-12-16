import sys
from pprint import pprint

from solver import load_lex_dawg

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('USAGE: python3 wordcube.py <letters>')
        print('first letter is required letter')

    letters = sys.argv[1].strip().lower()
    req = letters[0]

    dawg = load_lex_dawg(('dictionaries/enable2k.txt',),
                         'dawgs/enable1.dawg')

    print(f'letters: {letters}, required={req}')

    words = []
    for word in dawg.gen_completions('', letters):
        if len(word) > 3 and req in word:
            words.append(word)
    words.sort(key=len)
    pprint(words)
