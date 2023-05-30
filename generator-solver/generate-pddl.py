#!/usr/bin/env python3

import sys
import os
import requests
import random
from bs4 import BeautifulSoup

TOPDIR = os.path.dirname(os.path.realpath(__file__))


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

#get_puzzle('http://www.puzzle-loop.com/?v=0&size=5')
#get_puzzle('http://www.puzzle-loop.com/?v=0')
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

def txtToPddl(puzzle):
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
    print(s)

def generate(rows, cols):
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
            print(f';; {line}')

    txtToPddl(puzzle)

    os.unlink('tmp.gen.prob')
    os.unlink('tmp.gen.sol')


if __name__ == '__main__':
    sys.exit(generate(int(sys.argv[1]), int(sys.argv[2])))

    if len(sys.argv) != 2:
        print('Usage: {0} puzzle.txt >prob.pddl'.format(sys.argv[0]), file = sys.stderr)
        sys.exit(-1)
    sys.exit(main(sys.argv[1]))

