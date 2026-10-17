#!/bin/bash
# Preparation replay (orders 0.2-0.5 and the task-sheet review): answer request_next_K with the stored order text, wait for the next request.
# usage: [RUN=<run dir>] orch_step.sh K     (the texts are in prep_orders/, copied from walk1; no other run is needed)
HERE="$(cd "$(dirname "$0")" && pwd)"; D="$(cd "$HERE/../.." && pwd)"
R=${RUN:-$(ls -td $D/runs/orders-* | head -1)}
B=$(ls -d $R/work/*/harness/*/rundir/.orchestrator)
K=$1; N=$((K+1)); T0=$(date +%s)
python3 - "$K" "$B" "$HERE/prep_orders" <<'P'
import sys
K,B,P=sys.argv[1:4]
t=open('%s/answer_next_%s.md'%(P,K)).read()
i=t.index('WORK ORDER')
open(B+'/answer_next_%s.md'%K,'w').write('Accepted.\n\n'+t[i:])
print('answered',K,'with:',t[i:i+60].splitlines()[0],'/',t[i:].splitlines()[1][:80])
P
for i in $(seq 1 55); do sleep 8; [ -f $B/request_next_$N.md ] && break; [ -f $B/request_sheet_1.md ] && break; done
echo "elapsed $(( $(date +%s)-T0 )) s"
f=$B/request_next_$N.md; [ -f $f ] || f=$B/request_sheet_1.md
sed -n '/^## Report/,/^## Recorded/p;/^## Task sheet/,+0p' $f | head -14 | cut -c1-700
