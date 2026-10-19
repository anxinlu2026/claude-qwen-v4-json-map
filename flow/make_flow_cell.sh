#!/bin/bash
# 建立一個「方塊對應流程」cell:原始 RTL、容器(交換模式)、架構套件 v0、HDL 骨架、說明與提示(由模板產生)、每個 cell 自己的 rtl 包裝。
# 用法: flow/make_flow_cell.sh TAG        輸出: cell 路徑
set -e
D="$(cd "$(dirname "$0")/.." && pwd)"; TAG=$1
C=$("$D/scripts/make_cell.sh" "$TAG" | tail -1); X=$C/exchange; mkdir -p "$X" "$C/hdl_bin"
"$D/scripts/start_container.sh" "$C" exchange >/dev/null
printf '#!/bin/sh\nexec docker exec -i orders_%s rtl "$@"\n' "$TAG" > "$C/hdl_bin/rtl"; chmod +x "$C/hdl_bin/rtl"
python3 "$D/flow/make_arch_package.py" "$X" 0 >/dev/null; python3 "$D/flow/make_hdl_skeleton.py" "$X" "$X/skeletons" 0 >/dev/null
RTLDIR=$(ls -d "$C"/work/*/harness/5)/rtl
for t in README_HDL:README_HDL.md prompt_round0:../prompt_round0.md prompt_round1:../prompt_round1.md; do
  python3 - "$D/flow/templates/${t%%:*}.template.md" "$X/${t##*:}" "$D" "$X" "$C/hdl_bin" "$RTLDIR" <<'PY'
import sys
src,dst,R,X,B,RT=sys.argv[1:7]
s=open(src).read().replace('{EXCHANGE}',X).replace('{HDLBIN}',B).replace('{REPO}',R).replace('{RTLDIR}',RT)
open(dst,'w').write(s)
PY
done
chmod -R a+rwX "$C/state" "$X"; echo "$C"
