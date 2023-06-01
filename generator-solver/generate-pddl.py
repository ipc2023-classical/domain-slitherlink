#!/usr/bin/env python3

####
# The get_puzzle() function is adapted from https://github.com/pinkston3/slitherlink
# It was written by Donnie Pinkston and licensed under GPLv3
#
# The rest is in public domain.

import sys
import os
import requests
import random
from bs4 import BeautifulSoup

TOPDIR = os.path.dirname(os.path.realpath(__file__))

def solveCP(fn):

    cols = 0
    rows = 0
    clues = {}
    with open(fn, 'r') as fin:
        for row, line in enumerate(fin):
            line = line.strip()
            if len(line) == 0:
                break

            rows += 1
            for col, c in enumerate(line):
                cols = max(cols, col + 1)
                if c != '.':
                    clues[(row, col)] = int(c)

    from docplex.cp.model import CpoModel
    m = CpoModel()

    edge = []
    horizontal = []
    for row in range(rows + 1):
        hr = []
        for col in range(cols):
            v = m.binary_var(f'he-{row}-{col}')
            edge += [v]
            hr += [v]
        horizontal += [hr]

    vertical = []
    for row in range(rows):
        r = []
        for col in range(cols + 1):
            v = m.binary_var(f've-{row}-{col}')
            edge += [v]
            r += [v]
        vertical += [r]

    for row in range(rows):
        for col in range(cols):
            if (row, col) in clues:
                clue = clues[(row, col)]
                top = horizontal[row][col]
                bottom = horizontal[row + 1][col]
                left = vertical[row][col]
                right = vertical[row][col + 1]
                m.add(top + bottom + left + right == clue)

    for col in range(1, cols):
        left = horizontal[0][col - 1]
        right = horizontal[0][col]
        bottom = vertical[0][col]
        m.add((left + right + bottom) != 3)
        m.add((left + right + bottom) != 1)

        left = horizontal[rows][col - 1]
        right = horizontal[rows][col]
        top = vertical[rows - 1][col]
        m.add((left + right + top) != 3)
        m.add((left + right + top) != 1)

    for row in range(1, rows):
        up = vertical[row - 1][0]
        down = vertical[row][0]
        right = horizontal[row][0]
        m.add((up + down + right) != 3)
        m.add((up + down + right) != 1)

        up = vertical[row - 1][cols]
        down = vertical[row][cols]
        left = horizontal[row][cols - 1]
        m.add(up + down + left != 3)
        m.add(up + down + left != 1)

    m.add(horizontal[0][0] + vertical[0][0] != 1)
    m.add(horizontal[0][cols - 1] + vertical[0][cols] != 1)
    m.add(horizontal[rows][0] + vertical[rows - 1][0] != 1)
    m.add(horizontal[rows][cols - 1] + vertical[rows - 1][cols] != 1)
    for row in range(1, rows):
        for col in range(1, cols):
            up = vertical[row - 1][col]
            down = vertical[row][col]
            left = horizontal[row][col - 1]
            right = horizontal[row][col]
            m.add(up + down + left + right != 4)
            m.add(up + down + left + right != 3)
            m.add(up + down + left + right != 1)

    m.minimize(m.sum(edge))

    sol = m.solve()

    grid = [[' ' for _ in range(2 * cols + 1)] for __ in range(2 * rows + 1)]
    for r in range(rows + 1):
        for c in range(cols + 1):
            grid[2 * r][2 * c] = '+'
    for (r, c), v in clues.items():
        grid[2 * r + 1][2 * c + 1] = str(v)

    if sol:
        for ri, row in enumerate(horizontal):
            for ci, e in enumerate(row):
                if sol[e] > 0:
                    grid[2 * ri][2 * ci + 1] = '-'
        for ri, col in enumerate(vertical):
            for ci, e in enumerate(col):
                if sol[e] > 0:
                    grid[2 * ri + 1][2 * ci] = '|'

    s = ''
    for row in grid:
        for c in row:
            s += c
        s += '\n'
    return s



# Only works against the "old version" of the website, since the new version
# uses client-side Javascript to download and display the puzzle.  The "size"
# argument doesn't specify the actual puzzle size; rather, it maps to one of
# a number of sizes and difficulties.  Note that 'normal' puzzles can be solved
# by repeated rule-application, but 'hard' puzzles also require guessing.
#
# [no size] = 5x5 normal
#         4 = 5x5 hard
#        10 = 7x7 normal
#        11 = 7x7 hard
#         1 = 10x10 normal
#         5 = 10x10 hard
#         2 = 15x15 normal
#         6 = 15x15 hard
#         3 = 20x20 normal
#         7 = 20x20 hard
#         8 = 25x30 normal
#         9 = 25x30 hard
#        13 = special daily loop
#        12 = special weekly loop
#        14 = special monthly loop
def get_puzzle(page_url):
    page = requests.get(page_url)
    soup = BeautifulSoup(page.text, 'html.parser')

    puzzle_table = soup.find('table', id='LoopTable')

    puzzle_rows = puzzle_table.findAll('tr')
    puzzle_rows = puzzle_rows[1::2]

    row_specs = []

    for row in puzzle_rows:
        puzzle_cols = row.findAll('td')
        puzzle_cols = puzzle_cols[1::2]

        row_spec = ''

        for col in puzzle_cols:
            cellval = col.string
            if not cellval:
                cellval = '.'
            row_spec += cellval

        row_specs.append(row_spec)

    return row_specs

def txtToPddl(puzzle, out = sys.stdout):
    rows = len(puzzle)
    cols = len(puzzle[0])

    nodes = []
    for r in range(rows + 1):
        for c in range(cols + 1):
            nodes += [f'n-{r}-{c}']

    cells = []
    for r in range(rows):
        for c in range(cols):
            cells += [f'cell-{r}-{c}']

    goal_cap = []
    cell_capacity = []
    for i, row in enumerate(puzzle):
        for j, c in enumerate(row):
            if c != '.':
                cap = int(c)
                cell_capacity += [f'(cell-capacity cell-{i}-{j} cap-{cap})']
                goal_cap += [f'(cell-capacity cell-{i}-{j} cap-0)']
            else:
                cell_capacity += [f'(cell-capacity cell-{i}-{j} cap-4)']

    for r in range(rows):
        cells += [f'cell-outside-{r}-left']
        cell_capacity += [f'(cell-capacity cell-outside-{r}-left cap-1)']
        cells += [f'cell-outside-{r}-right']
        cell_capacity += [f'(cell-capacity cell-outside-{r}-right cap-1)']
    for c in range(cols):
        cells += [f'cell-outside-{c}-up']
        cell_capacity += [f'(cell-capacity cell-outside-{c}-up cap-1)']
        cells += [f'cell-outside-{c}-down']
        cell_capacity += [f'(cell-capacity cell-outside-{c}-down cap-1)']

    cell_edge = []
    for r in range(1, rows):
        for c in range(cols):
            upcell = 'cell-{0}-{1}'.format(r - 1, c)
            downcell = 'cell-{0}-{1}'.format(r, c)
            cto = c + 1
            cell_edge += [f'(cell-edge {upcell} {downcell} n-{r}-{c} n-{r}-{cto})']
    for c in range(cols):
        r = 0
        upcell = f'cell-outside-{c}-up'
        downcell = 'cell-{0}-{1}'.format(r, c)
        cto = c + 1
        cell_edge += [f'(cell-edge {upcell} {downcell} n-{r}-{c} n-{r}-{cto})']

        r = rows
        upcell = 'cell-{0}-{1}'.format(r - 1, c)
        downcell = f'cell-outside-{c}-down'
        cto = c + 1
        cell_edge += [f'(cell-edge {upcell} {downcell} n-{r}-{c} n-{r}-{cto})']
    for c in range(1, cols):
        for r in range(rows):
            leftcell = 'cell-{0}-{1}'.format(r, c - 1)
            rightcell = 'cell-{0}-{1}'.format(r, c)
            rto = r + 1
            cell_edge += [f'(cell-edge {leftcell} {rightcell} n-{r}-{c} n-{rto}-{c})']
    for r in range(rows):
        c = 0
        leftcell = 'cell-outside-{0}-left'.format(r)
        rightcell = 'cell-{0}-{1}'.format(r, c)
        rto = r + 1
        cell_edge += [f'(cell-edge {leftcell} {rightcell} n-{r}-{c} n-{rto}-{c})']

        c = cols
        leftcell = 'cell-{0}-{1}'.format(r, c - 1)
        rightcell = 'cell-outside-{0}-right'.format(r)
        rto = r + 1
        cell_edge += [f'(cell-edge {leftcell} {rightcell} n-{r}-{c} n-{rto}-{c})']

    capacity = [f'cap-{i}' for i in range(5)]
    capacity_inc = []
    for i in range(4):
        capacity_inc += ['(cell-capacity-inc cap-{0} cap-{1})'.format(i, i + 1)]

    node_degree0 = [f'(node-degree0 {n})' for n in nodes]

    nodefree = []
    nodegoal = []
    for n in nodes:
        nodefree += [f'(node-degree0 {n})']
        nodegoal += [f'(not (node-degree1 {n}))']
    nodefree = sorted(nodefree)
    nodegoal = sorted(nodegoal)

    capacity = ' '.join(capacity)
    nodes = ' '.join(nodes)
    cells = ' '.join(cells)

    capacity_inc = '\n    '.join(capacity_inc)
    cell_capacity = '\n    '.join(cell_capacity)
    node_degree0 = '\n    '.join(node_degree0)
    cell_edge = '\n    '.join(cell_edge)

    nodegoal = '\n        '.join(nodegoal)
    goal_cap = '\n        '.join(goal_cap)

    header = ''
    #for row in puzzle:
    #    header += f';; |{row}|\n'

    rand = int(1000000 * random.random())
    s = f'''{header}
(define (problem sliterlink-{rows}-{cols}-{rand})
(:domain slitherlink)

(:objects
    {capacity} - cell-capacity-level
    {nodes} - node
    {cells} - cell
)

(:init
    {capacity_inc}

    {cell_capacity}

    {node_degree0}

    {cell_edge}
)
(:goal
    (and
        {nodegoal}

        {goal_cap}
    )
)
)


'''
    print(s, file = out)

def generate(rows, cols, fnpddl, fnplan):
    pddlout = open(fnpddl, 'w')
    prog = os.path.join(TOPDIR, 'generate')
    if not os.path.isfile(prog):
        print(f'Error: Missing program {prog}', file = sys.stderr)
        return -1

    cmd = f'{prog} {rows} {cols} tmp.gen.prob tmp.gen.sol'
    ret = os.system(cmd)
    assert(ret == 0)

    puzzle = []
    with open('tmp.gen.prob', 'r') as fin:
        for line in fin:
            line = line.strip('\n')
            puzzle += [line]

    with open('tmp.gen.sol', 'r') as fin:
        for line in fin:
            line = line.strip('\n')
            print(f';; {line}', file = pddlout)

    solveCP('tmp.gen.prob')
    txtToPddl(puzzle, pddlout)

    os.unlink('tmp.gen.prob')
    os.unlink('tmp.gen.sol')
    pddlout.close()
    return 0

def download(spec, fnpddl, fnplan):
    pddlout = open(fnpddl, 'w')
    spec_map = {
        '5x5 normal' : None,
        '5x5 hard' : '4',
        '7x7 normal' : '10',
        '7x7 hard' : '11',
        '10x10 normal' : '1',
        '10x10 hard' : '5',
        '15x15 normal' : '2',
        '15x15 hard' : '6',
        '20x20 normal' : '3',
        '20x20 hard' : '7',
        '25x30 normal' : '8',
        '25x30 hard' : '9',
        'special daily loop' : '13',
        'special weekly loop' : '12',
        'special monthly loop' : '14',
    }

    if spec not in spec_map:
        print(f'Error: Unkown "{spec}"', file = sys.stderr)
        return -1

    url = 'http://www.puzzle-loop.com/?v=0'
    s = spec_map[spec]
    if s is not None:
        url += f'&size={s}'

    puzzle = get_puzzle(url)
    with open('tmp.gen.prob', 'w') as fout:
        for row in puzzle:
            fout.write(row + '\n')

    cmd = f'{TOPDIR}/solve tmp.gen.prob 100 >tmp.gen.sol'
    ret = os.system(cmd)
    assert(ret == 0)

    with open('tmp.gen.sol', 'r') as fin:
        for line in fin:
            line = line.strip('\n')
            if line.startswith('Showing up to'):
                continue
            print(f';; {line}', file = pddlout)

    txtToPddl(puzzle, pddlout)

    os.unlink('tmp.gen.prob')
    os.unlink('tmp.gen.sol')
    pddlout.close()


if __name__ == '__main__':
    if len(sys.argv) not in [6, 5]:
        print('Usage: {0} gen num-rows num-colst prob.pddl prob.plan'.format(sys.argv[0]), file = sys.stderr)
        print('       {0} download spec prob.pddl prob.plan'.format(sys.argv[0]), file = sys.stderr)
        sys.exit(-1)

    if sys.argv[1] == 'gen':
        sys.exit(generate(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]))
    elif sys.argv[1] == 'download':
        sys.exit(download(sys.argv[2], sys.argv[3], sys.argv[4]))

