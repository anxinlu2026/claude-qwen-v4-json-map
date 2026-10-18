#!/bin/bash
# 測試 rtl 關卡的兩種模式(strict、exchange):在全新 cell 上連續修改兩次,第一次修改後只做一次單元比對。
# 用法: flow/test_gate_modes.sh MODE   (會建立 cell gt<MODE> 與容器 orders_gt<MODE>,不刪除任何目錄)
D="$(cd "$(dirname "$0")/.." && pwd)"; MODE=$1
C=$(ls -d "$D"/runs/*-qc-gt$MODE-* 2>/dev/null | head -1); [ -n "$C" ] || C=$("$D/scripts/make_cell.sh" gt$MODE | tail -1); "$D/scripts/start_container.sh" "$C" $MODE >/dev/null; N=orders_gt$MODE
seq(){ python3 -c "print('+'.join('$1[%d][%d]'%(i%4,i//4) for i in range(16)))"; }
bc(){ docker exec $N sh -c "rtl blockcheck --in '$(seq AddRoundKey)' --out '$(seq MixColumns)' --model 'python3 /tmp/ip_work/arch/model_cli.py block inv_mix_columns' --when 'round_ff>=2 && round_ff<=10' >/dev/null 2>&1"; }
docker exec $N rtl sim >/dev/null 2>&1; docker exec $N rtl model /opt/resources/ip_models/aes128 >/dev/null 2>&1; bc
L=$(docker exec $N sh -c "sed -n 140p /code/rtl/aes128_decrypt.sv")
echo "--- [$MODE] replace 1 (the same text again: no functional change)"; docker exec -i $N sh -c "rtl replace rtl/aes128_decrypt.sv 140 140" <<<"$L" 2>&1 | head -2 | cut -c1-150
bc
echo "--- [$MODE] after one comparison, replace 2"; docker exec -i $N sh -c "rtl replace rtl/aes128_decrypt.sv 140 140" <<<"$L" 2>&1 | head -2 | cut -c1-170
docker rm -f $N >/dev/null
