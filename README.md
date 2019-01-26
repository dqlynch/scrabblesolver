a python scrabble solver (WIP)
based on the cmu paper: http://www.cs.cmu.edu/afs/cs/academic/class/15451-s06/www/lectures/scrabble.pdf

Outputs a list of the 20 highest-scoring words possible given a words with friends (facebook messenger version) board, and a rack of any number of letters (including blanks). 

to install, clone repo and run `pip install .` or `python3 setup.py develop`. Not yet released on pip.

`USAGE: wwfsolve <board_file> <letters> [<dictionary>]`

` - Available dictionaries: enable (default), sowpods, comb`
Use '?' for blank tiles.

example of a board file can be found in scrabble_solver/example_board
