#!/usr/bin/env python3
"""Change list from the difference between the original and the current implementation, reconciled with the records the HDL engineer wrote.
A change unit is a region of changed lines; regions separated by at most --gap unchanged lines are merged (default 0).
usage: change_list.py ORIG_DIR CUR_DIR [--records EXCHANGE_DIR] [--round K] [--gap N] [--out FILE]
The records are the rtl_changes of hdl-blk*-rtl-v<K>.json (file, lines). A record matches a region when its line range overlaps the region
in either the original or the current numbering. Output lists regions, records, records that match no region, regions no record covers,
distinct places and records that repeat a place."""
import difflib, glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usage
a = sys.argv[1:]; opts = {}; pos = []
i = 0
while i < len(a):
    if a[i] in ('--records', '--round', '--gap', '--out'): opts[a[i]] = a[i + 1]; i += 2
    else: pos.append(a[i]); i += 1
orig, cur = pos[:2]; gap = int(opts.get('--gap', 0)); K = opts.get('--round')
regions = []
for f in sorted(os.listdir(cur)):
    if not f.endswith(('.sv', '.v')): continue
    o = open(os.path.join(orig, f), encoding='utf-8', errors='replace').read().splitlines() if os.path.exists(os.path.join(orig, f)) else []
    c = open(os.path.join(cur, f), encoding='utf-8', errors='replace').read().splitlines()
    ops = [op for op in difflib.SequenceMatcher(None, o, c, autojunk=False).get_opcodes() if op[0] != 'equal']
    merged = []
    for tag, i1, i2, j1, j2 in ops:
        if merged and i1 - merged[-1][1] <= gap and j1 - merged[-1][3] <= gap: merged[-1] = [merged[-1][0], i2, merged[-1][2], j2]
        else: merged.append([i1, i2, j1, j2])
    for i1, i2, j1, j2 in merged:
        regions.append({"file": f, "orig_lines": f"{i1 + 1}-{i2}" if i2 > i1 else f"{i1}(insert)", "cur_lines": f"{j1 + 1}-{j2}" if j2 > j1 else f"{j1}(delete)",
                        "removed": len(o[i1:i2]), "added": len(c[j1:j2]), "_o": (i1 + 1, max(i2, i1 + 1)), "_c": (j1 + 1, max(j2, j1 + 1))})
for n, r in enumerate(regions, 1): r['id'] = f'd{n}'
recs = []
if '--records' in opts:
    ex = opts['--records']; k = K if K is not None else '*'
    for p in sorted(glob.glob(os.path.join(ex, f'hdl-blk*-rtl-v{k}.json'))):
        d = json.load(open(p))
        for c_ in d.get('rtl_changes', []) or []:
            m = re.findall(r'\d+', str(c_.get('lines', ''))); lo, hi = (int(m[0]), int(m[-1])) if m else (None, None)
            recs.append({"block": d.get('block'), "id": c_.get('id'), "file": os.path.basename(str(c_.get('file', ''))), "lines": c_.get('lines'), "status": c_.get('status'), "_r": (lo, hi)})
ov = lambda x, y: x[0] is not None and x[0] <= y[1] and y[0] <= x[1]
for r in recs:
    r['regions'] = [g['id'] for g in regions if g['file'] == r['file'] and (ov(r['_r'], g['_o']) or ov(r['_r'], g['_c']))]
covered = {i for r in recs for i in r['regions']}
out = {"gap": gap, "regions": [{k: v for k, v in g.items() if not k.startswith('_')} for g in regions],
       "records": [{k: v for k, v in r.items() if not k.startswith('_')} for r in recs]}
if recs:
    key = {}
    for r in recs: key.setdefault(tuple(r['regions']), []).append(f"{r['block']}.{r['id']}")
    out["reconciliation"] = {"regions": len(regions), "records": len(recs), "records_matching_no_region": [f"{r['block']}.{r['id']}" for r in recs if not r['regions']],
                             "regions_without_record": [g['id'] for g in regions if g['id'] not in covered],
                             "distinct_record_places": len(key), "distinct_record_locations(file,lines)": len({(r['file'], str(r['lines'])) for r in recs}), "records_repeating_a_place": [v for v in key.values() if len(v) > 1]}
if '--out' in opts: json.dump(out, open(opts['--out'], 'w'), ensure_ascii=False, indent=1)
usage.log(opts.get('--records'), 'change_list', regions=len(regions), records=len(recs))
print(f"{len(regions)} change region(s) (gap {gap}); " + (f"{len(recs)} record(s); " + json.dumps(out['reconciliation'], ensure_ascii=False)[:600] if recs else 'no records given'))
for g in out['regions']: print(f"  {g['id']} {g['file']} orig {g['orig_lines']} -> cur {g['cur_lines']}  (-{g['removed']} +{g['added']})")
