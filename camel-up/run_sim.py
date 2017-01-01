#!/usr/bin/env python3

import random
import sys
import traceback

from collections import defaultdict

COLOURS = ['green', 'blue', 'orange', 'yellow', 'white']
COLOUR_MAP = {
    'g': 'green',
    'b': 'blue',
    'o': 'orange',
    'y': 'yellow',
    'w': 'white',
}
MAX_SQUARE_DIST = 4
MAX_POS = 0
MAX_SQUARES = 4
ROLLOUTS = 50000
SQUARE_ROLLOUTS = 5000
ALL_MOVABLE = True
INTERACTIVE = True

class Board(object):
    def __init__(self):
        self.camels = {}
        self.squares = {}

    def add_square(self, position, direction):
        self.squares[position] = [direction, 0]

    def add_camel(self, colour, position, movable):
        height = 0
        for camel in self.camels:
            pos = self.camels[camel]
            if pos[0] == position:
                height = max(height, pos[1] + 1)
        self.set_camel(colour, position, height, movable)

    def set_camel(self, colour, position, height, movable):
        self.camels[colour] = (position, height, movable)

    def square_options(self):
        # Get positions of camels
        unavailable = set()
        lowest_pos = 16
        highest_pos = 0
        for camel in self.camels:
            position = self.camels[camel][0]
            lowest_pos = min(lowest_pos, position + 1)
            highest_pos = max(highest_pos, position + MAX_SQUARE_DIST)
            unavailable.add(position)
        for square in self.squares:
            unavailable.add(square)
            unavailable.add(square + 1)
            unavailable.add(square - 1)

        # Work out where squares can go
        square_options = []
        for i in range(lowest_pos, highest_pos):
            if i not in unavailable:
                square_options.append(i)
        return square_options

    def apply_roll(self, colour, number):
        position, height, movable = self.camels[colour]
        target = [position + number, 0]

        # Take into consideration +/- squares
        # Rules guarantee only one in a row
        if target[0] in self.squares:
            self.squares[target[0]][1] += 1
            target[0] += self.squares[target[0]][0]

        # Find all the camels that are moving
        moving = []
        for camel in self.camels:
            opos = self.camels[camel]
            if opos[0] == position and height <= opos[1]:
                moving.append((opos, camel))
            if opos[0] == target[0]:
                target[1] = max(target[1], opos[1] + 1)
        moving.sort()

        # Move the camels
        for opos, camel in moving:
            self.camels[camel] = (target[0], target[1], False)
            target[1] += 1

    def copy(self):
        ans = Board()
        for camel in self.camels:
            ans.camels[camel] = self.camels[camel]
        for square in self.squares:
            ans.squares[square] = self.squares[square][:]
        return ans

    def stack_size(self, pos):
        count = 0
        for camel in self.camels:
            if self.camels[camel][0] == pos:
                count += 1
        return count

    def leader(self, ignore=None):
        best = None
        best_colour = None
        for camel in self.camels:
            if camel == ignore:
                continue
            pos = self.camels[camel]
            if best is None or pos[0] > best[0] or (pos[0] == best[0] and pos[1] > best[1]):
                best = pos
                best_colour = camel
        return best_colour

    def second(self):
        best = self.leader()
        return self.leader(best)

    def __str__(self):
        ans = []
        camel_list = [(self.camels[camel], camel) for camel in self.camels]
        camel_list.sort()
        for pos, camel in camel_list:
            while pos[0] >= len(ans):
                ans.append('')
            ans[pos[0]] += camel[0]
            if not pos[2]:
                ans[pos[0]] += "!"
        for pos in self.squares:
            while pos >= len(ans):
                ans.append('')
            direction = self.squares[pos][0]
            if direction > 0:
                ans[pos] += '+'
            else:
                ans[pos] += '-'
        return '.'.join(ans)


def get_roll(available):
    colour = available[random.randint(0, len(available) - 1)]
    number = random.randint(1, 3)
    return (number, colour)

def read_state():
    # Format, a single line:
    # Letters: g b o y w
    # Squares: + -
    # Dot to indicate next square
    try:
        data = input("\nEnter current state:\n")
        init = Board()
        board_position = 0
        for pos in range(len(data)):
            char = data[pos]
            if char == '.':
                board_position += 1
            elif char == '+':
                init.add_square(board_position, 1)
            elif char == '-':
                init.add_square(board_position, -1)
            elif char in 'gboyw':
                movable = True
                if pos + 1 < len(data) and data[pos + 1] == '!':
                    movable = False
                init.add_camel(COLOUR_MAP[char], board_position, movable)
###                print("Insert", COLOUR_MAP[char], board_position, movable)
        return init
    except EOFError:
        return None

def add_random_camels(state):
    tops = {}
    for colour in COLOURS:
        position = random.randint(0, MAX_POS)
        movable = random.randint(0, 1) == 0
        if ALL_MOVABLE:
            movable = True
        state.add_camel(colour, position, movable)
        if position not in tops:
            tops[position] = 0
        tops[position] += 1
###    state.add_camel('green', 0)
###    state.add_camel('blue', 0)
###    state.add_camel('white', 0)
###    state.add_camel('orange', 19)
###    state.add_camel('yellow', 19)
###    tops = {0:3, 19:2}

def add_random_squares(state):
    # Get positions of camels
    unavailable = set()
    for camel in state.camels:
        position = state.camels[camel]
        unavailable.add(position[0])

    # Work out where squares can go
    for i in range(min(unavailable) + 1, max(unavailable) + MAX_SQUARE_DIST):
        if i not in unavailable:
            square_options.append(i)
    for i in range(random.randint(0, MAX_SQUARES)):
        if len(square_options) == 0:
            break
        to_add = square_options[random.randint(0, len(square_options) - 1)]
        direction = [-1, 1][random.randint(0, 1)]
        state.add_square(to_add, direction)
        pos = 0
        while pos < len(square_options):
            if abs(square_options[pos] - to_add) < 2:
                square_options.pop(pos)
            else:
                pos += 1

def do_rollout(init_state):
    cur = init_state.copy()
    cur_available = COLOURS[:]
    for camel in cur.camels:
        if not cur.camels[camel][2]:
            cur_available.remove(camel)
    while len(cur_available) > 0:
        square_options = cur.square_options()
        action = random.randint(0, 1)
        if action == 1 and len(square_options) > 0:
            addition = square_options[random.randint(0, len(square_options) - 1)]
            direction = (random.randint(0, 1) * 2) - 1
            cur.add_square(addition, direction)
        else:
            number, colour = get_roll(cur_available)
            cur_available.remove(colour)
            cur.apply_roll(colour, number)
    return cur

if INTERACTIVE:
    while True:
        try:
            init = read_state()
            if init is None:
                break

            # Do rollout
            counts = {camel: 0 for camel in COLOURS}
            counts_second = {camel: 0 for camel in COLOURS}
            for i in range(ROLLOUTS):
                cur = do_rollout(init.copy())
                counts[cur.leader()] += 1
                counts_second[cur.second()] += 1
                if i % 10000 == 0 and i > 0:
                    print("Done", i)
            counts_squares = defaultdict(lambda: 0)
            square_options = init.square_options()
            if len(square_options) > 0:
                for option in square_options:
                    for direction in [1, -1]:
                        for i in range(SQUARE_ROLLOUTS):
                            cur = init.copy()
                            cur.add_square(option, direction)
                            cur = do_rollout(cur)
                            score = cur.squares[option][1]
                            desc = '{}{}'.format(('+'+ str(direction))[-2], option)
                            counts_squares[desc] += score
            # Create summary
            ordering = []
            for camel in counts:
                ordering.append((counts[camel], counts_second[camel], camel))
            ordering.sort(reverse=True)
            for first_count, second_count, camel in ordering:
                name = "{:6}".format(camel)
                first = first_count / ROLLOUTS
                second = second_count / ROLLOUTS
                expected = []
                for num in [5, 3, 2]:
                    score = num * first + second - (1 - first - second)
                    summary = "{: 6.2f}".format(score)
                    expected.append(summary)

                print("{} {:>6.2f} {:>6.2f}  {}".format(name, first * 100, second * 100, ' '.join(expected)))
            ordering = []
            for square in counts_squares:
                score = counts_squares[square] / SQUARE_ROLLOUTS
                ordering.append((score, square))
            ordering.sort(reverse=True)
            for score, square in ordering:
                print(square, score)
        except Exception as inst:
            traceback.print_exc()
else:
    win_based_on_start = defaultdict(lambda: 0)
    for i in range(ROLLOUTS):
        init = Board()

        # Initialise the board
        # 1 - Add camels
        add_random_camels(init)
        # 2 - Add squares
        add_random_squares(init)

        # Note properties of the start state
        starting = {}
        for camel in init.camels:
            position = init.camels[camel]
            distance_from_top = init.stack_size(position[0]) - position[1] - 1

            # Add in whether there is a +/- square 1,2,3 in front
            square_info = ''
            for pos in init.squares:
                direction = init.squares[pos][0]
                distance = pos - init.camels[camel][0]
                if 0 < distance < 4:
                    square_info += "."+ str(distance)
                    if direction > 0:
                        square_info += "+"
                    else:
                        square_info += "-"
            while len(square_info) <= 6:
                square_info += "   "

            starting[camel] = (init.stack_size(position[0]), distance_from_top, square_info)

        # Do rollout   
        best_camel = do_rollout(init).leader()

        # Create summary
        best_info = "Stack height: {} Camel depth: {} Squares: {}".format(*starting[best_camel])
        win_based_on_start[best_info] += 1

    for key in win_based_on_start:
        print(key, " wins:", win_based_on_start[key])

