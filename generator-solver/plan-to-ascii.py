#!/usr/bin/env python3

import sys

def main(plan_fn, idx = ''):
    NODE_NAME = 'n' + idx
    if NODE_NAME == 'n0':
        NODE_NAME = 'n'

    row_edge = []
    col_edge = []
    cols = 0
    rows = 0
    fin = open(plan_fn, 'r')
    for line in fin:
        if line.startswith('(link-'):
            s = line.split()
            name, n1row, n1col = s[1].split('-')
            name2, n2row, n2col = s[2].split('-')
            assert(name == name2)
            if name != NODE_NAME:
                continue
            n1row = int(n1row)
            n1col = int(n1col)
            n2row = int(n2row)
            n2col = int(n2col)
            assert(n1row == n2row or n1col == n2col)

            if n1row == n2row:
                row_edge += [((n1row, n1col), (n2row, n2col))]
            else:
                col_edge += [((n1row, n1col), (n2row, n2col))]

            rows = max(rows, n1row + 1, n2row + 1)
            cols = max(cols, n1col + 1, n2col + 1)
    fin.close()

    out = []
    for i in range(2 * rows - 1):
        out += [[' ' for j in range(2 * cols - 1)]]

    for ri in range(len(out)):
        if ri % 2 == 1:
            continue
        for i, c in enumerate(out[ri]):
            if i % 2 == 0:
                out[ri][i] = '+'

    for ((r1, c1), (r2, c2)) in row_edge:
        assert(r1 == r2)
        assert(abs(c1 - c2) == 1)
        row = 2 * r1
        col = min(c1, c2) * 2
        out[row][col + 1] = '-'

    for ((r1, c1), (r2, c2)) in col_edge:
        assert(c1 == c2)
        assert(abs(r1 - r2) == 1)
        col = 2 * c1
        row = min(r1, r2) * 2
        out[row + 1][col] = '|'

    for row in out:
        print(''.join(row))

if __name__ == '__main__':
    if len(sys.argv) not in [2, 3]:
        print('Usage: {0} problem.plan [sub-idx]'.format(sys.argv[0]), file = sys.stderr)
        sys.exit(-1)

    sys.exit(main(*sys.argv[1:]))
