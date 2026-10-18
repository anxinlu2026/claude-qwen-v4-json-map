#!/bin/bash
# usage: [RUN=<run dir>] [ORDER=13b] relay.sh CONV "state sentence"  -> case_CONV.md from architecture/order_<ORDER or CONV>.md, issue, wait for the report, print it
D="$(cd "$(dirname "$0")/.." && pwd)"   # claude/cvdp_aes0005_multi_ai (dashboard/orch.py lives here)
R=${RUN:-$(ls -d $D/runs/* | head -1)}; N=$1; STATE=$2; O=${ORDER:-$N}
python3 - "$R" "$N" "$O" "$STATE" <<'P'
import sys
R,N,O,S=sys.argv[1:5]
o=open(f'{R}/control/architecture/order_{O}.md').read().strip()
hdr=(f"CASE FILE — conversation {N}\nWhere the work stands: {S}\n"
"Rules for this order: do exactly what it says, copy every value from tool output, change only what the order names, report with rtl next.\n\n")
open(f'{R}/control/case_{N}.md','w').write(hdr+o+"\n")
P
T=$(grep -m1 -o "TYPE: [A-Z ]*[A-Z]" $R/control/case_$N.md | sed 's/TYPE: //')
python3 $D/dashboard/orch.py handoff $O "order_$O.md from the architecture session relayed unchanged as case_$N.md" --run $R >/dev/null
python3 $D/dashboard/orch.py issue $O "$T (architecture order $O) to Qwen 27B 8-bit thinking off, conversation $N; limit set by the runner" --run $R >/dev/null
for i in $(seq 1 60); do f=$(find $R/work -name 'request_*.md' -newer $R/control/case_$N.md | head -1); [ -n "$f" ] && break; [ -f $R/control/conv_$N.done ] && break; sleep 8; done
date +%H:%M:%S; echo "$f" | sed 's#.*/##'
sed -n '/^## Report/,/^## Recorded/p' "$f" | head -6 | cut -c1-1800
python3 - "$R" <<'P'
import json,sys
H=[json.loads(l) for l in open(sys.argv[1]+'/state/rtlwork/history.jsonl')]
for h in [x for x in H if 'cmd' in x and not x['cmd'].startswith(('next','status','history'))][-5:]:
    print('$',h['cmd'][:200].replace('\n',' ')); print('   ',(h.get('out') or '')[:1000].replace('\n',' | '))
P
