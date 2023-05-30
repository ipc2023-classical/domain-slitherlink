#!/usr/bin/env python3

import sys
import re
import random

pat_edge = re.compile(r'^edge\(([a-zA-Z_0-9]+), *([a-zA-Z_0-9]+)\)\.$')
pat_clue = re.compile(r'^clue\(([a-z_A-Z0-9]+), *([0-9]+)\)\.$')
pat_cell = re.compile(r'^cell_contains\(([a-z_A-Z0-9]+), *([a-zA-Z_0-9]+), *([a-zA-Z_0-9]+)\)\.$')

def main():
    edges = {}
    clues = {}
    cells = {}
    cap = {}

    for line in sys.stdin:
        m = pat_edge.match(line.strip())
        if m is not None:
            n1 = m.group(1)
            n2 = m.group(2)
            e = (n1, n2)
            assert(e not in edges)
            edges[e] = []
            continue

        m = pat_clue.match(line.strip())
        if m is not None:
            c = m.group(1)
            clue = int(m.group(2))
            assert(c not in clues)
            clues[c] = clue
            continue

        m = pat_cell.match(line.strip())
        if m is not None:
            c = m.group(1)
            n1 = m.group(2)
            n2 = m.group(3)
            if c not in cells:
                cells[c] = []
            cells[c] += [(n1, n2)]
            continue

    for cell, es in cells.items():
        assert(len(es) == len(set(es)))
        if cell in clues:
            cap[cell] = clues[cell]
        else:
            cap[cell] = len(es)

        for e in es:
            if e not in edges:
                n1, n2 = e
                e = (n2, n1)
            assert(e in edges)
            edges[e] += [cell]

    for e, c in edges.items():
        assert(len(c) in [1,2])
        if len(c) == 1:
            n1, n2 = e
            name = f'outside-cell-{n1}-{n2}'
            edges[e] += [name]
            cap[name] = 1
            cells[name] = [e]

    nodes = []
    for e in edges.keys():
        n1, n2 = e
        nodes += [n1]
        nodes += [n2]
    nodes = sorted(list(set(nodes)))

    max_capacity = max(cap.values())
    capacity = ['cap-{0}'.format(i) for i in range(max_capacity + 1)]
    capacity_inc = []
    for i in range(max_capacity):
        capacity_inc += ['(cell-capacity-inc cap-{0} cap-{1})'.format(i, i + 1)]

    nodeobjs = ['n-{0}'.format(x) for x in nodes]
    cellobjs = ['c-{0}'.format(x) for x in sorted(cells.keys())]
    cellcap = []
    for cname, cp in cap.items():
        cellcap += [f'(cell-capacity c-{cname} cap-{cp})']
    cellcap = sorted(cellcap)

    nodefree = []
    nodegoal = []
    for n in nodes:
        nodefree += [f'(node-degree0 n-{n})']
        nodegoal += [f'(not (node-degree1 n-{n}))']
    nodefree = sorted(nodefree)
    nodegoal = sorted(nodegoal)

    not_linked = []
    cell_edge = []
    for (n1, n2), (c1, c2) in edges.items():
        cell_edge += [f'(cell-edge c-{c1} c-{c2} n-{n1} n-{n2})']
        #not_linked += [f'(not-linked n-{n1} n-{n2})']

    goal_cap = []
    for c, clue in clues.items():
        assert(clue <= cap[c])
        goal_cap += [f'(cell-capacity c-{c} cap-0)']

    capacity = ' '.join(capacity)
    capacity_inc = '\n    '.join(capacity_inc)
    nodeobjs = ' '.join(nodeobjs)
    cellobjs = ' '.join(cellobjs)
    cellcap = '\n    '.join(cellcap)
    nodefree = '\n    '.join(nodefree)
    nodegoal = '\n        '.join(nodegoal)
    cell_edge = '\n    '.join(cell_edge)
    not_linked = '\n    '.join(not_linked)
    goal_cap = '\n        '.join(goal_cap)

    s = f'''(define (problem sliterlink-xxx)
(:domain slitherlink)

(:objects
    {capacity} - cell-capacity-level
    {nodeobjs} - node
    {cellobjs} - cell
)

(:init
    {capacity_inc}

    {cellcap}

    {nodefree}

    {cell_edge}

    {not_linked}
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
    return 0

if __name__ == '__main__':
    sys.exit(main())
