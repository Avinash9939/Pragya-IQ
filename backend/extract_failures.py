import sys

lines = open('all_tests_fixed.txt', encoding='utf-8').read().split('\n')
failures = []
in_fail = False
cur = []
for l in lines:
    if l.startswith('____') or l.startswith('=== FAILURES ==='):
        if cur:
            failures.append('\n'.join(cur))
            cur = []
        in_fail = True
    if in_fail:
        cur.append(l)
    if l.startswith('====') and 'FAILURES' not in l and in_fail:
        if cur:
            failures.append('\n'.join(cur))
            cur = []
        in_fail = False
if cur:
    failures.append('\n'.join(cur))

open('failed_tracebacks.txt', 'w', encoding='utf-8').write('\n\n=======================================================\n\n'.join(failures))
print(f"Extracted {len(failures)} failures.")
