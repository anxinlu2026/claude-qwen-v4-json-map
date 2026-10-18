#!/usr/bin/env python3
"""Check that the drafts for agent.md / skills stay general: no design-specific or episode-specific words.
usage: check_general.py FILE [FILE ...]   (exit 1 when a forbidden word appears)"""
import re, sys
FORBID = [r'\bAES\b', r'aes128', r'round_ff', r'\bo_done\b', r'\bi_start\b', r'key_done', r'xtime', r'MixColumns', r'ShiftRows', r'SubBytes', r'state_reg', r'\bblk\d+', r'round_mux', r'Rcon', r'FIPS', r'load_block',
          r'\bstart\b.*(accept|接受)', r'(accept|接受).*\bstart\b', r'\bstart 被', r'v5a', r'Codex', r'Qwen', r'transpos', r'轉置', r'JSON map flow']
bad = 0
for f in sys.argv[1:]:
    for n, line in enumerate(open(f, encoding='utf-8'), 1):
        for p in FORBID:
            if re.search(p, line, flags=re.I if p.startswith('\\bstart') else 0):
                print(f'{f}:{n}: matches {p!r}: {line.strip()[:110]}'); bad += 1
print(f'{bad} problem(s)'); sys.exit(1 if bad else 0)
