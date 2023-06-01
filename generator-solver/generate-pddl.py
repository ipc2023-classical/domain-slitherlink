#!/usr/bin/env python3

####
# The get_puzzle() function is adapted from https://github.com/pinkston3/slitherlink
# It was written by Donnie Pinkston and licensed under GPLv3
#
# The rest is in public domain.

import sys
import os
import random
import copy

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
    import requests
    from bs4 import BeautifulSoup
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

class Prob(object):
    def __init__(self, use_start_edge = False):
        self.use_start_edge = use_start_edge
        self.puzzles = []
        self.solutions = []
        self.capacity = [f'cap-{i}' for i in range(5)]
        self.capacity_inc = []
        for i in range(4):
            self.capacity_inc += ['(cell-capacity-inc cap-{0} cap-{1})'.format(i, i + 1)]

        self.nodes = []
        self.cells = []
        self.cell_capacity = []
        self.node_degree0 = []
        self.cell_edge = []
        self.nodegoal = []
        self.goal_cap = []
        self.linked = []

        self.plans = []

    def _chainPlan(self, plan):
        out = [plan[0]]
        nxt = plan[0][1]
        while len(out) != len(plan):
            found = False
            for step in plan:
                if step in out:
                    continue
                if nxt == step[0]:
                    out += [step]
                    nxt = step[1]
                    found = True
                    break
                elif nxt == step[1]:
                    out += [step]
                    nxt = step[0]
                    found = True
                    break
            if not found:
                print('PLAN IS INVALID!', file = sys.stderr)
                print(plan)
                sys.exit(-1)
        return out

    def add(self, puzzle, solution):
        IDX = ''
        if len(self.puzzles) > 0:
            IDX = str(len(self.puzzles))

        self.puzzles += [copy.deepcopy(puzzle)]
        self.solutions += [copy.deepcopy(solution)]

        rows = len(puzzle)
        cols = len(puzzle[0])

        plan = []
        for ri, srow in enumerate(solution):
            if ri % 2 == 0:
                for i in range(1, len(srow), 2):
                    if srow[i] == '-':
                        plan += [((ri // 2, i // 2), (ri // 2, i // 2 + 1))]
            else:
                for i in range(0, len(srow) + 1, 2):
                    if srow[i] == '|':
                        plan += [((ri // 2, i // 2), (ri // 2 + 1, i // 2))]
        plan = self._chainPlan(plan)
        self.plans += [plan]

        start_edge = ['', '']
        if self.use_start_edge:
            start_edge = [f'n{IDX}-{{0}}-{{1}}'.format(plan[0][0][0], plan[0][0][1]),
                          f'n{IDX}-{{0}}-{{1}}'.format(plan[0][1][0], plan[0][1][1])]
            self.linked += ['(linked {0} {1})'.format(*start_edge)]

        nodes = []
        for r in range(rows + 1):
            for c in range(cols + 1):
                nodes += [f'n{IDX}-{r}-{c}']

        cell_edge = []
        for r in range(1, rows):
            for c in range(cols):
                upcell = f'cell{IDX}-{r - 1}-{c}'
                downcell = f'cell{IDX}-{r}-{c}'
                cto = c + 1
                cell_edge += [f'(cell-edge {upcell} {downcell} n{IDX}-{r}-{c} n{IDX}-{r}-{cto})']
        for c in range(cols):
            r = 0
            upcell = f'cell{IDX}-outside-{c}-up'
            downcell = f'cell{IDX}-{r}-{c}'
            cto = c + 1
            cell_edge += [f'(cell-edge {upcell} {downcell} n{IDX}-{r}-{c} n{IDX}-{r}-{cto})']

            r = rows
            upcell = f'cell{IDX}-{r - 1}-{c}'
            downcell = f'cell{IDX}-outside-{c}-down'
            cto = c + 1
            cell_edge += [f'(cell-edge {upcell} {downcell} n{IDX}-{r}-{c} n{IDX}-{r}-{cto})']
        for c in range(1, cols):
            for r in range(rows):
                leftcell = f'cell{IDX}-{r}-{c - 1}'
                rightcell = f'cell{IDX}-{r}-{c}'
                rto = r + 1
                cell_edge += [f'(cell-edge {leftcell} {rightcell} n{IDX}-{r}-{c} n{IDX}-{rto}-{c})']
        for r in range(rows):
            c = 0
            leftcell = f'cell{IDX}-outside-{r}-left'
            rightcell = f'cell{IDX}-{r}-{c}'
            rto = r + 1
            cell_edge += [f'(cell-edge {leftcell} {rightcell} n{IDX}-{r}-{c} n{IDX}-{rto}-{c})']

            c = cols
            leftcell = f'cell{IDX}-{r}-{c - 1}'
            rightcell = f'cell{IDX}-outside-{r}-right'
            rto = r + 1
            cell_edge += [f'(cell-edge {leftcell} {rightcell} n{IDX}-{r}-{c} n{IDX}-{rto}-{c})']

        lowercap = []
        if self.use_start_edge:
            for c in cell_edge:
                if start_edge[0] in c and start_edge[1] in c:
                    s = c.split()
                    lowercap += [s[1], s[2]]

        goal_cap = []
        cell_capacity = []
        cells = []
        for r in range(rows):
            for c in range(cols):
                cells += [f'cell{IDX}-{r}-{c}']
        for r in range(rows):
            cap = 'cap-1'
            cell = f'cell{IDX}-outside-{r}-left'
            if cell in lowercap:
                cap = 'cap-0'
            cells += [cell]
            cell_capacity += [f'(cell-capacity {cell} {cap})']

            cap = 'cap-1'
            cell = f'cell{IDX}-outside-{r}-right'
            if cell in lowercap:
                cap = 'cap-0'
            cells += [cell]
            cell_capacity += [f'(cell-capacity {cell} {cap})']

        for c in range(cols):
            cap = 'cap-1'
            cell = f'cell{IDX}-outside-{c}-up'
            if cell in lowercap:
                cap = 'cap-0'
            cells += [cell]
            cell_capacity += [f'(cell-capacity {cell} {cap})']

            cap = 'cap-1'
            cell = f'cell{IDX}-outside-{c}-down'
            if cell in lowercap:
                cap = 'cap-0'
            cells += [cell]
            cell_capacity += [f'(cell-capacity {cell} {cap})']

        for i, row in enumerate(puzzle):
            for j, c in enumerate(row):
                cell = f'cell{IDX}-{i}-{j}'
                cap = 4
                if c != '.':
                    cap = int(c)
                    goal_cap += [f'(cell-capacity {cell} cap-0)']
                if cell in lowercap:
                    cap -= 1
                cell_capacity += [f'(cell-capacity {cell} cap-{cap})']


        node_degree0 = []
        for n in nodes:
            if n in start_edge:
                node_degree0 += [f'(node-degree1 {n})']
            else:
                node_degree0 += [f'(node-degree0 {n})']

        nodegoal = []
        for n in nodes:
            nodegoal += [f'(not (node-degree1 {n}))']
        nodegoal = sorted(nodegoal)

        self.nodes += nodes
        self.cells += cells
        self.cell_capacity += cell_capacity
        self.node_degree0 += node_degree0
        self.cell_edge += cell_edge
        self.nodegoal += nodegoal
        self.goal_cap += goal_cap

    def toPddl(self):
        capacity = ' '.join(self.capacity)
        nodes = ' '.join(self.nodes)
        cells = ' '.join(self.cells)

        capacity_inc = '\n    '.join(self.capacity_inc)
        cell_capacity = '\n    '.join(self.cell_capacity)
        node_degree0 = '\n    '.join(self.node_degree0)
        cell_edge = '\n    '.join(self.cell_edge)

        nodegoal = '\n        '.join(self.nodegoal)
        goal_cap = '\n        '.join(self.goal_cap)

        hcols = [len(x[0]) for x in self.puzzles]
        hcols += [len(x[0]) for x in self.solutions]
        hcols = max(hcols)
        assert(len(self.puzzles) == len(self.solutions))

        header = ''
        hrows = max([len(x) for x in self.puzzles])
        for row in range(hrows):
            header += ';;'
            for puzzle in self.puzzles:
                header += '  '
                if row < len(puzzle):
                    header += puzzle[row]
                    for _ in range(len(puzzle[row]), hcols):
                        header += ' '
                else:
                    for _ in range(hcols):
                        header += ' '
            header += '\n'

        header += ';;\n'
        hrows = max([len(x) for x in self.solutions])
        for row in range(hrows):
            header += ';;'
            for solution in self.solutions:
                header += '  '
                if row < len(solution):
                    header += solution[row]
                    for _ in range(len(solution[row]), hcols):
                        header += ' '
                else:
                    for _ in range(hcols):
                        header += ' '
            header += '\n'

        linked = copy.deepcopy(self.linked)
        if self.use_start_edge:
            linked += ['(disable-link-0-0)']
        linked = '\n    '.join(linked)
        rand = int(1000000 * random.random())
        s = f'''{header}
(define (problem sliterlink-{rand})
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

    {linked}
)
(:goal
    (and
        {nodegoal}

        {goal_cap}
    )
)
)


'''
        return s

    def addGen(self, rows, cols):
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

        solution = []
        with open('tmp.gen.sol', 'r') as fin:
            for line in fin:
                line = line.strip('\n')
                solution += [line]

        self.add(puzzle, solution)

        os.unlink('tmp.gen.prob')
        os.unlink('tmp.gen.sol')
        return 0

    def optimalCost(self):
        cost = sum([len(sol) for sol in self.plans])
        if self.use_start_edge:
            cost -= len(self.plans)
        return cost


def generate(rows, cols, fnpddl, fnplan, parallel = 1):
    prob = Prob(use_start_edge = (parallel > 1))

    for i in range(parallel):
        prob.addGen(rows, cols)

    out = prob.toPddl()
    with open(fnpddl, 'w') as fout:
        fout.write(';; {0}\n'.format(' '.join(sys.argv)))
        fout.write(';;\n')
        fout.write(out)

    with open(fnplan, 'w') as fout:
        fout.write(';; Optimal cost: {0}\n'.format(prob.optimalCost()))
    return 0

def download(spec, fnpddl, fnplan):
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

    solution = []
    with open('tmp.gen.sol', 'r') as fin:
        for line in fin:
            if len(line) == 0 or line[0] not in ['+', '|', ' ']:
                continue
            line = line.strip('\n')
            solution += [line]

    prob = Prob()
    prob.add(puzzle, solution)

    out = prob.toPddl()
    with open(fnpddl, 'w') as fout:
        fout.write(';; {0}\n'.format(' '.join(sys.argv)))
        fout.write(';;\n')
        fout.write(out)

    with open(fnplan, 'w') as fout:
        fout.write(';; Optimal cost: {0}\n'.format(prob.optimalCost()))

    os.unlink('tmp.gen.prob')
    os.unlink('tmp.gen.sol')


if __name__ == '__main__':
    if len(sys.argv) not in [7, 6, 5]:
        print('Usage: {0} gen num-rows num-colst prob.pddl prob.plan'.format(sys.argv[0]), file = sys.stderr)
        print('       {0} gen-parallel num-parallel num-rows num-colst prob.pddl prob.plan'.format(sys.argv[0]), file = sys.stderr)
        print('       {0} download spec prob.pddl prob.plan'.format(sys.argv[0]), file = sys.stderr)
        sys.exit(-1)

    if sys.argv[1] == 'gen':
        sys.exit(generate(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]))
    elif sys.argv[1] == 'gen-parallel':
        sys.exit(generate(int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6], parallel = int(sys.argv[2])))
    elif sys.argv[1] == 'download':
        sys.exit(download(sys.argv[2], sys.argv[3], sys.argv[4]))

