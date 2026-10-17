#!/bin/bash
# 建立一個 v4 cell:新的 run 目錄，設計是原始 RTL，工具狀態取自 prepared/（任務單已核准、基準 RUN #1、模型已驗證，沒有 mark、探測、修改）。
# 另放入 v4 端口填表所需的輸入:架構套件(state/ip_work/arch)、state/pilot(model_dp.json、rtl_structure.json、骨架、腳本)。
# 用法: scripts/make_cell.sh TAG
set -e
D="$(cd "$(dirname "$0")/.." && pwd)"; TAG=$1
DST=$D/runs/orders-cvdp_agentic_AES_encryption_decryption_0005-qwen8-qc-$TAG-$(date +%Y%m%d)
[ -e "$DST" ] && { echo "$DST 已存在"; exit 1; }
mkdir -p "$DST/control/architecture" "$DST/state/pilot" "$DST/state/deliveries"
cp -R "$D/prepared/work" "$DST/work"; cp -R "$D/prepared/state/rtlwork" "$DST/state/rtlwork"; cp "$D/prepared/state/task_sheet.md" "$DST/state/"
rm -rf "$DST/state/rtlwork/ckpt/"* "$DST/state/rtlwork/conv_done"; mkdir -p "$DST/state/rtlwork/ckpt"
WS=$(ls -d "$DST"/work/*/harness/5); rm -rf "$WS/rundir/"* "$WS/rundir/".orchestrator 2>/dev/null; mkdir -p "$WS/rundir/.orchestrator"; chmod 777 "$WS/rundir" "$WS/rundir/.orchestrator"
mkdir -p "$DST/state/ip_work"; cp -R "$D/pilot/arch" "$DST/state/ip_work/arch"; rm -rf "$DST/state/ip_work/arch/__pycache__"
cp "$D/pilot/out/model_dp.json" "$D/pilot/out/rtl_structure_original.json" "$DST/state/pilot/"; mv "$DST/state/pilot/rtl_structure_original.json" "$DST/state/pilot/rtl_structure.json"
cp "$D/pilot_tools/"*.py "$DST/state/pilot/"
python3 - "$DST" "$D" "$TAG" <<'P'
import json, sys, hashlib, os, shutil
dst, root, tag = sys.argv[1:4]
st = json.load(open(dst + '/state/rtlwork/state.json'))
st['marks'] = {}; st['probed'] = []; st['ckpts'] = []; st['events'] = ['sim', 'model']; st['next_asks'] = 0; st['next_pending'] = None; st['assumptions'] = []
rtl = dst + '/work/cvdp_agentic_AES_encryption_decryption/harness/5/rtl'
h = hashlib.sha1()
for f in sorted(x for x in os.listdir(rtl) if x.endswith(('.sv', '.v'))):
    h.update(f.encode()); h.update(open(rtl + '/' + f, 'rb').read())
st['hash'] = h.hexdigest()
os.makedirs(dst + '/state/rtlwork/ckpt/last', exist_ok=True)
for f in os.listdir(rtl):
    if f.endswith(('.sv', '.v')): shutil.copy2(rtl + '/' + f, dst + '/state/rtlwork/ckpt/last/' + f)
json.dump(st, open(dst + '/state/rtlwork/state.json', 'w'), indent=1)
pr = json.load(open(root + '/prepared/protocol.json'))
pr['run_id'] = dst.rstrip('/').split('/')[-1]; pr['work_orders']['container'] = 'orders_' + tag; pr['work_orders']['sessions'] = []
pr['note'] = 'v4 cell %s: original RTL; tool state of prepared/' % tag
json.dump(pr, open(dst + '/protocol.json', 'w'), indent=2)
open(dst + '/control/cell.json', 'w').write(json.dumps({'tag': tag, 'history_start_line': sum(1 for _ in open(dst + '/state/rtlwork/history.jsonl'))}, indent=1))
P
chmod -R a+rwX "$DST/state"; echo "$DST"
