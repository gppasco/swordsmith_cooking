import utils


class Wordlist:
    def __init__(self, words):
        self.words = set(words)
        self.added_words = set()

        # create mapping from lengths to sets of words of that length
        self.words_by_length = {}
        for w in words:
            self._add_to_words_by_length(w)
    
    def _add_to_words_by_length(self, word):
        length = len(word)
        if length in self.words_by_length:
            self.words_by_length[length].add(word)
        else:
            self.words_by_length[length] = set([word])
    
    def _remove_from_words_by_length(self, word):
        length = len(word)
        if length in self.words_by_length:
            if word in self.words_by_length[length]:
                self.words_by_length[length].remove(word)
    
    def add_word(self, word):
        if word not in self.words:
            self.words.add(word)
            self.added_words.add(word)
            self._add_to_words_by_length(word)
    
    def remove_word(self, word):
        if word in self.words:
            self.words.remove(word)
            self._remove_from_words_by_length(word)
        if word in self.added_words:
            self.added_words.remove(word)


class Entry:
    def __init__(self, word):
        self.word = word
    
    def __str__(self):
        return self.word

    def __hash__(self):
        return hash((self.word))

    def __eq__(self, other):
        return self.word == other.word

    # return words in wordlist that match the pattern of this word
    # TODO: optimize this with a trie or regex or something
    def get_matches(self, wordlist):
        matches = []
        length = len(self.word)
        if length not in wordlist.words_by_length:
            return []
        for w in wordlist.words_by_length[length]:
            for i in range(length):
                if self.word[i] != Crossword.EMPTY and self.word[i] != w[i]:
                    break
            else:
                matches.append(w)
        return matches
    
    # returns number of words in wordlist that match pattern of this word
    # TODO: optimize this with a trie or regex or something
    def num_matches(self, wordlist):
        matches = 0
        length = len(self.word)
        if length not in wordlist.words_by_length:
            return 0
        for w in wordlist.words_by_length[length]:
            for i in range(length):
                if self.word[i] != Crossword.EMPTY and self.word[i] != w[i]:
                    break
            else:
                matches += 1
        return matches

    # returns whether word is completely filled
    def is_filled(self):
        return Crossword.EMPTY not in self.word

    # sets character at index to given character
    def set_letter_at_index(self, letter, i):
        self.word = self.word[0:i] + letter + self.word[i+1 :]


class Slot:
    ACROSS = 'A'
    DOWN = 'D'

    def __init__(self, row=0, col=0, dir=ACROSS):
        self.row = row
        self.col = col
        self.dir = dir

    def __hash__(self):
        return hash((self.row, self.col, self.dir))

    def __eq__(self, other):
        return (self.row, self.col, self.dir) == (other.row, other.col, other.dir)
    
    def __str__(self):
        return f'[{self.row}, {self.col}]-{self.dir}'


class Crossword:
    EMPTY = '.'
    BLOCK = '#'

    # fills grid of given size with empty squares
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.wordlist = None
        
        # initalize grid array
        self.grid = [[Crossword.EMPTY for c in range(cols)] for r in range(rows)]
        
        # initialize words maps
        self.entries = {}
        self.across_crossings = {}
        self.down_crossings = {}

        self.generate_entries()

    # prints crossword
    def __str__(self):
        output = ''
        for row in self.grid:
            for letter in row:
                output += letter
            output += '\n'
        return output

    # assign this crossword a wordlist
    def set_wordlist(self, wordlist):
        self.wordlist = wordlist
    
    # returns whether given grid Slot contains a letter
    def is_letter(self, row, col):
        return self.grid[row][col] != Crossword.EMPTY and self.grid[row][col] != Crossword.BLOCK
    
    # places word in given Slot
    def put_word(self, word, row=0, col=0, dir=Slot.ACROSS, add_to_wordlist=True):
        if add_to_wordlist and self.wordlist:
            self.wordlist.add_word(word)

        # place word in grid array
        if dir == Slot.DOWN:
            for y in range(len(word)):
                self.grid[row + y][col] = word[y]
        else:
            for x in range(len(word)):
                self.grid[row][col + x] = word[x]
        
        # place word in words map
        self.entries[Slot(row, col, dir)] = Entry(word)

        # alter crossing words in words map
        if dir == Slot.DOWN:
            for y in range(len(word)):
                crossing_slot = self.across_crossings[row + y, col]
                self.entries[crossing_slot].set_letter_at_index(word[y], col - crossing_slot.col)
        else:
            for x in range(len(word)):
                crossing_slot = self.down_crossings[row, col + x]
                self.entries[crossing_slot].set_letter_at_index(word[x], row - crossing_slot.row)
    
    # places block in certain slot
    def put_block(self, row, col):
        self.grid[row][col] = Crossword.BLOCK
        self.generate_entries()

    # generates dictionary that maps Slot to Entry
    def generate_entries(self):
        # reset words map
        self.entries = {}
        self.across_crossings = {}
        self.down_crossings = {}

        # generate across words
        for r in range(self.rows):
            curr_word = ''
            slot = Slot(0, 0, Slot.ACROSS)
            for c in range(self.cols):
                letter = self.grid[r][c]
                if letter != Crossword.BLOCK:
                    self.across_crossings[r, c] = slot
                    curr_word += letter
                    if len(curr_word) == 1:
                        slot.row = r
                        slot.col = c
                else:
                    if curr_word != '':
                        self.entries[slot] = Entry(curr_word)
                        curr_word = ''
                        slot = Slot(0, 0, Slot.ACROSS)
            if curr_word != '':
                self.entries[slot] = Entry(curr_word)

        # generate down words
        for c in range(self.cols):
            curr_word = ''
            slot = Slot(0, 0, Slot.DOWN)
            for r in range(self.rows):
                letter = self.grid[r][c]
                if letter != Crossword.BLOCK:
                    self.down_crossings[r, c] = slot
                    curr_word += letter
                    if len(curr_word) == 1:
                        slot.row = r
                        slot.col = c
                else:
                    if curr_word != '':
                        self.entries[slot] = Entry(curr_word)
                        curr_word = ''
                        slot = Slot(0, 0, Slot.DOWN)
            if curr_word != '':
                self.entries[slot] = Entry(curr_word)


    # prints the whole word map, nicely formatted
    def print_words(self):
        for slot in self.entries:
            print(slot.row, slot.col, slot.dir, self.entries[slot])

    # finds the slot that has the fewest possible matches, this is probably the best next place to look
    def fewest_matches(self):
        fewest_matches_slot = None
        fewest_matches = len(self.wordlist.words) + 1

        for slot in self.entries:
            word = self.entries[slot]
            if word.is_filled():
                continue
            matches = word.num_matches(self.wordlist)
            if matches < fewest_matches:
                fewest_matches = matches
                fewest_matches_slot = slot
        return (fewest_matches_slot, fewest_matches)

    # returns whether or not the whole crossword is filled
    def is_filled(self):
        for row in self.grid:
            for letter in row:
                if letter == Crossword.EMPTY:
                    return False
        return True

    # returns whether or not the crossword is validly filled
    def has_valid_words(self):
        for pos in self.entries:
            w = self.entries[pos]
            if w.is_filled() and w.word not in self.wordlist.words:
                return False
        return True

    # returns whether or not a given word is already in the grid
    # TODO: make more efficient with word set
    def is_dupe(self, word):
        for pos in self.entries:
            if self.entries[pos].word == word:
                return True
        return False
    
    # solves the crossword using a naive, terrible, dfs algorithm
    # TODO: optimize efficiency of this before moving onto heuristic-based algorithm
    def solve_dfs(self, printout=False):
        if printout:
            utils.clear_terminal()
            print(self)

        # choose slot with fewest matches
        slot, num_matches = self.fewest_matches()

        # if some slot has zero matches, fail
        if num_matches == 0:
            return False

        # if the grid is filled, succeed if every word is valid and otherwise fail
        if self.is_filled():
            return self.has_valid_words()
        
        # iterate through all possible matches in the fewest-match slot
        previous_word = self.entries[slot]
        matches = self.entries[slot].get_matches(self.wordlist)
        for match in matches:
            if self.is_dupe(match):
                continue
            # try placing the match in slot and try to solve with the match there, otherwise continue
            self.put_word(match, slot.row, slot.col, slot.dir)
            if not self.has_valid_words():
                continue
            if self.solve_dfs(printout=printout):
                return True
        # if no match works, restore previous word
        self.put_word(previous_word.word, slot.row, slot.col, slot.dir, add_to_wordlist=False)
        return False