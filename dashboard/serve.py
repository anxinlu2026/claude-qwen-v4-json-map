#!/usr/bin/env python3
"""Board of a work-order run: flow (conversations and work orders), decisions (what the model reported, what the orchestrator answered),
the model's ledger (assumptions and facts) and the tool activity. Reads the run directory; changes nothing. Standard library only.

usage: serve.py [--port 8765] [--runs DIR]      then open http://127.0.0.1:8765/?run=<run directory name>
The page refreshes itself every 10 s; each request re-reads the files.
"""
import argparse, datetime, glob, html, json, os, re, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.normpath(os.path.join(HERE, '..', 'runs'))


def read(p, n=None):
    try:
        t = open(p, errors='replace').read()
        return t if n is None else t[:n]
    except OSError:
        return ''


def jl(p):
    out = []
    for l in read(p).splitlines():
        try:
            out.append(json.loads(l))
        except ValueError:
            pass
    return out


def ts(s):
    try:
        return datetime.datetime.fromisoformat(s).timestamp()
    except ValueError:
        return 0.0


def clock(t):
    return datetime.datetime.fromtimestamp(t).strftime('%m-%d %H:%M:%S') if t else ''


def esc(s):
    return html.escape(str(s))


PLAN = os.path.normpath(os.path.join(HERE, '..', '01_plan', 'responsibility_table.md'))


def stage_plan():
    """Rows of the responsibility table: id, worker, work, skill, prerequisites."""
    out = []
    for l in read(PLAN).splitlines():
        m = re.match(r'^\|\s*(A\d\.\d)\s*\|(.*)$', l)
        if not m:
            continue
        c = [x.strip() for x in m.group(2).split('|')]
        if len(c) < 5:
            continue
        out.append({'id': m.group(1), 'worker': c[0], 'work': c[1], 'skill': c[3].strip('`'), 'deps': c[4]})
    return out


PREP = [('0.1', 'read the task text'), ('0.2', 'read the testbench'), ('0.3', 'run the testbench once'),
        ('0.4', 'find and validate the golden model'), ('0.5', 'classify the task, task sheet approved')]


def walk_board(d, run):
    """Board of the walk flow (orders 0.1-0.5, then the orders the architecture session writes): every order seen, plus the next one announced."""
    rows = []
    state = {o['id']: o for o in d['orders']}
    rnd = {}
    for e in d['olog']:
        if e.get('action') == 'round':
            rnd[str(e.get('order'))] = e.get('result')
        if e.get('action') == 'close':
            rnd.setdefault(str(e.get('order')), 'pass')
    def col(i):
        o = state.get(i); r = rnd.get(i)
        if r == 'pass': return 'Closed'
        if r == 'fail': return 'Not pass'
        if o: return {'Running': 'Running', 'Reported': 'Reported', 'Answered': 'Reported', 'Closed': 'Closed'}.get(o['col'], 'Running')
        return None
    seen = set()
    for i, goal in PREP:
        rows.append({'id': i, 'worker': 'HDL', 'skill': goal, 'col': col(i) or 'Backlog'}); seen.add(i)
    for o in d['orders']:
        if o['id'] in seen: continue
        seen.add(o['id'])
        rows.append({'id': o['id'], 'worker': 'HDL', 'skill': (o['type'] + ' ' + o['goal'])[:70], 'col': col(o['id']) or 'Running'})
    for e in reversed([e for e in d['olog'] if e.get('action') == 'round']):
        nx = str(e.get('next') or '')
        if nx and nx not in seen:
            rows.append({'id': nx, 'worker': 'architecture', 'skill': 'announced by the last round', 'col': 'Ready'}); break
    return rows


def stage_board(d, run):
    plan = stage_plan()
    ids = {r['id'] for r in plan}
    used = {o['id'] for o in d['orders']} | {str(e.get('order')) for e in d['olog']}
    if not (ids & used):
        return walk_board(d, run)
    state = {o['id']: o['col'] for o in d['orders']}
    for e in d['olog']:
        if e.get('action') == 'close':
            state[e.get('order')] = 'Closed'
    try:
        if json.load(open(os.path.join(run, 'control', 'a1_gate.json'))).get('gate') == 'pass':
            state['A1.6'] = 'Closed'
    except (OSError, ValueError):
        pass
    done = lambda i: state.get(i) in ('Closed', 'Answered')
    for r in plan:
        st = state.get(r['id'])
        if st in ('Closed', 'Answered'):
            r['col'] = 'Closed'
        elif st == 'Reported':
            r['col'] = 'Reported'
        elif st == 'Running':
            r['col'] = 'Running'
        elif st:
            r['col'] = st if st in ('Ended without report',) else 'Running'
        else:
            need = re.findall(r'A\d\.(?:\d|\*)', r['deps'])
            ok = True
            for t in need:
                if t.endswith('*'):
                    ok = ok and all(done(x['id']) for x in plan if x['id'].startswith(t[:-1]))
                else:
                    ok = ok and done(t)
            r['col'] = 'Ready' if ok else 'Backlog'
    return plan


def collect(run):
    ctl = os.path.join(run, 'control')
    log = read(os.path.join(run, 'console.log'))
    convs = {}
    for m in re.finditer(r'^\[(\S+)\] conversation (\d+) (start|end)(?:: (.*))?', log, re.M):
        t, n, kind, rest = ts(m.group(1)), int(m.group(2)), m.group(3), m.group(4) or ''
        c = convs.setdefault(n, {'n': n})
        if kind == 'start':
            c['start'] = t
        else:
            c['end'] = t; c['reason'] = rest
    for f in glob.glob(os.path.join(ctl, 'case_*.md')):
        n = int(re.search(r'case_(\d+)', f).group(1)); c = convs.setdefault(n, {'n': n})
        txt = read(f)
        orders = re.findall(r'^WORK ORDER ([\d.A-Z]+)(?: [—-]+ TYPE: ([A-Z -]+))?', txt, re.M)
        c['case_orders'] = ', '.join(o[0] for o in orders)
        c['type'] = next((o[1] for o in orders if o[1]), '') or (re.search(r'TYPE:\s*([A-Z][A-Z -]+[A-Z])', txt) or [None, ''])[1]
        g = re.search(r'^Goal:\s*(.*)', txt, re.M)
        c['goal'] = g.group(1).strip() if g else ''
        c['case_chars'] = len(txt)
    for n, c in convs.items():
        rs = read(os.path.join(ctl, f'conv_{n}_reasoning.md'))
        c['reasoning_chars'] = len(rs)
        d = read(os.path.join(ctl, f'conv_{n}.done'))
        try:
            c['done'] = json.loads(d)
        except ValueError:
            pass
    # decisions: reports (request) and orchestrator answers
    box = next(iter(glob.glob(os.path.join(run, 'work', '*', 'harness', '*', 'rundir', '.orchestrator'))), '')
    reqs = []
    for f in glob.glob(os.path.join(box, 'request_*.md')):
        k = os.path.basename(f)[len('request_'):-3]
        a = os.path.join(box, 'answer_' + k + '.md')
        reqs.append({'k': k, 't': os.path.getmtime(f), 'req': read(f), 'ans': read(a) if os.path.exists(a) else None,
                     'at': os.path.getmtime(a) if os.path.exists(a) else 0})
    reqs.sort(key=lambda r: r['t'])
    starts = sorted((c.get('start', 0), n) for n, c in convs.items() if c.get('start'))
    for r in reqs:
        r['conv'] = next((n for s, n in reversed(starts) if s <= r['t']), '')
    st = {}
    try:
        st = json.load(open(os.path.join(run, 'state', 'rtlwork', 'state.json')))
    except (OSError, ValueError):
        pass
    hist = [h for h in jl(os.path.join(run, 'state', 'rtlwork', 'history.jsonl')) if 'cmd' in h]
    try:
        live = json.load(open(os.path.join(ctl, 'live.json')))
    except (OSError, ValueError):
        live = {}
    proto = {}
    try:
        proto = json.load(open(os.path.join(run, 'protocol.json')))
    except (OSError, ValueError):
        pass
    deliv = sorted(glob.glob(os.path.join(run, 'state', 'deliveries', '*')))
    olog = jl(os.path.join(ctl, 'orchestrator_log.jsonl'))
    arch = sorted(glob.glob(os.path.join(ctl, 'architecture', '*')))
    # work-order board: each order id once, in the order issued; column from what has been seen of it
    orders = []
    seen = set()
    evs = []
    for f in glob.glob(os.path.join(ctl, 'case_*.md')):
        n = int(re.search(r'case_(\d+)', f).group(1))
        evs.append((convs.get(n, {}).get('start') or os.path.getmtime(f), 'issue', n, read(f)))
    for r in reqs:
        evs.append((r['t'], 'report', r['k'], r['req']))
        if r['ans'] is not None:
            evs.append((r['at'], 'answer', r['k'], r['ans']))
    evs.sort(key=lambda e: e[0])
    cur = None
    for t, kind, k, txt in evs:
        ms = list(re.finditer(r'^WORK ORDER ([0-9]+(?:\.[0-9]+)*|[A-Z][A-Z0-9]*(?:\.[0-9]+)+)(?:\s+[—-]+\s*TYPE:\s*([A-Z][A-Z -]+[A-Z]))?', txt, re.M)) if kind in ('issue', 'answer') else []
        if kind == 'report' and cur is not None:
            cur['col'] = 'Reported'; cur['report_t'] = t
        if kind == 'answer' and cur is not None and cur['col'] == 'Reported':
            cur['col'] = 'Answered'
        if ms and ms[0].group(1) not in seen:
            m0 = ms[0]; seen.add(m0.group(1))
            blk = txt[m0.start():]
            g = re.search(r'^Goal:\s*(.*)', blk, re.M)
            cur = {'id': m0.group(1), 'type': (m0.group(2) or '').strip(), 'goal': g.group(1).strip() if g else '', 'col': 'Running', 't': t}
            orders.append(cur)
    # an order is Closed when a later order exists or its conversation ended with a report answered
    for i, o in enumerate(orders):
        if i + 1 < len(orders) and o['col'] in ('Answered', 'Running'):
            o['col'] = 'Closed' if o['col'] == 'Answered' else 'Ended without report'
    for e in olog:
        for o in orders:
            if o['id'] == e.get('order') and e.get('action') == 'close':
                o['col'] = 'Closed'
    return {'orders': orders, 'olog': olog, 'arch': arch, 'convs': convs, 'reqs': reqs, 'state': st, 'hist': hist, 'live': live, 'proto': proto, 'deliv': deliv, 'log': log}



def flow_section(run):
    """Block-map flow (arch/hdl JSON exchange): one row per block from exchange/*.json, derived from the files; plus regression and the orchestrator's runlog."""
    ex = os.path.join(run, 'exchange')
    if not os.path.isdir(ex): return ''
    def lj(path):
        try: return json.load(open(path))
        except Exception: return None
    files = sorted(os.listdir(ex)); rounds = [int(m.group(1)) for f in files for m in [re.search(r'-v(\d+)\.json$', f)] if m]
    top = lj(os.path.join(ex, 'arch-top-model-v%d.json' % (max(r for r in rounds) if rounds else 0))) or lj(os.path.join(ex, 'arch-top-model-v0.json')) or {}
    h = ['<h2>Block map flow (arch ↔ hdl JSON)</h2>']
    hdl_n = sum(1 for f in files if f.startswith('hdl-blk'))
    h.append(f'<p class="meta">rounds seen: {sorted(set(rounds))} · hdl block files: {hdl_n} / {len(top.get("blocks", []))} · exchange files: {len(files)}</p>')
    rows = []
    for b in top.get('blocks', []):
        bid = b['id']; vs = sorted((int(m.group(1)) for f in files for m in [re.match(r'hdl-%s-rtl-v(\d+)\.json$' % bid, f)] if m))
        if not vs:
            rows.append(f'<tr><td>{esc(bid)}</td><td>{esc(b["name"])}</td><td colspan="9" style="color:#888">no hdl file yet</td></tr>'); continue
        v = vs[-1]; fp = os.path.join(ex, f'hdl-{bid}-rtl-v{v}.json'); d = lj(fp)
        if d is None:
            rows.append(f'<tr class="bad"><td>{esc(bid)}</td><td>{esc(b["name"])}</td><td>v{v}</td><td colspan="8">invalid JSON</td></tr>'); continue
        todo = open(fp).read().count('TODO'); hr = d.get('harness_result') or {}
        fc = hr.get('function_check') or {}; ic = hr.get('input_check') or {}
        fcs = f'{fc.get("match")}/{fc.get("rows")}' if fc else '—'; ics = f'{ic.get("match")}/{ic.get("rows")}' if ic else '—'
        bad = (fc.get('mismatch') or 0) > 0 or (ic.get('mismatch') or 0) > 0
        conf = (d.get('confidence') or {}).get('level', '—'); dif = (d.get('difficulty') or {}).get('level', '—'); ctl = (d.get('control') or {}).get('assessment', '—')
        rows.append(f'<tr class="{"bad" if bad else ""}"><td>{esc(bid)}</td><td>{esc(b["name"])}</td><td>v{v}</td><td>{"TODO×%d" % todo if todo else "ok"}</td><td>{esc(fcs)}</td><td>{esc(ics)}</td>'
                    f'<td>{esc(conf)}</td><td>{esc(dif)}</td><td>{esc(ctl)}</td><td>{esc(d.get("status", "—"))}</td>'
                    f'<td>q{len(d.get("questions") or [])} h{len(d.get("assumptions") or [])} c{len(d.get("rtl_changes") or [])}</td></tr>')
    h.append('<table><tr><th>blk</th><th>block</th><th>hdl ver</th><th>TODO</th><th>function check (match/rows)</th><th>input check (match/steps)</th><th>confidence</th><th>difficulty</th><th>control</th><th>status</th><th>questions / assumptions / changes</th></tr>' + ''.join(rows) + '</table>')
    ht = sorted(f for f in files if f.startswith('hdl-top-rtl'))
    h.append(f'<p class="meta">hdl top file: {esc(", ".join(ht) or "not yet")}</p>')
    regs = sorted(f for f in files if f.startswith('tool-top-regression'))
    for f in regs[-3:]:
        r = lj(os.path.join(ex, f)) or {}; tb = r.get('testbench', {}); of = r.get('official_harness', {})
        h.append(f'<p class="meta">{esc(f)}: testbench <b>{esc(tb.get("result"))}</b> ({esc(tb.get("fail"))} FAIL, {esc(tb.get("pass"))} PASS) · observed {esc(tb.get("observed"))} · official {esc(of.get("result"))}</p>')
    recent = sorted(((os.path.getmtime(os.path.join(ex, f)), f) for f in files if not f.startswith('arch-') and f != 'README_HDL.md'), reverse=True)[:6]
    if recent: h.append('<p class="meta">latest changes: ' + ' · '.join(f'{esc(f)} ({clock(t)})' for t, f in recent) + '</p>')
    # modification list: the HDL engineer's records (latest version of each block) and the list generated from the difference
    ch = []
    for b in top.get('blocks', []):
        vs = sorted((int(m.group(1)) for f in files for m in [re.match(r'hdl-%s-rtl-v(\d+)\.json$' % b['id'], f)] if m))
        d = lj(os.path.join(ex, f'hdl-{b["id"]}-rtl-v{vs[-1]}.json')) if vs else None
        for c_ in (d or {}).get('rtl_changes') or []:
            ch.append(f'<tr><td>{esc(b["id"])}</td><td>{esc(c_.get("id"))}</td><td>{esc(c_.get("file"))}</td><td>{esc(c_.get("lines"))}</td><td>{esc(c_.get("status"))}</td><td>{esc(c_.get("based_on"))}</td><td>{esc(str(c_.get("reason", ""))[:110])}</td></tr>')
    if ch: h.append('<details><summary>RTL changes recorded by the HDL engineer (%d)</summary><table><tr><th>blk</th><th>id</th><th>file</th><th>lines</th><th>status</th><th>based on</th><th>reason</th></tr>%s</table></details>' % (len(ch), ''.join(ch)))
    for f in sorted(x for x in files if x.startswith('tool-top-changes'))[-1:]:
        t = lj(os.path.join(ex, f)) or {}; rc = t.get('reconciliation', {})
        if rc: h.append(f'<p class="meta">{esc(f)} (generated from the difference): regions {esc(rc.get("regions"))} · records {esc(rc.get("records"))} · distinct record locations {esc(rc.get("distinct_record_locations(file,lines)"))} · records matching no region {esc(rc.get("records_matching_no_region"))} · regions without a record {esc(rc.get("regions_without_record"))} · repeated: {esc(rc.get("records_repeating_a_place"))}</p>')
    # tool usage: rtl commands from the rtl history, flow tools from the usage log
    hist = os.path.join(run, 'state', 'rtlwork', 'history.jsonl'); rc_ = {}
    if os.path.exists(hist):
        for l in open(hist):
            try: c0 = (json.loads(l).get('cmd') or '').split(' ')[0]
            except Exception: continue
            if c0: rc_[c0] = rc_.get(c0, 0) + 1
    fl = {}; ulog = os.path.join(ex, 'usage-log.jsonl')
    if os.path.exists(ulog):
        for l in open(ulog):
            try: t_ = json.loads(l)
            except Exception: continue
            k_ = f'{t_.get("actor")}:{t_.get("tool")}'; fl[k_] = fl.get(k_, 0) + 1
    if rc_ or fl:
        h.append('<p class="meta">tool use · rtl: ' + esc(', '.join(f'{k} {v}' for k, v in sorted(rc_.items(), key=lambda x: -x[1])[:10])) + ' · flow tools: ' + esc(', '.join(f'{k} {v}' for k, v in sorted(fl.items(), key=lambda x: -x[1])) or 'none logged') + '</p>')
    # requests waiting for an answer (read from the worker's request files)
    box = next(iter(glob.glob(os.path.join(run, 'work', '*', 'harness', '*', 'rundir', '.orchestrator'))), '')
    pend = [os.path.basename(f) for f in sorted(glob.glob(os.path.join(box, 'request_*.md'))) if not os.path.exists(f.replace('request_', 'answer_'))]
    h.append(f'<p class="meta">requests waiting for an answer: <b>{esc(", ".join(pend) or "none")}</b></p>' if not pend else f'<div class="box wait"><b>Requests waiting for an answer:</b> {esc(", ".join(pend))}</div>')
    rl = os.path.join(run, 'runlog.md')
    if os.path.exists(rl): h.append('<details><summary>runlog.md (problems and dynamic fixes)</summary><pre>' + esc(read(rl)) + '</pre></details>')
    return '\n'.join(h)


def render(run):
    d = collect(run)
    name = os.path.basename(run)
    p = d['proto']; ses = (p.get('work_orders') or {}).get('sessions') or [{}]
    now = datetime.datetime.now().timestamp()
    convs = d['convs']
    last = max(convs) if convs else None
    cur = convs.get(last, {}) if last is not None else {}
    running = last is not None and 'end' not in cur
    h = []
    h.append(f'<h1>{esc(name)}</h1>')
    h.append(f'<p class="meta">model <b>{esc(p.get("model", ""))}</b> · kickoff {esc(os.path.basename(str((ses[-1] or {}).get("kickoff_file", ""))))} · '
             f'effort {esc((ses[-1] or {}).get("reasoning_effort", ""))} · conversations {len(convs)} · reports {len(d["reqs"])} · tool calls {len(d["hist"])} · refreshed {clock(now)}</p>')
    fl = flow_section(run)
    if fl: h.append(fl)
    # status
    if last is None and fl:
        pass
    elif last is None:
        h.append('<div class="box wait">Waiting for the first work order (no <code>control/case_0.md</code> yet).</div>')
    elif running:
        el = int(now - cur.get('start', now))
        pend = [r for r in d['reqs'] if r['ans'] is None]
        h.append(f'<div class="box run">Conversation {last} running {el} s · type {esc(cur.get("type", ""))} · goal: {esc(cur.get("goal", ""))}'
                 + (f'<br><b>A report is waiting for an answer</b> (request {esc(pend[-1]["k"])}, {int(now - pend[-1]["t"])} s)' if pend else '') + '</div>')
        lv = d['live']
        if lv:
            h.append(f'<p class="meta">reasoning {lv.get("reasoning_chars", "")} chars · loop phrases {lv.get("loop_phrases", "")} · {esc(lv.get("signs", ""))}</p>')
    else:
        h.append(f'<div class="box idle">Idle: conversation {last} ended ({esc(cur.get("reason", ""))}). The next work order is the orchestrator\'s turn.</div>')
    # stage board: every order of the plan, by state
    sb = None if fl else stage_board(d, run)
    if sb:
        h.append('<h2>Stage board (A1–A6)</h2><div class="kan sb">')
        for c in ('Backlog', 'Ready', 'Running', 'Reported', 'Not pass', 'Ended without report', 'Closed'):
            items = [r for r in sb if r['col'] == c]
            h.append(f'<div class="col"><h3>{esc(c)} ({len(items)})</h3><div class="scroll">' + ''.join(
                f'<div class="card"><b>{esc(r["id"])}</b> <span class="who who-{esc(r["worker"])}">{esc(r["worker"])}</span><br>{esc(r["skill"])}</div>' for r in items) + '</div></div>')
        h.append('</div>')
    # work-order board (kanban)
    cols = ['Running', 'Reported', 'Answered', 'Closed', 'Ended without report']
    h.append('<h2>Work orders</h2><div class="kan">')
    for c in cols:
        items = [o for o in d['orders'] if o['col'] == c]
        h.append(f'<div class="col"><h3>{esc(c)} ({len(items)})</h3>' + ''.join(
            f'<div class="card"><b>{esc(o["id"])}</b> {esc(o["type"])}<br>{esc(o["goal"])[:90]}</div>' for o in items[-12:]) + '</div>')
    h.append('</div>')
    # rounds (one line per finished order; written by `orch.py round` before the next round starts)
    rounds = [e for e in d['olog'] if e.get('action') == 'round']
    if rounds:
        h.append(f'<h2>Rounds ({len(rounds)})</h2><table><tr><th>time</th><th>order</th><th>result</th><th>fails in a row</th><th>authorization</th><th>next</th><th>reason</th></tr>')
        for e in reversed(rounds[-30:]):
            r = e.get('result', '')
            h.append(f'<tr class="rnd-{esc(r)}"><td>{clock(e.get("t", 0))}</td><td>{esc(e.get("order", ""))}</td><td><b>{esc(r)}</b></td>'
                     f'<td>{esc(e.get("fails", ""))}</td><td>{esc(e.get("auth", ""))}</td><td>{esc(e.get("next", ""))}</td><td>{esc(e.get("text", ""))}</td></tr>')
        h.append('</table>')
    # orchestrator log
    h.append(f'<h2>Orchestrator log ({len(d["olog"])})</h2><table><tr><th>time</th><th>role</th><th>action</th><th>order</th><th>text</th></tr>')
    for e in reversed(d['olog'][-60:]):
        h.append(f'<tr class="act-{esc(e.get("action", ""))}"><td>{clock(e.get("t", 0))}</td><td>{esc(e.get("role", ""))}</td><td><b>{esc(e.get("action", ""))}</b></td>'
                 f'<td>{esc(e.get("order", ""))}</td><td>{esc(e.get("text", ""))}</td></tr>')
    h.append('</table>')
    if d['arch']:
        h.append('<h2>Architecture session files</h2><ul>' + ''.join(
            f'<li>{esc(os.path.relpath(x, run))} ({os.path.getsize(x)} bytes, {clock(os.path.getmtime(x))})</li>' for x in d['arch']) + '</ul>')
    # flow
    h.append('<h2>Flow: conversations</h2><table><tr><th>#</th><th>work orders</th><th>type</th><th>goal</th><th>start</th><th>s</th><th>end</th><th>reasoning</th><th>reports</th></tr>')
    for n in sorted(convs):
        c = convs[n]; secs = int(c.get('end', now) - c['start']) if c.get('start') else ''
        rep = sum(1 for r in d['reqs'] if r['conv'] == n)
        reason = c.get('reason', 'running' if 'start' in c else '')
        cls = 'ok' if reason.startswith('ended') else ('bad' if 'exceeded' in reason else ('run' if reason == 'running' else ''))
        h.append(f'<tr class="{cls}"><td>{n}</td><td>{esc(c.get("case_orders", ""))}</td><td>{esc(c.get("type", ""))}</td><td>{esc(c.get("goal", ""))[:110]}</td>'
                 f'<td>{clock(c.get("start", 0))}</td><td>{secs}</td><td>{esc(reason)}</td><td>{c.get("reasoning_chars", "")}</td><td>{rep}</td></tr>')
    h.append('</table>')
    # decisions
    h.append('<h2>Decisions: report → answer</h2>')
    for r in reversed(d['reqs'][-40:]):
        rep = r['req'].split('## Report', 1)[-1].strip()
        ans = (r['ans'] or '').strip()
        h.append(f'<details {"open" if r["ans"] is None else ""}><summary>conv {r["conv"]} · request {esc(r["k"])} · {clock(r["t"])}'
                 + (f' → answered {clock(r["at"])} (+{int(r["at"] - r["t"])} s)' if r['ans'] else ' → <b>no answer yet</b>') + '</summary>'
                 f'<div class="two"><div><h4>model report</h4><pre>{esc(rep[:2500])}</pre></div><div><h4>orchestrator answer / next work order</h4><pre>{esc(ans[:2500])}</pre></div></div></details>')
    # architecture ledger (markdown written by the architecture session: facts, assumptions, decisions)
    lg = read(os.path.join(run, 'control', 'architecture', 'ledger.md'))
    if lg:
        h.append(f'<h2>Architecture ledger <span class="meta">(control/architecture/ledger.md, {clock(os.path.getmtime(os.path.join(run, "control", "architecture", "ledger.md")))})</span></h2><div class="lg">')
        for line in lg.splitlines():
            e = esc(line)
            cls = ''
            if re.match(r'^\s*-?\s*A\d+\b|^\s*-?\s*B\d+\b', line):
                cls = 'st-proven' if re.search(r'PROVEN|FIXED', line.split('   ')[0]) else ('st-struck' if 'STRUCK' in line.split('   ')[0] else ('st-open' if re.search(r'OPEN|BLOCKED', line.split('   ')[0]) else ''))
            if line.startswith('#'):
                h.append(f'<h3>{e.lstrip("# ")}</h3>')
            elif line.strip():
                h.append(f'<div class="lgl {cls}">{e}</div>')
        h.append('</div>')
    # ledger
    st = d['state']
    asm = st.get('assumptions', [])
    h.append(f'<h2>Ledger ({len(asm)})</h2><table><tr><th>id</th><th>kind</th><th>status</th><th>claim</th><th>evidence</th><th>order</th></tr>')
    for a in asm:
        s = a.get('status', '')
        h.append(f'<tr class="st-{esc(s.replace(" ", "-"))}"><td>{esc(a.get("id", ""))}</td><td>{esc(a.get("kind", ""))}</td><td>{esc(s)}</td>'
                 f'<td>{esc(a.get("object", ""))}</td><td>{esc(str(a.get("evidence", ""))[:300])}</td><td>{esc(a.get("order", ""))}</td></tr>')
    h.append('</table>')
    # state counters
    runs = [x for x in st.get('runs', []) if not x.get('probe')]
    h.append(f'<p class="meta">testbench runs {len(runs)}'
             + (f' · last run #{runs[-1].get("n")}: {esc(runs[-1].get("result", ""))}' if runs else '') +
             f' · task sheet {"approved" if st.get("sheet_approved") else "not approved"} · model {"validated" if st.get("model") else "not validated"}'
             f' · edits {len(st.get("ckpts", []))} checkpoints</p>')
    # deliveries
    if d['deliv']:
        h.append('<h2>Deliveries</h2><ul>' + ''.join(f'<li>{esc(os.path.relpath(x, run))} ({os.path.getsize(x)} bytes, {clock(os.path.getmtime(x))})</li>' for x in d['deliv']) + '</ul>')
    # tool activity
    cnt = {}
    for x in d['hist']:
        c0 = x['cmd'].split()[0] if x['cmd'].split() else '?'
        cnt[c0] = cnt.get(c0, 0) + 1
    h.append('<h2>Tool activity</h2><p>' + ' · '.join(f'<b>{esc(k)}</b> {v}' for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])) + '</p>')
    h.append('<table><tr><th>time</th><th>command</th><th>result (first line)</th></tr>')
    for x in reversed(d['hist'][-15:]):
        h.append(f'<tr><td>{clock(x.get("t", 0))}</td><td><code>{esc(x["cmd"])[:120]}</code></td><td>{esc((x.get("out") or "").splitlines()[0][:160] if x.get("out") else "")}</td></tr>')
    h.append('</table>')
    return '\n'.join(h)


CSS = """body{font:14px/1.45 -apple-system,Segoe UI,sans-serif;margin:16px;max-width:1300px;background:#fff;color:#1c1c1c}
h1{font-size:18px;margin:0 0 4px}h2{font-size:15px;margin:22px 0 6px;border-bottom:1px solid #ddd;padding-bottom:3px}h4{margin:4px 0;font-size:12px;color:#666}
.meta{color:#666;margin:2px 0 10px}table{border-collapse:collapse;width:100%;font-size:12.5px}td,th{border:1px solid #ddd;padding:3px 6px;text-align:left;vertical-align:top}
th{background:#f4f4f4}tr.ok td:nth-child(7){color:#0a7a3b}tr.bad{background:#fdecea}tr.run{background:#eef6ff}
.box{padding:10px 12px;border-radius:6px;margin:8px 0}.run{background:#e8f1ff}.idle{background:#f3f3f3}.wait{background:#fff7e0}
details{border:1px solid #ddd;border-radius:6px;margin:6px 0;padding:4px 8px}summary{cursor:pointer}.two{display:grid;grid-template-columns:1fr 1fr;gap:10px}
pre{white-space:pre-wrap;word-break:break-word;background:#fafafa;padding:6px;border-radius:4px;max-height:360px;overflow:auto;font-size:12px}
tr.st-proven td:nth-child(3){color:#0a7a3b;font-weight:600}tr.st-struck-out td:nth-child(3){color:#b00020}tr.st-open td:nth-child(3){color:#a15c00}
tr.rnd-pass td:nth-child(3){color:#0a7a3b}tr.rnd-fail td:nth-child(3){color:#b00020}
code{font-size:12px}.lg{font-size:12.5px}.lgl{padding:2px 6px;border-left:3px solid #ddd;margin:2px 0}.lgl.st-proven{border-color:#0a7a3b}.lgl.st-struck{border-color:#b00020}.lgl.st-open{border-color:#a15c00}.kan{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}.kan.sb{grid-template-columns:repeat(7,1fr)}.scroll{max-height:340px;overflow:auto}.who{font-size:10px;padding:0 5px;border-radius:8px;background:#e8e8e8}.who-HDL{background:#d9ecff}.who-architecture{background:#e6f7e0}.who-orchestrator{background:#fff0c9}.col{background:#f6f6f6;border-radius:6px;padding:6px}
.col h3{font-size:12px;margin:0 0 6px}.card{background:#fff;border:1px solid #ddd;border-radius:4px;padding:4px 6px;margin:4px 0;font-size:12px}
tr.act-close td:nth-child(3){color:#0a7a3b}tr.act-issue td:nth-child(3){color:#0b57d0}tr.act-decide td:nth-child(3){color:#a15c00}tr.act-stop td:nth-child(3){color:#b00020}
code{font-size:12px}@media (max-width:900px){.kan{grid-template-columns:1fr 1fr}.two{grid-template-columns:1fr}}
@media (prefers-color-scheme:dark){.col{background:#222}.card{background:#1b1b1b;border-color:#444}body{background:#161616;color:#e6e6e6}th{background:#262626}td,th,details{border-color:#444}pre{background:#202020}
.run{background:#16314f}.idle{background:#262626}.wait{background:#40351a}tr.bad{background:#40201d}tr.run{background:#16314f}}"""


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        runs = sorted(glob.glob(os.path.join(RUNS, 'orders-*')), key=os.path.getmtime)
        want = (q.get('run') or [''])[0]
        run = next((r for r in runs if os.path.basename(r) == want), runs[-1] if runs else '')
        opts = ''.join(f'<option value="{esc(os.path.basename(r))}"{" selected" if r == run else ""}>{esc(os.path.basename(r))}</option>' for r in reversed(runs))
        body = render(run) if run else '<p>No run directory under ' + esc(RUNS) + '</p>'
        page = (f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<meta http-equiv="refresh" content="10"><title>Run board</title><style>{CSS}</style>'
                f'<form><select name="run" onchange="this.form.submit()">{opts}</select></form>{body}')
        b = page.encode()
        self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.send_header('Content-Length', str(len(b))); self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=8765); ap.add_argument('--runs', default=None)
    a = ap.parse_args()
    if a.runs:
        RUNS = os.path.abspath(a.runs)
    print(f'board: http://127.0.0.1:{a.port}/  runs: {RUNS}', flush=True)
    HTTPServer(('127.0.0.1', a.port), H).serve_forever()
