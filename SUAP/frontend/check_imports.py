#!/usr/bin/env python
"""Check for broken imports in frontend."""
import os, re

errors = []
count = 0
for root, dirs, files in os.walk('src'):
    for f in files:
        if f.endswith('.jsx'):
            count += 1
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                content = fp.read()
            imports = re.findall(r"from\s+'([^']+)'|from\s+\"([^\"]+)\"", content)
            for imp_tup in imports:
                imp = imp_tup[0] or imp_tup[1]
                if imp.startswith('@/') and not imp.endswith('.css'):
                    rel = imp.replace('@/', 'src/')
                    if not os.path.isfile(rel):
                        if not os.path.isfile(rel + '.jsx') and not os.path.isfile(rel + '.js'):
                            errors.append(f'{path}: NOT FOUND: {imp}')

print(f'Files checked: {count}')
print(f'Broken imports: {len(errors)}')
for e in errors:
    print(f'  [ERR] {e}')
