import dawg
import dawg_python
from dawg_python.compat import int_from_byte

WILDCARD = '?'

class ScrabbleDAWG(dawg_python.CompletionDAWG):
    """
    A CompletionDAWG with letter-restricted prefix completion options.
    """
    def __init__(self, *args, **kwargs):
        super(ScrabbleDAWG, self).__init__(*args, **kwargs)

    def _get_index_from_prefix(self, prefix):
        given = prefix
        index = self.dct.ROOT
        prefix, = _encode(prefix)
        for ch in prefix:
            index = self.dct.follow_char(int_from_byte(ch), index)
            if not index:
                return None
        return index

    def _complete(self, index, prefix, letters):
        for ch in letters:
            next_index = self.dct.follow_char(int_from_byte(ch), index)

            if next_index:

                # Check if terminal
                if self._has_value(next_index):
                    yield prefix + [ch]

                # Recurse with remaining letters
                remaining_letters = letters[:]
                remaining_letters.remove(ch)
                yield from self._complete(next_index,
                                          prefix + [ch],
                                          remaining_letters)

    def get_completions(self, prefix, letters):
        """
        Returns all words that start with prefix and end in some permutation
        of one or more of letters.
        """
        # Encode all as utf8
        prefix, letters = _encode(prefix, letters)

        completions = []

        # traverse dawg along current prefix
        index = self._get_index_from_prefix(prefix)
        if not index:
            return completions

        # Attempt traversing with remaining rack letters
        for word_bytes in self._complete(index, prefix, letters):
            completions.append(byte_array_to_str(word_bytes))

        return completions


    def _gen_possible_placements(self, index, letters):
        """Generate possible letter placements after the given index."""
        # Check which letters are valid
        for letter in letters:
            next_index = self.dct.follow_char(int_from_byte(letter), index)
            if next_index:
                yield next_index, chr(letter)

    def gen_possible_placements(self, prefix, rack_ls, valid_letters):
        """
        Generate all possible letter placements with the given letters placed
        after the given prefix.
        """
        letters = [ch for ch in rack_ls if ch in valid_letters]
        if WILDCARD in rack_ls:
            letters = valid_letters
        prefix, letters = _encode(prefix, letters)

        # Traverse current prefix
        index = self._get_index_from_prefix(prefix)
        if not index:
            return []

        for _, ch in self._gen_possible_placements(index, letters):
            yield ch


    def _gen_prefixes_with_length(self, index, rack_ls, row_valid_letters, placed):
        """
        Generate all prefixes with the given letters and valid placements
        of length len(valid_letters), starting with index.
        """
        if not row_valid_letters:
            # Out of space
            yield '', rack_ls
            return

        # find placeable letters
        letters = [ch for ch in rack_ls if ch in row_valid_letters[0]]
        if WILDCARD in rack_ls:
            letters = row_valid_letters[0]
        letters, = _encode(letters)

        if not rack_ls or not letters:
            # No valid placements
            return

        # check valid first placement, prepend to rest of word
        for next_index, ch in self._gen_possible_placements(index, letters):
            # if tile is already placed, don't take one of our tiles
            if placed[0]:
                #print('TILE PLACED')
                assert(len(row_valid_letters[0]) == 1)
                for wordpart, remaining in self._gen_prefixes_with_length(
                        next_index,
                        rack_ls,
                        row_valid_letters[1:],
                        placed[1:]):
                    yield ch + wordpart, remaining
                return

            # if wildcard present, split on using it or not
            if WILDCARD in rack_ls:
                for wordpart, remaining in self._gen_prefixes_with_length(
                        next_index,
                        rack_ls.replace(WILDCARD, '', 1),
                        row_valid_letters[1:],
                        placed[1:]):
                    yield ch.upper() + wordpart, remaining

            if ch in rack_ls:       # letter could be from wildcard
                for wordpart, remaining in self._gen_prefixes_with_length(
                        next_index,
                        rack_ls.replace(ch, '', 1),
                        row_valid_letters[1:],
                        placed[1:]):
                    yield ch + wordpart, remaining

    def gen_valid_prefixes(self, rack_ls, row, row_valid_letters):
        """
        Generate all valid word prefixes with the given rack letters on the
        given row (arbitrary row length, usually slice of an actual row).
        """
        assert(len(row) == len(row_valid_letters))
        rack_ls = ''.join(rack_ls)

        placed = [bool(c) for c in row]

        for length in range(len(row) + 1):
            # Skip when tile is placed before this one
            if length < len(row) and placed[-1-length]:
                #print(f'length {length} skipped')
                continue

            # Generate possible prefixes with given length
            #print('evaluating prefix length', length)
            #print('PLACED:', placed)
            letters, placed_s = row_valid_letters[-length:], placed[-length:]
            if length == 0:
                letters, placed_s = [], []
            #print(placed_s)
            yield from self._gen_prefixes_with_length(
                self.dct.ROOT,
                rack_ls,
                letters,
                placed_s
            )

    def _gen_right_extensions(self, index, rack_ls, row_valid_letters, placed):
        # If tile is placed, must use it before checking word
        if placed and placed[0]:
            assert(len(row_valid_letters[0]) == 1)
            letters, = _encode(row_valid_letters[0])
            for next_index, ch in self._gen_possible_placements(index, letters): # only placed tile
                for suffix, remaining in self._gen_right_extensions(
                        next_index,
                        rack_ls,
                        row_valid_letters[1:],
                        placed[1:]):
                    yield ch + suffix, remaining
            return

        # Return any possible word if the next tile is open or wall
        #print(f'right placed: {placed}')
        if self._has_value(index) and (len(placed) < 2 or not placed[1]):
            yield '', rack_ls

        if not row_valid_letters:
            # Out of space
            return

        # find placeable letters
        letters = [ch for ch in rack_ls if ch in row_valid_letters[0]]
        if WILDCARD in rack_ls:
            letters = row_valid_letters[0]
        letters, = _encode(letters)

        if not rack_ls or not letters:
            # No more valid placements
            return

        # Attempt to place letter
        for next_index, ch in self._gen_possible_placements(index, letters):
            # if wildcard present, split on using it or not
            if WILDCARD in rack_ls:
                for suffix, remaining in self._gen_right_extensions(
                        next_index,
                        rack_ls.replace(WILDCARD, '', 1),
                        row_valid_letters[1:],
                        placed[1:]):
                    yield ch.upper() + suffix, remaining

            if ch in rack_ls:       # letter could be from wildcard
                for suffix, remaining in self._gen_right_extensions(
                        next_index,
                        rack_ls.replace(ch, '', 1),
                        row_valid_letters[1:],
                        placed[1:]):
                    yield ch + suffix, remaining

    def gen_right_extensions(self, prefix, rack_ls, row, row_valid_letters):
        """
        Generate all valid words starting with the given prefix on the given
        partial row.
        """
        formatted_prefix = prefix
        prefix = prefix.lower()


        assert(len(row) == len(row_valid_letters))
        rack_ls = ''.join(rack_ls)

        placed = [bool(c) for c in row]
        index = self._get_index_from_prefix(prefix)

        # FIXME Special case right now for single letter adds
        # FIXME likely double-counting some of these
        # FIXME this is wrong
        #if not prefix:
        #    single_letters = [ch for ch in rack_ls if ch in row_valid_letters[0]]
        #    if WILDCARD in rack_ls:
        #        single_letters = row_valid_letters[0]
        #    for ch in single_letters:
        #        if WILDCARD in rack_ls:
        #            yield ch.upper(), rack_ls.replace(WILDCARD, '', 1)
        #        if ch in rack_ls:
        #            yield ch, rack_ls.replace(ch, '', 1)

        # Generate right extensions from the given prefix
        for suffix, remaining in self._gen_right_extensions(
                index, rack_ls, row_valid_letters, placed):
            if not suffix:          # must have letter on anchor
                continue
            yield formatted_prefix + suffix, remaining


def byte_array_to_str(byte_array):
    return ''.join([chr(ch) for ch in byte_array])


def _encode(*args):
    encoded = ()
    for letters in args:
        enc_letters = ''.join(letters)
        if not isinstance(letters, bytes):
            enc_letters = enc_letters.encode('utf8')
        encoded += ([c for c in enc_letters],)
    return encoded
