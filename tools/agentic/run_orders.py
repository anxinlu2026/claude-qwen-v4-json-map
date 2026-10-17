"""Run one CVDP agentic problem in work-order mode: the orchestrator plans, the agent (Qwen Code) executes.

The agent container stays up for the whole problem. The work is done in conversations; each conversation is one
headless Qwen Code session that starts from a case file written by the orchestrator (control/case_N.md) and ends
when the orchestrator answers a report with "CONVERSATION COMPLETE", or when a work order exceeds its time limit.
Inside a conversation the agent reports with `rtl next` and gets the next work order as the answer
(<workspace>/rundir/.orchestrator/request_next_K.md -> answer_next_K.md).

Files the orchestrator uses, in <RUN>/control:
  case_N.md        written by the orchestrator: starts conversation N
  conv_N.done      written here when conversation N has ended (JSON: seconds, reason, exit code)
  finish           written by the orchestrator: this session of the run ends (the model is unloaded)

The work can be paused and taken up again. Everything the agent's tools keep (state of the rtl tool, task
sheet, models built, checkpoints) lives in <RUN>/state on the host, mounted at /tmp in the container, and the
design files are in the run's workspace. So after a stop - by `finish`, by killing this program, or after the
container is gone - `--resume RUN` continues with the next conversation, also with a newer image. The
container is left running when this program ends; `--close RUN` removes it.

Usage: python run_orders.py <label> --from-run RUN [--pos 1] --tag TAG --image IMAGE --kickoff FILE
                            [--temperature 0.6] [--order-timeout 600] [--timeout 0]
       python run_orders.py <label> --resume RUN [--image IMAGE] [--kickoff FILE] ...
       python run_orders.py <label> --close RUN
Tuning runs only; the result is graded separately with grade_partial.py and is not comparable with baselines.
"""
from pathlib import Path
import argparse, base64, collections, datetime, json, os, re, shutil, subprocess, sys, time, urllib.request

ROOT = Path(__file__).resolve().parents[2]
MODELS = {'qwen-qc': 'qwen3.8:27b-nvfp4', 'qwen8-qc': 'qwen3.8:27b-mxfp8', 'gemma-qc': 'gemma4:26b', 'coder-qc': '/Users/anxin/AI/models/mlx/Qwen3-Coder-30B-A3B-Instruct-8bit'}


def sh(*a, **kw):
    return subprocess.run(list(a), capture_output=True, text=True, **kw)


def log(run, msg):
    line = f'[{datetime.datetime.now().astimezone().isoformat(timespec="seconds")}] {msg}'
    print(line, flush=True)
    with open(run / 'console.log', 'a') as f:
        f.write(line + '\n')


def digest_block(state, control, ctext):
    """What the tool already has on record, copied from its state files: no reading of the design, no judgement.
    Appended after the case file so that the agent does not have to rebuild it by reading (2026-10-11)."""
    try:
        st = json.loads((state / 'rtlwork' / 'state.json').read_text())
    except Exception:
        return ''
    out = ['', '===== What the tool has on record (copied from its state files; not a judgement, not read from the design) =====']
    runs = [x for x in st.get('runs', []) if not x.get('probe')]
    if runs:
        out.append(f'Last testbench run: #{runs[-1]["n"]}: {runs[-1].get("result", "")}')
    ck = st.get('ckpts')
    out.append(f'Simulator runs so far: {len(st.get("runs", []))}; checkpoints: {len(ck) if hasattr(ck, "__len__") else ck}.')
    led = st.get('assumptions', [])
    for kind, title in (('assumption', 'Your assumptions on record (object, status, evidence; change with rtl assumption set):'),
                        ('fact', 'Facts you measured (established; use them, do not measure them again; change with rtl assumption set):')):
        rows = [a for a in led if a.get('kind', 'assumption') == kind]
        if rows:
            out.append(title)
            for a in rows:
                out.append(f'  {a["id"]} [{a["status"]}] {a["object"]}' + (f' | evidence: {a.get("evidence", "")[:260]}' if a.get('evidence') else ''))
    marks = st.get('marks', {})
    if marks:
        out.append('Recorded comparisons (signal: status, edits, what was recorded):')
        for k, v in marks.items():
            out.append(f'  {k}: {v.get("status")} (edits {v.get("attempts", 0)}) {(v.get("note") or "")[:170]}')
    ok, seen = [], set()
    hp = state / 'rtlwork' / 'history.jsonl'
    if hp.exists():
        for ln in hp.read_text(errors='replace').splitlines():
            try:
                h = json.loads(ln)
            except Exception:
                continue
            c = h.get('cmd', '')
            if re.match(r'(probe|blockcheck)\b', c) and not h.get('out', '').startswith('PROBE ERROR') and c not in seen:
                seen.add(c); ok.append(c)
    if ok:
        out.append('Probe / blockcheck commands the tool accepted (most recent last; names as written):')
        for c in ok[-8:]:
            out.append('  rtl ' + c[:200])
    lp = control / 'lessons.md'
    if lp.exists() and 'YOUR OWN RULES' not in ctext:
        out.append('Your own lessons (control/lessons.md):')
        out.append(lp.read_text(errors='replace').strip()[:2500])
    return '\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('label', choices=sorted(MODELS))
    ap.add_argument('--from-run', help='a prepared agentic run to take the problem files from')
    ap.add_argument('--resume', help='an existing work-order run to continue')
    ap.add_argument('--close', help='an existing work-order run whose container is to be removed')
    ap.add_argument('--pos', type=int, default=1, help='position of the problem in that run (1-based)')
    ap.add_argument('--tag')
    ap.add_argument('--image')
    ap.add_argument('--kickoff', help='instructions placed before every case file')
    ap.add_argument('--temperature', type=float, default=None)
    ap.add_argument('--reasoning-effort', default=None, help='thinking level for every request, e.g. low')
    ap.add_argument('--presence-penalty', type=float, default=None)
    ap.add_argument('--frequency-penalty', type=float, default=None)
    ap.add_argument('--repeat-penalty', type=float, default=None)
    ap.add_argument('--order-timeout', type=int, default=480, help='seconds after which a work order without a report ends its conversation')
    ap.add_argument('--order-soft', type=int, default=360, help='seconds after which the tool accepts only rtl next and rtl ask')
    ap.add_argument('--request-timeout', type=int, default=3600)
    ap.add_argument('--base-url', default=None, help='OpenAI-compatible endpoint of the agent as seen from the container (default: the local Ollama); e.g. http://host.docker.internal:18081/v1')
    ap.add_argument('--api-key-file', default=None, help='file that holds the key of that endpoint; it is read here and passed to the container through the environment, never as an argument')
    ap.add_argument('--qwen-context', type=int, default=None, help='context window Qwen Code is told (its own compaction triggers at a share of it)')
    ap.add_argument('--served-model', default=None, help='model name sent to the endpoint (default: the Ollama tag of the label)')
    ap.add_argument('--digest', choices=('on', 'off'), default='on', help='append the tool\'s own records (recorded comparisons, accepted probe commands, lessons) after the case file at the start of each conversation')
    ap.add_argument('--dev-mount', action='store_true', help='mount the tool, the skills and the resources from this checkout into the container (no image rebuild needed to change them); for walk-through runs')
    ap.add_argument('--loop-limit', type=int, default=3, help='ignored since 2026-10-11 evening (the signs are only recorded in control/live.json; they no longer end a conversation)')
    ap.add_argument('--timeout', type=int, default=0, help='seconds for this session of the run (0 = no limit)')
    a = ap.parse_args()

    old = a.resume or a.close
    if old:
        run = Path(old).resolve()
        proto = json.loads((run / 'protocol.json').read_text())
        wo = proto['work_orders']
        pid = proto['problems'][0]
        name = wo['container']
        if a.close:
            print(sh('docker', 'rm', '-f', name).stdout.strip() or 'no container'); return
        a.image = a.image or proto['agent_image']; a.kickoff = a.kickoff or wo['kickoff_file']
        if a.temperature is None:
            a.temperature = wo.get('temperature')
    else:
        if not (a.from_run and a.tag and a.image and a.kickoff):
            sys.exit('a new run needs --from-run, --tag, --image and --kickoff')
        src = Path(a.from_run).resolve()
        proto = json.loads((src / 'protocol.json').read_text())
        pid = proto['problems'][a.pos - 1]
        name = 'orders_' + re.sub(r'[^a-zA-Z0-9_.-]', '_', a.tag)
        run = ROOT / 'runs' / f'orders-{pid}-{a.label}-{a.tag}-{datetime.date.today():%Y%m%d}'
        if run.exists():
            sys.exit(f'{run} exists already (use --resume)')
    base, num = re.match(r'(.*)_(\d+)$', pid).groups()
    num = str(int(num))
    ws = run / 'work' / base / 'harness' / num
    agent_log = run / 'work' / base / 'reports' / f'{num}_agent.txt'
    control = run / 'control'; box = ws / 'rundir' / '.orchestrator'; state = run / 'state'
    model = MODELS[a.label]
    if not old:
        sh_src = src / 'work' / base / 'harness' / num
        ws.mkdir(parents=True)
        for d in ('docs', 'rtl', 'verif'):                      # untouched problem files
            shutil.copytree(sh_src / 'before' / d, ws / d)
        (ws / 'rundir').mkdir()
        shutil.copytree(sh_src / 'before', ws / 'before')
        shutil.copy2(sh_src / 'prompt.json', ws / 'prompt.json')
        shutil.copytree(sh_src / 'src', ws / 'src')              # hidden tests: for grading only, never mounted
        if (sh_src / 'docker-compose.yml').exists():
            shutil.copy2(sh_src / 'docker-compose.yml', ws / 'docker-compose.yml')
        agent_log.parent.mkdir(parents=True); control.mkdir(); box.mkdir(); state.mkdir()
        proto.update({'run_id': run.name, 'label': a.label, 'problems': [pid], 'mode': 'work orders',
                      'work_orders': {'container': name, 'source_run': src.name},
                      'note': 'tuning run: the orchestrator plans every work order; not comparable with baselines'})
    state.chmod(0o1777)
    proto['agent_image'] = a.image
    proto['work_orders'].update({'kickoff_file': a.kickoff, 'order_timeout_s': a.order_timeout, 'temperature': a.temperature})
    proto['work_orders'].setdefault('sessions', []).append({'started': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
                                                            'image': a.image, 'kickoff_file': a.kickoff, 'model': model})
    (run / 'protocol.json').write_text(json.dumps(proto, indent=1))
    (run / 'finished.json').unlink(missing_ok=True); (control / 'finish').unlink(missing_ok=True)
    kick = Path(a.kickoff).read_text()
    api_key = 'ollama'
    if a.api_key_file:
        api_key = Path(a.api_key_file).read_text().strip()
    env = {'QWEN_MODEL': a.served_model or model, 'OPENAI_BASE_URL': a.base_url or 'http://host.docker.internal:11434/v1', 'OPENAI_API_KEY': api_key,
           'QWEN_REQUEST_TIMEOUT_MS': str(a.request_timeout * 1000), 'QWEN_STREAM_MAX_LIFETIME_MS': str(a.request_timeout * 1000),
           'RTL_ORDER_LIMIT_S': str(a.order_timeout), 'RTL_ORDER_SOFT_S': str(a.order_soft)}
    if a.temperature is not None:
        env['QWEN_TEMPERATURE'] = str(a.temperature)
    if a.reasoning_effort:
        env['QWEN_REASONING_EFFORT'] = a.reasoning_effort
    if a.qwen_context:
        env['QWEN_CONTEXT_WINDOW'] = str(a.qwen_context)
    for var, val in (('QWEN_PRESENCE_PENALTY', a.presence_penalty), ('QWEN_FREQUENCY_PENALTY', a.frequency_penalty), ('QWEN_REPEAT_PENALTY', a.repeat_penalty)):
        if val is not None:
            env[var] = str(val)
    proto['work_orders'].setdefault('sessions', [{}])[-1].update({'temperature': a.temperature, 'presence_penalty': a.presence_penalty, 'frequency_penalty': a.frequency_penalty, 'repeat_penalty': a.repeat_penalty, 'reasoning_effort': a.reasoning_effort})
    (run / 'protocol.json').write_text(json.dumps(proto, indent=1))
    import hashlib
    env_fp = hashlib.sha1(json.dumps({k: v for k, v in sorted(env.items()) if k != 'OPENAI_API_KEY'}, sort_keys=True).encode()).hexdigest()[:16]
    dev = a.dev_mount or proto['work_orders'].get('dev_mount', False)
    proto['work_orders']['dev_mount'] = dev
    (run / 'protocol.json').write_text(json.dumps(proto, indent=1))
    cur = sh('docker', 'inspect', '-f', '{{.Config.Image}} {{.State.Running}}', name).stdout.split()
    has_dev = '/opt/skills' in sh('docker', 'inspect', '-f', '{{range .Mounts}}{{.Destination}} {{end}}', name).stdout
    cur_fp = sh('docker', 'inspect', '-f', '{{index .Config.Labels "rtl.env"}}', name).stdout.strip()
    if cur != [a.image, 'true'] or has_dev != dev or cur_fp != env_fp:   # a container keeps the environment it was created with                 # no container, a stopped one, or one of another image: start afresh on the kept state
        sh('docker', 'rm', '-f', name)
        cmd = ['docker', 'run', '-d', '--name', name, '--label', f'rtl.env={env_fp}', '-w', '/code', '-v', f'{state}:/tmp']
        for d in ('docs', 'rtl', 'verif', 'rundir'):
            cmd += ['-v', f'{ws / d}:/code/{d}']
        cmd += ['-v', f'{ws / "prompt.json"}:/code/prompt.json']
        if dev:   # live files of this checkout instead of the copies baked into the image
            for src_, dst_ in ((ROOT / 'tools' / 'rtl' / 'rtl', '/usr/local/bin/rtl'), (ROOT / 'tools' / 'agentic' / 'agent_qwen.py', '/app/agent_qwen.py'),
                               (ROOT / 'skills', '/opt/skills'), (ROOT / 'resources', '/opt/resources')):
                cmd += ['-v', f'{src_}:{dst_}:ro']
        for k, v in env.items():
            cmd += ['-e', k if k == 'OPENAI_API_KEY' else f'{k}={v}']   # the key goes by name; its value comes from the environment of this process
        cmd += ['--entrypoint', 'sleep', a.image, 'infinity']
        r = sh(*cmd, env={**os.environ, 'OPENAI_API_KEY': api_key})
        if r.returncode:
            sys.exit('container did not start: ' + r.stderr)
    done = [int(re.search(r'conv_(\d+)', f.name).group(1)) for f in control.glob('conv_*.done')]
    n = max(done) + 1 if done else 0
    for q in box.glob('request_*.md'):           # a report left unanswered by an interrupted conversation is closed
        ans = box / q.name.replace('request_', 'answer_')
        if not ans.exists():
            ans.write_text('(closed: the conversation that sent this was ended)\n')
    log(run, f'work-order session start {run.name}; container {name}; image {a.image}; model {model}; order limit {a.order_timeout}s; next conversation {n}')
    t_start = time.time(); reason_end = 'finish'
    try:
        while True:
            case = control / f'case_{n}.md'
            while not case.exists() and not (control / 'finish').exists():
                if a.timeout and time.time() - t_start > a.timeout:
                    break
                time.sleep(2)
            if (control / 'finish').exists():
                break
            if a.timeout and time.time() - t_start > a.timeout:
                reason_end = 'time limit of the problem'; break
            ctext = case.read_text().strip()
            m_ = re.search(r'TYPE:\s*([A-Z][A-Z -]+[A-Z])', ctext)
            typ = m_.group(1).strip() if m_ else None
            types = {'TASK LIST': 'task-sheet', 'FIND ASSUMPTION': 'find-assumption', 'PROVE ASSUMPTION': 'prove-assumption', 'FIX': 'fix-one-driver', 'CONFIRM FIX': 'confirm-fix', 'CLOSING': 'closing',
                     'ARCH-PLAN': 'architecture-plan', 'ARCH-REVIEW': 'architecture-review', 'HDL-EXPERIMENT': 'prove-assumption',
                     'RTL-HARNESS': 'rtl-harness', 'IP-MODEL-HARNESS': 'ip-model-harness', 'SPEC-PLANNING': 'spec-planning',
                     'MODEL-VECTOR-RUN': 'model-vector-run', 'SPEC-TESTCASE-REVIEW': 'spec-testcase-review',
                     'RTL-INVENTORY': 'rtl-inventory', 'MODEL-INVENTORY': 'model-inventory', 'BLOCK-PAIRING': 'block-pairing',
                     'SIGNAL-PAIRING': 'signal-pairing', 'SIGNAL-EXISTENCE-CHECK': 'signal-existence-check', 'MAP-REVIEW': 'map-review'}
            skill = ''
            if typ in types:   # the skill of the first work order's type comes with it, as the tool does for later ones
                for nm in (types[typ], 'uncertainty'):
                    t_ = re.sub(r'(?s)\A---.*?---\s*', '', (ROOT / 'skills' / nm / 'SKILL.md').read_text())
                    skill += f'\n\n----- skill: {nm} -----\n' + t_.strip()
            else:
                typ = None
            digest = digest_block(state, control, ctext) if a.digest == 'on' else ''
            extra = kick.rstrip() + '\n\n' + ctext + digest + skill + '\n'
            sh('docker', 'exec', name, 'sh', '-c', 'rm -f /tmp/rtlwork/conv_done; python3 - <<E\nimport json,os\nTYPE=' + repr(typ) + '\np="/tmp/rtlwork/state.json"\nif os.path.exists(p):\n    s=json.load(open(p)); s["next_pending"]=None; import time; s["order_t"]=time.time(); s["order_type"]=TYPE; s["order_obs"]=0; s["order_edits"]=0; s["order_reverts"]=0; json.dump(s,open(p,"w"),indent=1)\nE')
            ver = sh('git', '-C', str(ROOT), 'rev-parse', '--short', 'HEAD').stdout.strip() + ('+changes' if sh('git', '-C', str(ROOT), 'status', '--porcelain', 'tools', 'skills', 'resources').stdout.strip() else '')
            log(run, f'conversation {n} start (files: {"live checkout " + ver if dev else "image " + a.image})')
            t0 = time.time(); t_order = t0; reason = 'ended'
            with open(agent_log, 'a') as out:
                out.write(f'\n##### conversation {n} #####\n'); out.flush()
                p = subprocess.Popen(['docker', 'exec', '-e', 'CVDP_EXTRA_INSTRUCTIONS_B64=' + base64.b64encode(extra.encode()).decode(),
                                      name, 'python3', '/app/agent_qwen.py'], stdout=out, stderr=subprocess.STDOUT)
                answered = {f.name for f in box.glob('answer_*.md')}
                # live view of what the model is producing (the agent writes it piece by piece): the reasoning of the
                # current work order is collected, and the phrases that mark going round in circles are counted
                pos = agent_log.stat().st_size; tailbuf = ''; think = ''; said = ''; tells = 0
                TELL = re.compile(r"let me reconsider|actually, hold on|let me double-check|one final time", re.I)
                while p.poll() is None:
                    time.sleep(2)
                    with open(agent_log, errors='replace') as lf:
                        lf.seek(pos); tailbuf += lf.read(); pos = lf.tell()
                    *lines_, tailbuf = tailbuf.split('\n')
                    for ln in lines_:
                        if '"stream_event"' not in ln:
                            continue
                        try:
                            dl = json.loads(ln).get('event', {}).get('delta') or {}
                        except Exception:
                            continue
                        think += dl.get('thinking', '') or ''; said += dl.get('text', '') or ''
                    tells = len(TELL.findall(think))
                    # three signs of going round in circles (decided 2026-10-11; since 2026-10-11 evening they only go to live.json, they no longer end a conversation):
                    #  1 the same announced action ("let me record/report/...") three times in one work order's reasoning
                    #  2 "let me reconsider" fifty times   3 "actually, hold on" once
                    acts = collections.Counter(m.lower() for m in re.findall(r"let me (?:just )?(record|report|write|apply|send|submit|mark|run)\b", think, flags=re.I))
                    top_act = acts.most_common(1)[0] if acts else ('', 0)
                    n_recon = len(re.findall(r"let me reconsider", think, flags=re.I))
                    n_hold = len(re.findall(r"actually, hold on", think, flags=re.I))
                    stuck = (f'"let me {top_act[0]}" announced {top_act[1]} times' if top_act[1] >= 3 else
                             f'"let me reconsider" {n_recon} times' if n_recon >= 50 else
                             '"actually, hold on" appeared' if n_hold >= 1 else '')
                    (control / 'live.json').write_text(json.dumps({'conversation': n, 'order_seconds': round(time.time() - t_order), 'reasoning_chars': len(think),
                                                                   'loop_phrases': tells, 'signs': stuck, 'reasoning_tail': think[-600:], 'text_tail': said[-300:]}))
                    now_ans = {f.name for f in box.glob('answer_*.md')}
                    if now_ans - answered:           # an answer was delivered: a new work order starts now
                        answered = now_ans; t_order = time.time(); think = ''; said = ''; tells = 0
                    waiting = any(not (box / q.name.replace('request_', 'answer_')).exists() for q in box.glob('request_*.md'))
                    if waiting:                      # the agent is waiting for the orchestrator: not its time
                        t_order = time.time()
                    elif time.time() - t_order > a.order_timeout:
                        reason = f'work order exceeded {a.order_timeout}s'
                    elif a.timeout and time.time() - t_start > a.timeout:
                        reason = 'time limit of the problem'
                    if reason != 'ended':
                        sh('docker', 'exec', name, 'pkill', '-f', 'qwen')
                        time.sleep(3)
                        if p.poll() is None:
                            p.kill()
                        break
                rc = p.wait()
            (control / f'conv_{n}_reasoning.md').write_text(f'# reasoning of the last work order of conversation {n} ({len(think)} chars, {tells} loop phrases)\n\n' + think + ('\n\n# text\n\n' + said if said else ''))
            (control / f'conv_{n}.done').write_text(json.dumps({'conversation': n, 'seconds': round(time.time() - t0), 'reason': reason, 'exit_code': rc}))
            log(run, f'conversation {n} end: {reason}; {time.time() - t0:.0f}s; exit {rc}')
            if reason == 'time limit of the problem':
                reason_end = reason; break
            n += 1
    finally:                                  # the container is kept: --resume continues, --close removes it
        try:
            urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:11434/api/generate', json.dumps({'model': model, 'keep_alive': 0}).encode(),
                                                          {'Content-Type': 'application/json'}), timeout=30)
        except Exception:
            pass
        (run / 'finished.json').write_text(json.dumps({'reason': reason_end, 'conversations': n, 'wall_s': round(time.time() - t_start)}))
        log(run, f'work-order session end: {reason_end}; next conversation would be {n}; wall={time.time() - t_start:.0f}s; container {name} kept')


if __name__ == '__main__':
    main()
