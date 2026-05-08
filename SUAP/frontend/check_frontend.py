#!/usr/bin/env python
"""Check frontend for potential errors."""
import os

print("=" * 60)
print("FRONTEND VERIFICATION")
print("=" * 60)

# Check directory structure
for dir_name in ['src/pages', 'src/components', 'src/context', 'src/api']:
    path = f'src/{dir_name}' if '/' not in dir_name.replace('src/', '') else dir_name
    if os.path.isdir(dir_name):
        files = [f for f in os.listdir(dir_name) if f.endswith('.jsx') or f.endswith('.js')]
        print(f"[OK] {dir_name}: {len(files)} files")

# Check imports in App.jsx match actual files
import re
with open('src/App.jsx', 'r', encoding='utf-8') as f:
    app_content = f.read()

# Find all lazy imports
imports = re.findall(r"import\(['\"]@/pages/([^'\"]+)['\"]\)", app_content)
imports += re.findall(r"import\(['\"]@/modules/([^'\"]+)['\"]\)", app_content)

missing = []
for imp in sorted(set(imports)):
    full_path = f'src/{imp}'
    if not os.path.isfile(full_path):
        missing.append(imp)

if missing:
    print(f"\n[ERROR] Missing imports ({len(missing)}):")
    for m in missing:
        print(f"  - @/pages/{m}")
else:
    print(f"\n[OK] All {len(set(imports))} lazy imports match existing files")

# Check for common patterns
print("\n--- Checking component exports ---")
for root, dirs, files in os.walk('src'):
    for f in files:
        if f.endswith('.jsx'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                content = fp.read()
            if 'export default' not in content and 'App.jsx' not in path and 'main.jsx' not in path:
                print(f"[WARN] {path} - No default export")

# Check context
if os.path.isfile('src/context/AuthContext.jsx'):
    print("[OK] AuthContext exists")
if os.path.isfile('src/api/axios.js') or os.path.isfile('src/api/client.js') or os.path.isfile('src/api/index.js'):
    print("[OK] API module exists")

print("\n--- Vite config ---")
if os.path.isfile('vite.config.js'):
    with open('vite.config.js', 'r') as f:
        print(f.read())

print("\n--- index.html ---")
if os.path.isfile('index.html'):
    with open('index.html', 'r') as f:
        content = f.read()
    if 'root' in content:
        print("[OK] index.html has #root div")
    if 'main.jsx' in content or 'main.js' in content:
        print("[OK] index.html references entry point")

print("\n--- END ---")
