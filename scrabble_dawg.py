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

        index = self.dct.ROOT

        # traverse dawg along current prefix
        for ch in prefix:
            index = self.dct.follow_char(int_from_byte(ch), index)
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
        index = self.dct.ROOT
        for ch in prefix:
            index = self.dct.follow_char(int_from_byte(ch), index)
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
                for wordpart, remaining in self._gen_prefixes_with_length(
                    next_index,
                    rack_ls,
                    row_valid_letters[1:],
                    placed[1:]
                ):
                    yield ch + wordpart, remaining
                return

            # if wildcard present, split on using it or not
            if WILDCARD in rack_ls:
                for wordpart, remaining in self._gen_prefixes_with_length(
                    next_index,
                    rack_ls.replace(WILDCARD, '', 1),
                    row_valid_letters[1:],
                    placed[1:]
                ):
                    yield ch + wordpart, remaining

            if ch in rack_ls:       # letter could be from wildcard
                for wordpart, remaining in self._gen_prefixes_with_length(
                    next_index,
                    rack_ls.replace(ch, '', 1),
                    row_valid_letters[1:],
                    placed[1:]
                ):
                    yield ch + wordpart, remaining



    def gen_valid_prefixes(self, rack_ls, row, row_valid_letters):
        """
        Generates all valid words with the given rack letters on the given
        row (arbitrary row length, usually slice of an actual row).
        """
        assert(len(row) == len(row_valid_letters))
        rack_ls = ''.join(rack_ls)

        placed = [bool(c) for c in row]
        for length in range(len(row) + 1):
            if length < len(row) and placed[-1-length]:
                continue
            # Generate possible prefixes with given length
            #print('evaluating length', length)
            yield from self._gen_prefixes_with_length(
                self.dct.ROOT,
                rack_ls,
                row_valid_letters[-length:],
                placed[-length:]
            )





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
