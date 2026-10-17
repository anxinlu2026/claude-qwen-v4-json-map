#!/bin/bash
# Advance one order of a delegation cell: close the previous report (optional), issue the next order, wait for the report (up to ~9.5 min per call).
# usage: adv.sh RUNDIR CLOSE_REQ_NUMBER|- "closing text" ORDER_FILE_SUFFIX CONV NEXT_REQ_NUMBER "where the work stands"
#   ORDER_FILE_SUFFIX: the order is control/architecture/order_<suffix>.md ; use '-' as ORDER to only wait (no issue)
RUN=$1; CK=$2; CT=$3; ORD=$4; CONV=$5; NREQ=$6; STATE=$7
D="$(cd "$(dirname "$0")/.." && pwd)"
B=$(ls -d $RUN/work/*/harness/*/rundir/.orchestrator)
if [ "$CK" != "-" ]; then printf 'CONVERSATION COMPLETE\n%s\n' "$CT" > $B/answer_next_$CK.md; fi
if [ "$ORD" != "-" ]; then
  RUN=$RUN ORDER=$ORD nohup $D/orchestrator/relay.sh $CONV "$STATE" > /tmp/relay_adv_$CONV.out 2>&1 &
fi
pending(){ for f in $B/request_model_*.md; do [ -f "$f" ] || continue; a=${f/request_/answer_}; [ -f "$a" ] || { echo "MODEL REVIEW PENDING: $f"; return 0; }; done; return 1; }
for i in $(seq 1 190); do pending && break; [ -f $B/request_next_$NREQ.md ] && break; [ -f $RUN/control/conv_$CONV.done ] && break; sleep 3; done
date +%H:%M:%S; cat $RUN/control/conv_$CONV.done 2>/dev/null; echo
[ -f $B/request_next_$NREQ.md ] && sed -n '/^## Report/,/^## Recorded/p' $B/request_next_$NREQ.md | cut -c1-2600
python3 - $RUN <<'P'
import json,sys,time
H=[json.loads(l) for l in open(sys.argv[1]+'/state/rtlwork/history.jsonl')]
for h in H[-3:]: print('  ',time.strftime('%H:%M:%S',time.localtime(h['t'])),h.get('cmd','')[:80].replace('\n',' '),'|',(h.get('out') or '')[:110].replace('\n',' '))
P
