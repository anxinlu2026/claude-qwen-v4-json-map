#!/usr/bin/env python3
"""Start the HDL files of round K+1 from those of round K: copy hdl-*-rtl-vK.json to -v(K+1).json with the envelope round updated, harness_result cleared,
status 'open' and no_change false; everything else (map, ports, questions, assumptions, replies, rtl_changes of earlier rounds) is kept for the HDL engineer to update.
usage: next_round_hdl.py EXCHANGE_DIR K"""
import glob, json, os, re, sys
ex, K = sys.argv[1], int(sys.argv[2])
for f in sorted(glob.glob(os.path.join(ex, f'hdl-*-rtl-v{K}.json'))):
    d = json.load(open(f)); d['round'] = K + 1
    if d.get('block') != 'top': d['harness_result'] = {}; d['status'] = 'open'
    d['no_change'] = False
    out = re.sub(rf'-v{K}\.json$', f'-v{K + 1}.json', f)
    if os.path.exists(out): print('exists, skipped:', os.path.basename(out)); continue
    json.dump(d, open(out, 'w'), ensure_ascii=False, indent=1); print('wrote', os.path.basename(out))
