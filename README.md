# scrabblesolver
a python scrabble solver (WIP) using a modified directed acyclic word graph (DAWG) for efficient prefix generation and completion, based on the CMU paper: http://www.cs.cmu.edu/afs/cs/academic/class/15451-s06/www/lectures/scrabble.pdf

Outputs a list of the 20 highest-scoring words possible given a words with friends (facebook messenger version) board, and a rack of any number of letters (including blanks). 

to install, clone repo and run `pip install -e .` or `python3 setup.py develop`. Not yet released on pip.

`USAGE: wwfsolve <board_file> <letters> [<dictionary>]`

` - Available dictionaries: enable (default), sowpods, comb`

Use '?' for blank tiles.

example of board files can be found in `scrabble_solver/example_board` and `scrabble_solver/test_board.txt`

## Example usage:

![alt text](https://github.com/dqlynch/scrabblesolver/blob/master/example_images/one_blank_example.png)
