#!/bin/bash
# 監看 cell 的等待中的請求與驅動是否結束。用法: flow/watch_requests.sh CELL_DIR
C=$1; X=$C/exchange; last=""
while true; do
  p=$(python3 -c "import json;d=json.load(open('$X/pending-requests.json'))['pending'];print(len(d), [x['file'] for x in d])" 2>/dev/null || echo "0 []")
  if [ "$p" != "$last" ]; then echo "$(date +%H:%M:%S) pending requests: $p"; last="$p"; fi
  if ! pgrep -f "flow/run_hdl_cc" >/dev/null; then echo "$(date +%H:%M:%S) driver ended: $(tail -2 $C/run_hdl_cc_round0.log | tr '\n' ' ')"; break; fi
  sleep 60
done
