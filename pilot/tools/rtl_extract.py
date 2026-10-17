#!/usr/bin/env python3
"""Extract the structure of an RTL design into a compact JSON (modules, ports, instances, registers, signals with their drivers).
The structure comes from yosys (read_verilog -sv; hierarchy; proc; opt_clean; write_json), not from reading the text.
usage: rtl_extract.py TOP FILE.sv [FILE.sv ...] > rtl_structure.json     (run where yosys is installed, e.g. in the cvdp-sim image)
Arrays are collapsed: current_data_ff[0][0] .. [3][3] -> one signal 'current_data_ff' with shape [4,4]."""
import json, re, subprocess, sys, tempfile, os
DFF = ('$dff', '$adff', '$dffe', '$adffe', '$sdff', '$sdffe', '$dlatch', '$aldff')

def run_yosys(top, files):
    d = tempfile.mkdtemp(); out = os.path.join(d, 'o.json')
    cmd = f'read_verilog -sv {" ".join(files)}; hierarchy -top {top}; proc; opt_clean; write_json {out}'
    subprocess.run(['yosys', '-q', '-p', cmd], check=True, capture_output=True)
    return json.load(open(out))

def base(n):
    return n.split('[')[0]

def shape_of(names):
    dims = {}
    for n in names:
        idx = re.findall(r'\[(\d+)\]', n[len(base(n)):])
        for k, v in enumerate(idx):
            dims[k] = max(dims.get(k, 0), int(v) + 1)
    return [dims[k] for k in sorted(dims)]

def extract(top, files):
    d = run_yosys(top, files)
    res = {'top': top, 'modules': {}}
    for mname, m in d['modules'].items():
        pub = {n: v for n, v in m['netnames'].items() if not v.get('hide_name', 1) and not n.startswith('$')}
        bit2name = {}
        for n, v in pub.items():
            for b in v['bits']:
                if isinstance(b, int):
                    bit2name.setdefault(b, []).append(n)
        driver = {}
        for cn, c in m['cells'].items():
            for p, dirn in c['port_directions'].items():
                if dirn == 'output':
                    for b in c['connections'][p]:
                        if isinstance(b, int):
                            driver[b] = (cn, c)
        port_in = {b for p, v in m['ports'].items() if v['direction'] == 'input' for b in v['bits'] if isinstance(b, int)}
        def fanin(bits, own, seen_cells, depth=0):
            out = set()
            for b in bits:
                if not isinstance(b, int):
                    continue
                names = [x for x in bit2name.get(b, []) if base(x) != own]
                if names:
                    out.update(base(x) for x in names)
                    continue
                if b in driver and depth < 40:
                    cn, c = driver[b]
                    if cn in seen_cells:
                        continue
                    seen_cells.add(cn)
                    for p, dirn in c['port_directions'].items():
                        if dirn == 'input':
                            out |= fanin(c['connections'][p], own, seen_cells, depth + 1)
            return out
        groups = {}
        for n in pub:
            groups.setdefault(base(n), []).append(n)
        signals = []
        for g, names in sorted(groups.items()):
            bits = [b for n in names for b in pub[n]['bits'] if isinstance(b, int)]
            width = len(pub[names[0]]['bits'])
            drivers = {driver[b][1]['type'] for b in bits if b in driver}
            if any(b in port_in for b in bits):
                kind = 'input'
            elif drivers & set(DFF):
                kind = 'register'
            elif any(not t.startswith('$') for t in drivers):
                kind = 'instance_output'
            elif drivers:
                kind = 'combinational'
            else:
                kind = 'undriven'
            dep = set()
            seen = set()
            for b in bits:
                if b in driver:
                    cn, c = driver[b]
                    if cn in seen:
                        continue
                    seen.add(cn)
                    for p, dirn in c['port_directions'].items():
                        if dirn == 'input':
                            dep |= fanin(c['connections'][p], g, seen)
            signals.append({'name': g, 'width': width, 'shape': shape_of(names), 'kind': kind, 'depends_on': sorted(dep)})
        regs = []
        for cn, c in m['cells'].items():
            if c['type'] in DFF:
                q = c['connections'].get('Q', [])
                nm = sorted({base(x) for b in q if isinstance(b, int) for x in bit2name.get(b, [])})
                clk = sorted({base(x) for b in c['connections'].get('CLK', []) if isinstance(b, int) for x in bit2name.get(b, [])})
                rst = sorted({base(x) for b in c['connections'].get('ARST', []) if isinstance(b, int) for x in bit2name.get(b, [])})
                regs.append({'cell': c['type'], 'signal': nm, 'width': int(c['parameters'].get('WIDTH', '0'), 2) if isinstance(c['parameters'].get('WIDTH'), str) else c['parameters'].get('WIDTH'), 'clock': clk, 'clock_edge': 'pos' if str(c['parameters'].get('CLK_POLARITY', '1'))[-1] == '1' else 'neg', 'async_reset': rst, 'reset_level': 'high' if str(c['parameters'].get('ARST_POLARITY', '1'))[-1] == '1' else 'low'})
        # collapse registers by signal name
        rc = {}
        for r in regs:
            key = (tuple(r['signal']), tuple(r['clock']), r['clock_edge'], tuple(r['async_reset']), r['reset_level'])
            e = rc.setdefault(key, {'signal': r['signal'], 'clock': r['clock'], 'clock_edge': r['clock_edge'], 'async_reset': r['async_reset'], 'reset_level': r['reset_level'], 'count': 0})
            e['count'] += 1
        insts = []
        for cn, c in m['cells'].items():
            if not c['type'].startswith('$'):
                conn = {}
                for p, bits in c['connections'].items():
                    nm = sorted({base(x) for b in bits if isinstance(b, int) for x in bit2name.get(b, [])})
                    conn[p] = {'dir': c['port_directions'].get(p), 'signals': nm}
                insts.append({'name': cn.lstrip('\\'), 'module': c['type'].lstrip('\\'), 'connections': conn})
        ports = [{'name': p, 'direction': v['direction'], 'width': len(v['bits'])} for p, v in m['ports'].items()]
        # collapse instances of the same module with the same connection signals (generate loops)
        ic = {}
        for i in insts:
            key = (i['module'], json.dumps(i['connections'], sort_keys=True))
            e = ic.setdefault(key, {'module': i['module'], 'connections': i['connections'], 'names': []})
            e['names'].append(i['name'])
        res['modules'][mname.lstrip('\\')] = {'ports': ports, 'registers': list(rc.values()), 'instances': [{'module': e['module'], 'count': len(e['names']), 'example_name': e['names'][0], 'connections': e['connections']} for e in ic.values()], 'signals': signals}
    return res

if __name__ == '__main__':
    json.dump(extract(sys.argv[1], sys.argv[2:]), sys.stdout, indent=1)
