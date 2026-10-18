#!/usr/bin/env python3
"""Insert a draft section into an agent.md before a given heading (idempotent).
usage: apply_drafts.py DRAFT.md TARGET_agent.md "ANCHOR HEADING TEXT"   (the section is the draft from its first '## ' heading to the end)"""
import sys
d, t, anchor = sys.argv[1:4]
txt = open(d, encoding='utf-8').read(); sec = txt[txt.index('\n## ') + 1:].rstrip('\n') + '\n\n'
head = sec.split('\n', 1)[0]
tgt = open(t, encoding='utf-8').read()
if head in tgt: print('already present:', head); sys.exit(0)
i = tgt.index('\n' + anchor) + 1
open(t, 'w', encoding='utf-8').write(tgt[:i] + sec + tgt[i:]); print('inserted', head, 'before', anchor, 'in', t)
