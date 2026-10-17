WORK ORDER pilotB-output_map-iface - TYPE: ALIGN-IFACE
目標:對方塊「output_map」,把它在 RTL 裡的端口,和架構模型對它的上游、下游所宣告的端口,逐訊號比較,寫成兩份 Markdown:output_map_c1_to.md(與下游)和 output_map_c2_from.md(與上游)。這張工單不找功能錯誤。

輸入(機器上已經有):
  - /tmp/pilot/model_dp.json:架構模型給你的版本(只有資料路徑方塊;控制不在其中)。你負責的方塊是 blocks 裡 id = "output_map" 的那一項:看它的 ports_detail(inputs、outputs 的每個端口:寬度、類型、clock、邊緣、組合或暫存、最大與最小延遲、連到哪裡)、upstream_blocks、downstream_blocks、function_detail、python。標成「control (RTL's own; not specified by the architecture)」的連接,是架構沒有規定的控制,你要依 RTL 自己的控制去描述(不要去讀 /tmp/ip_work/arch/model.json 裡的控制部分)。
  - /tmp/ip_work/arch/model.py 與 model_cli.py:架構的 Python 函式。
  - /tmp/pilot/rtl_structure.json:工具(yosys)從 RTL 抽出的結構(模組、埠、暫存器與時脈與 reset、訊號與其依賴)。陣列已合併(current_data_ff[0][0] 到 [3][3] 是一個形狀 [4,4] 的訊號)。寬度、時脈、邊緣、reset 的事實從這裡複製。
  - RTL(rtl show 檔案 起 迄、rtl signals)、testbench(verif/tb_aes128_dec.sv)、模擬器(rtl sim、rtl probe、rtl blockcheck)。時間上的行為與延遲看不出來時,在模擬中觀察。

輸出:/tmp/deliveries/output_map_c1_to.md 與 /tmp/deliveries/output_map_c2_from.md。
**第一個動作**:建立這兩個骨架檔。

--- output_map_c1_to.md 的骨架 ---
# output_map c1_to:與下游的端口比較
## 摘要
- 架構預期的下游(方塊與訊號數):TODO
- RTL 實際接到下游的訊號數與名稱:TODO
- 缺少(架構有、RTL 沒有):TODO
- 多出(RTL 有、架構沒有):TODO
## 逐訊號比較
| 架構訊號 | RTL 訊號 | 寬度(架構/RTL) | 類型 pulse·level·held·data(valid with X)(架構/RTL) | clock(架構/RTL) | 邊緣 rising·falling(架構/RTL) | 組合或暫存(架構/RTL) | 最大延遲(架構/RTL) | 最小延遲(架構/RTL) | 結果 same·different·unknown | 假設編號 |
|---|---|---|---|---|---|---|---|---|---|---|
| TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
## 依據
TODO(RTL 行號、探測 run 與列、延遲的量法)
## 假設
TODO
## 歧義
TODO(每一個歧義點寫明原因;沒有就寫「無」並說明檢查過什麼)

--- output_map_c2_from.md 的骨架 ---
# output_map c2_from:與上游的端口比較
## 摘要
- 架構預期的上游(方塊與訊號數):TODO
- RTL 實際從上游接進來的訊號數與名稱:TODO
- 缺少(架構有、RTL 沒有):TODO
- 多出(RTL 有、架構沒有):TODO
## 逐訊號比較
| 架構訊號 | RTL 訊號 | 寬度(架構/RTL) | 類型 pulse·level·held·data(valid with X)(架構/RTL) | clock(架構/RTL) | 邊緣 rising·falling(架構/RTL) | 組合或暫存(架構/RTL) | 最大延遲(架構/RTL) | 最小延遲(架構/RTL) | 結果 same·different·unknown | 假設編號 |
|---|---|---|---|---|---|---|---|---|---|---|
| TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
## 依據
TODO(RTL 行號、探測 run 與列、延遲的量法)
## 假設
TODO
## 歧義
TODO(每一個歧義點寫明原因;沒有就寫「無」並說明檢查過什麼)

規則:
  - 在執行任何其他指令之前,先建立骨架檔;之後邊讀邊填,不要等讀完才寫。
  - 架構的某個訊號在 RTL 找不到對應的訊號或角色時,結果欄直接寫 `no rtl signal`,在假設寫原因,不要為了「該算 same 還是 different」反覆推敲;判斷交給架構。
  - 標成「control (RTL's own...)」的連接:列出 RTL 實際用來控制這個方塊的訊號(名稱、寬度、類型、clock),結果欄寫 `not specified`;只有當 RTL 的控制行為看不清楚時才寫假設。
  - 比較的單位是「訊號」:數目、缺少什麼、多出什麼,以及每個訊號的屬性——寬度、類型(pulse 脈衝 / level 位準 / held 保持 / data(valid with X):資料,有效條件由訊號 X 限定)、屬於哪個 clock、rising 或 falling、組合或暫存、從輸入到它的最大延遲(週期)與最小延遲(週期)。
  - 行號:所有引用的 RTL 行號都必須從 rtl show 的輸出(或 cat -n)複製,不能自己計算或估計;引用程式碼時一併複製原文。
  - RTL 這一側的屬性只能從 rtl_structure.json、RTL 陳述式、testbench 或探測得到;延遲的做法要寫出來(組合 = 0 週期;暫存器串接 = 數暫存器級數;或探測輸入改變到輸出改變差幾列)。不能從名稱或註解推。
  - 只要有任何一項不同,就必須寫一條假設;只要有任何一點看不清楚,也必須寫一條假設,並在「歧義」寫明為什麼看不清楚(原因)。假設格式:編號(H26、H27…)、對象、內容、原因。不要把猜測寫成事實。
  - 順便看到的功能差異(例如位元組或索引順序與架構的說明不同)也必須寫成編號假設,並註明「交給 c3 功能比較」;不能只寫在歧義裡。
  - 標題與表格欄位一律照骨架的原字(繁體),不要改寫。
  - 工作規則:第一個動作是用 shell 建立輸出檔(骨架如下,複製),之後邊讀邊把整個檔案重寫;回報前 grep -n TODO 輸出檔必須沒有輸出。
  - 不要改設計。用 rtl next 回報(格式固定):rtl next "skill step used: ... / found: ... / evidence: 檔案與指令 / unsure: ..."
