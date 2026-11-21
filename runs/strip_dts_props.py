#!/usr/bin/env python3
import re
import sys
from pathlib import Path

def find_block(lines, needle):
    for i, line in enumerate(lines):
        if needle in line:
            j = i
            while j >= 0 and not lines[j].rstrip().endswith('{'):
                j -= 1
            if j < 0:
                continue
            depth = 0
            k = j
            while k < len(lines):
                in_str = False
                for ch in lines[k]:
                    if ch == '"':
                        in_str = not in_str
                    elif not in_str:
                        if ch == '{':
                            depth += 1
                        elif ch == '}':
                            depth -= 1
                            if depth == 0:
                                return j, k
                k += 1
    return None

def main():
    path = Path(sys.argv[1])
    needle = sys.argv[2]
    props = sys.argv[3:]
    lines = path.read_text().splitlines(keepends=True)
    blk = find_block(lines, needle)
    if not blk:
        print('node not found')
        return 1
    start, end = blk
    out = []
    removed = 0
    for n, line in enumerate(lines):
        if start < n <= end and any(re.match(r'\s*' + re.escape(p) + r'\s*=', line) for p in props):
            removed += 1
            continue
        out.append(line)
    path.write_text(''.join(out))
    print(f'removed {removed} props from {needle}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
