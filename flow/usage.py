"""Usage log for the flow tools (observability): one JSON line per use, appended to <exchange>/usage-log.jsonl (or $FLOW_USAGE_LOG).
Who ran it comes from $FLOW_ACTOR (set it to hdl, architecture or orchestrator); unknown when not set. The log records the use, not its quality."""
import json, os, sys, time
def log(exchange, tool, **fields):
    path = os.environ.get('FLOW_USAGE_LOG') or (os.path.join(exchange, 'usage-log.jsonl') if exchange else None)
    if not path: return
    rec = {"t": time.strftime('%Y-%m-%d %H:%M:%S'), "actor": os.environ.get('FLOW_ACTOR', 'unknown'), "tool": tool}
    rec.update(fields)
    try:
        with open(path, 'a') as f: f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    except OSError: pass
