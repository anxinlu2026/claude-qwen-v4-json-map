#!/usr/bin/env python3
"""Consistency of skills and tool: every `rtl <command>` named in skills / role files must be a command the tool provides (tools/rtl/rtl).
The tool is the reference: when a document names a command the tool lacks, the document is wrong (or the tool needs the command).
usage: check_skill_commands.py [ROOT]   (default: repo root; exit 1 when a document names a missing command)"""
import os, re, sys
root = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
src = open(os.path.join(root, 'tools', 'rtl', 'rtl')).read()
m = re.search(r"\{(\s*'sim': cmd_sim.*?)\}", src, re.S) or re.search(r"'sim': cmd_sim.*", src)
tool = set(re.findall(r"'([a-z_]+)': cmd_", src))
print('tool provides:', ' '.join(sorted(tool)))
bad = 0
for base in ('skills', 'image_skills', 'roles'):
    for dp, dn, fn in os.walk(os.path.join(root, base)):
        for f in fn:
            if not f.endswith('.md'): continue
            p = os.path.join(dp, f)
            for n, line in enumerate(open(p, encoding='utf-8', errors='replace'), 1):
                for c in re.findall(r'`rtl ([a-z_]+)', line):
                    if c not in tool and c not in ('tool',):
                        print(f'{os.path.relpath(p, root)}:{n}: names `rtl {c}`, which the tool does not provide'); bad += 1
print(f'{bad} document reference(s) to missing commands'); sys.exit(1 if bad else 0)
