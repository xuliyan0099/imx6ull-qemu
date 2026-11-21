#!/usr/bin/env python3
import re
import sys
from pathlib import Path

def find_block(lines, compat):
    """Return (start, end) line indices of node whose compatible contains compat."""
    for i, line in enumerate(lines):
        m = re.match(r'\s*compatible\s*=\s*"([^"]*)"', line)
        if m and compat in m.group(1):
            # backtrack to opening node line
            j = i
            while j >= 0 and not lines[j].rstrip().endswith('{'):
                j -= 1
            if j < 0:
                continue
            depth = 0
            k = j
            while k < len(lines):
                # count braces outside quoted strings
                s = lines[k]
                in_str = False
                for ch in s:
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

def set_status(text, compat, status):
    lines = text.splitlines(keepends=True)
    blk = find_block(lines, compat)
    if not blk:
        print(f'missing: {compat}', file=sys.stderr)
        return text, False
    start, end = blk
    # look for status in block
    for n in range(start, end + 1):
        if re.match(r'\s*status\s*=', lines[n]):
            lines[n] = re.sub(r'status\s*=\s*"[^"]*"', f'status = "{status}"', lines[n])
            return ''.join(lines), True
    # insert after opening brace line, match indentation of compat line
    indent = re.match(r'(\s*)', lines[start]).group(1) + '\t'
    lines.insert(start + 1, f'{indent}status = "{status}";\n')
    return ''.join(lines), True

def main():
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    text = src.read_text()
    targets = sys.argv[3:]
    for t in targets:
        text, ok = set_status(text, t, 'disabled')
        print(('disabled ' if ok else 'MISSING  ') + t)
    dst.write_text(text)
    print(f'wrote {dst}')

if __name__ == '__main__':
    main()
