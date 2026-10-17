#!/usr/bin/env python3
"""Make the per-block orders (Traditional Chinese): <id>_iface (c1_to + c2_from) and <id>_func (c3_0_function). usage: make_block_orders.py"""
import json, os
CONTROL = ['key_counter','round_counter','done_gen','key_done_flag']
BLOCKS = ['load_block','state_reg','output_map','add_round_key','inv_shift_rows','inv_sub_bytes','inv_mix_columns','round_mux',
          'round_key_store','round_key_select','key_expand_step','rot_word','sub_word','rcon_step','word_xor_chain']
INPUTS = '''輸入(機器上已經有):
  - /tmp/pilot/model_dp.json:架構模型給你的版本(只有資料路徑方塊;控制不在其中)。你負責的方塊是 blocks 裡 id = "{b}" 的那一項:看它的 ports_detail(inputs、outputs 的每個端口:寬度、類型、clock、邊緣、組合或暫存、最大與最小延遲、連到哪裡)、upstream_blocks、downstream_blocks、function_detail、python。標成「control (RTL's own; not specified by the architecture)」的連接,是架構沒有規定的控制,你要依 RTL 自己的控制去描述(不要去讀 /tmp/ip_work/arch/model.json 裡的控制部分)。
  - /tmp/ip_work/arch/model.py 與 model_cli.py:架構的 Python 函式。
  - /tmp/pilot/rtl_structure.json:工具(yosys)從 RTL 抽出的結構(模組、埠、暫存器與時脈與 reset、訊號與其依賴)。陣列已合併(current_data_ff[0][0] 到 [3][3] 是一個形狀 [4,4] 的訊號)。寬度、時脈、邊緣、reset 的事實從這裡複製。
  - RTL(rtl show 檔案 起 迄、rtl signals)、testbench(verif/tb_aes128_dec.sv)、模擬器(rtl sim、rtl probe、rtl blockcheck)。時間上的行為與延遲看不出來時,在模擬中觀察。
'''
RULES = '''規則:
  - 在執行任何其他指令之前,先建立骨架檔;之後邊讀邊填,不要等讀完才寫。
  - 架構的某個訊號在 RTL 找不到對應的訊號或角色時,結果欄直接寫 `no rtl signal`,在假設寫原因,不要為了「該算 same 還是 different」反覆推敲;判斷交給架構。
  - 標成「control (RTL's own...)」的連接:列出 RTL 實際用來控制這個方塊的訊號(名稱、寬度、類型、clock),結果欄寫 `not specified`;只有當 RTL 的控制行為看不清楚時才寫假設。
  - 比較的單位是「訊號」:數目、缺少什麼、多出什麼,以及每個訊號的屬性——寬度、類型(pulse 脈衝 / level 位準 / held 保持 / data(valid with X):資料,有效條件由訊號 X 限定)、屬於哪個 clock、rising 或 falling、組合或暫存、從輸入到它的最大延遲(週期)與最小延遲(週期)。
  - 行號:所有引用的 RTL 行號都必須從 rtl show 的輸出(或 cat -n)複製,不能自己計算或估計;引用程式碼時一併複製原文。
  - RTL 這一側的屬性只能從 rtl_structure.json、RTL 陳述式、testbench 或探測得到;延遲的做法要寫出來(組合 = 0 週期;暫存器串接 = 數暫存器級數;或探測輸入改變到輸出改變差幾列)。不能從名稱或註解推。
  - 只要有任何一項不同,就必須寫一條假設;只要有任何一點看不清楚,也必須寫一條假設,並在「歧義」寫明為什麼看不清楚(原因)。假設格式:編號(H{h}、H{h1}…)、對象、內容、原因。不要把猜測寫成事實。
  - 順便看到的功能差異(例如位元組或索引順序與架構的說明不同)也必須寫成編號假設,並註明「交給 c3 功能比較」;不能只寫在歧義裡。
  - 標題與表格欄位一律照骨架的原字(繁體),不要改寫。
  - 工作規則:第一個動作是用 shell 建立輸出檔(骨架如下,複製),之後邊讀邊把整個檔案重寫;回報前 grep -n TODO 輸出檔必須沒有輸出。
  - 不要改設計。用 rtl next 回報(格式固定):rtl next "skill step used: ... / found: ... / evidence: 檔案與指令 / unsure: ..."
'''
def table_header():
    return ('| 架構訊號 | RTL 訊號 | 寬度(架構/RTL) | 類型 pulse·level·held·data(valid with X)(架構/RTL) | clock(架構/RTL) | 邊緣 rising·falling(架構/RTL) | 組合或暫存(架構/RTL) | 最大延遲(架構/RTL) | 最小延遲(架構/RTL) | 結果 same·different·unknown | 假設編號 |\n'
            '|---|---|---|---|---|---|---|---|---|---|---|\n| TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |')
def side_skel(b, side):
    if side == 'to':
        t = f'# {b} c1_to:與下游的端口比較\n## 摘要\n- 架構預期的下游(方塊與訊號數):TODO\n- RTL 實際接到下游的訊號數與名稱:TODO\n- 缺少(架構有、RTL 沒有):TODO\n- 多出(RTL 有、架構沒有):TODO\n'
    else:
        t = f'# {b} c2_from:與上游的端口比較\n## 摘要\n- 架構預期的上游(方塊與訊號數):TODO\n- RTL 實際從上游接進來的訊號數與名稱:TODO\n- 缺少(架構有、RTL 沒有):TODO\n- 多出(RTL 有、架構沒有):TODO\n'
    return t + '## 逐訊號比較\n' + table_header() + '\n## 依據\nTODO(RTL 行號、探測 run 與列、延遲的量法)\n## 假設\nTODO\n## 歧義\nTODO(每一個歧義點寫明原因;沒有就寫「無」並說明檢查過什麼)\n'
FUNC = '''# {b} c3_0_function:功能理解與比較(以讀懂 RTL 為主)
## 引用
- c1_to 的結論(含假設編號):TODO
- c2_from 的結論(含假設編號):TODO
## 1. RTL 結構對應
這個 Python 方塊由哪些 RTL 陳述式組成(always_ff、always_comb、assign、generate、子模組實例):
| RTL 元素(模組、種類、名稱) | 行號 | 原文(複製) | 在這個方塊裡負責什麼 | 與其他方塊共用? |
|---|---|---|---|---|
| TODO | TODO | TODO | TODO | TODO |
## 2. 功能理解
依 RTL 說明每個陳述式做什麼(運算、條件、順序、時序),對照架構 function_detail,逐項標記:
| 項目 | 架構(function_detail) | RTL 實際 | 一致·不一致·無法確認 | 假設編號 |
|---|---|---|---|---|
| TODO | TODO | TODO | TODO | TODO |
## 控制(依 RTL 自己的)
TODO(決定這個方塊何時運作的 RTL 控制訊號、條件、行號與原文;只描述 RTL 實際怎麼做,架構沒有規定)
## 3. 證據
TODO(以讀程式為主,附行號;模擬探測或 rtl blockcheck 只在這個方塊實際運作時使用,附指令、run 編號、列。方塊在模擬中不運作(被上游擋住)時,把這件事寫成觀察和假設,不算失敗)
## 4. 缺少與多出
- 架構有、RTL 沒有的功能(可能需要新增):TODO
- RTL 有、這個 Python 方塊沒有說明的部分:TODO
## 5. 假設
TODO(編號、內容、原因、需要什麼才能證明;只寫發現與疑問,不提出修改方案,修改由架構決定)
## 6. 歧義
TODO(每一個歧義點寫明原因;沒有就寫「無」並說明檢查過什麼)
'''
CFUNC = '''# {b} c3_0_function:控制功能理解與時序比較(以讀懂 RTL 為主)
## 引用
- c1_to 的結論(含假設編號):TODO
- c2_from 的結論(含假設編號):TODO
## 1. RTL 結構對應
這個控制方塊由 RTL 的哪些暫存器與陳述式組成:
| RTL 元素(暫存器或訊號、always 區塊) | 行號 | 原文(複製) | 負責什麼 |
|---|---|---|---|
| TODO | TODO | TODO | TODO |
## 2. 功能理解
RTL 的狀態變數、更新條件、轉移,對照架構 model.json 的 control(state_variables、events、round_table、o_done_rule、remember_across_cycles):
| 項目 | 架構 | RTL 實際 | 一致·不一致·無法確認 | 假設編號 |
|---|---|---|---|---|
| TODO | TODO | TODO | TODO | TODO |
## 3. 時序表對照
用模擬探測,把 testbench 的兩個測試案例(有 key 更新、沿用已存的 key)在逐列的實際值,對照架構 model.json 的 schedule(cases 的 i_start、i_update_key、key_cnt、round、key_done、o_done 各列);列與列的位置從 start 那一列算起。
| 案例 | 訊號 | 架構(逐列) | RTL(逐列,附 run 與列) | 第一個不同的列 | 假設編號 |
|---|---|---|---|---|---|
| TODO | TODO | TODO | TODO | TODO | TODO |
## 4. 缺少與多出
- 架構有、RTL 沒有的功能(例如需要記住的資訊):TODO
- RTL 有、架構沒有說明的暫存器或行為:TODO
## 5. 假設
TODO(編號、內容、原因、需要什麼才能證明;只寫發現與疑問,不提出修改方案)
## 6. 歧義
TODO(每一個歧義點寫明原因;沒有就寫「無」並說明檢查過什麼)
'''
def order_iface(b, h):
    skel_to, skel_from = side_skel(b, 'to'), side_skel(b, 'from')
    return f'''WORK ORDER pilotB-{b}-iface - TYPE: ALIGN-IFACE
目標:對方塊「{b}」,把它在 RTL 裡的端口,和架構模型對它的上游、下游所宣告的端口,逐訊號比較,寫成兩份 Markdown:{b}_c1_to.md(與下游)和 {b}_c2_from.md(與上游)。這張工單不找功能錯誤。

{INPUTS.format(b=b)}
輸出:/tmp/deliveries/{b}_c1_to.md 與 /tmp/deliveries/{b}_c2_from.md。
**第一個動作**:建立這兩個骨架檔。

--- {b}_c1_to.md 的骨架 ---
{skel_to}
--- {b}_c2_from.md 的骨架 ---
{skel_from}
{RULES.format(h=h, h1=h+1)}'''
def order_func(b, h):
    ctl = b in CONTROL
    skel = (CFUNC if ctl else FUNC).format(b=b)
    extra = ('補充:這是控制方塊。不用 rtl blockcheck(它不是單純函式);用 rtl probe 看逐列的實際值,和架構 model.json 的 schedule 對照。架構的時序表是從規格推出來的,週期數是架構的假設(見 assumptions_arch.json);RTL 與它的差異不一定是 RTL 的錯,一律寫成假設,由架構判斷。若 RTL 的行為讓下游方塊根本不運作(例如計數器自己離開 idle),把它寫成觀察與假設。'
             if ctl else
             '補充:以讀懂 RTL 為主。數值比較(rtl blockcheck --in <RTL 輸入訊號串接> --out <RTL 輸出訊號串接> --model "python3 /tmp/ip_work/arch/model_cli.py block {b}")只在這個方塊在模擬裡實際運作時做;如果它沒有運作(例如被上游控制擋住),就不用硬做,把原因寫在「證據」與假設。使用 blockcheck 前需先 rtl model /tmp/ip_work/arch(需要經 orchestrator 審查)。訊號串接的順序要和架構 function_detail 說的參數順序一致。'.format(b=b))
    return f'''WORK ORDER pilotB-{b}-func - TYPE: ALIGN-FUNC
目標:對方塊「{b}」,讀懂它在 RTL 裡由哪些陳述式組成、各做什麼,並與架構的說明{"(含時序表)" if ctl else "和 Python 函式"}比較功能是否一致,寫成 {b}_c3_0_function.md。這份文件要引用同一方塊的 c1_to 與 c2_from(上一張工單,在 /tmp/deliveries/)。這張工單不修改設計,也不提出修改方案:發現與疑問寫成假設,修改由架構決定。

{INPUTS.format(b=b)}
  - /tmp/deliveries/{b}_c1_to.md、{b}_c2_from.md:你在上一張工單寫的端口比較。
輸出:/tmp/deliveries/{b}_c3_0_function.md。
**第一個動作**:建立這個骨架檔。

--- {b}_c3_0_function.md 的骨架 ---
{skel}
{extra}
{RULES.format(h=h, h1=h+1)}'''
def order_cov():
    skel = '# RTL 覆蓋清單\n## 全部的 RTL 元素\n| 模組 | 種類(always_ff·always_comb·assign·generate·實例·宣告) | 名稱 | 行號 | 對應的 Python 方塊(或「未對應」) | 備註 |\n|---|---|---|---|---|---|\n| TODO | TODO | TODO | TODO | TODO | TODO |\n## 未對應的 RTL\nTODO(逐項說明它在做什麼、為什麼不屬於任何一個 Python 方塊)\n## 沒有 RTL 對應的 Python 方塊\nTODO\n## 假設\nTODO\n## 歧義\nTODO\n'
    return f'''WORK ORDER pilotB-coverage - TYPE: ALIGN-COVER
目標:把 RTL 的每一個 always、assign、generate、子模組實例,逐一對應到架構的某個方塊,列出沒有對應到任何方塊的 RTL,以及沒有 RTL 對應的架構方塊,寫成 /tmp/deliveries/rtl_coverage.md。不修改設計,不提出修改方案。

{INPUTS.format(b='(全部方塊)')}
  - /tmp/deliveries/ 底下各方塊的 c1_to、c2_from、c3_0_function 文件。
**第一個動作**:建立骨架檔 /tmp/deliveries/rtl_coverage.md:

{skel}
{RULES.format(h=60, h1=61)}'''

if __name__ == '__main__':
    os.makedirs('hdl_orders/blocks', exist_ok=True)
    h = 10
    for b in BLOCKS:
        open(f'hdl_orders/blocks/{b}_iface.zh.md', 'w').write(order_iface(b, h)); h += 4
        open(f'hdl_orders/blocks/{b}_func.zh.md', 'w').write(order_func(b, h)); h += 4
    open('hdl_orders/blocks/rtl_coverage.zh.md', 'w').write(order_cov())
    print('made', 2 * len(BLOCKS) + 1, 'orders')
