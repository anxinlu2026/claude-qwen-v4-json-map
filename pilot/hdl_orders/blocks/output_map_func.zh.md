WORK ORDER pilotB-output_map-func - TYPE: ALIGN-FUNC
目標:對方塊「output_map」,讀懂它在 RTL 裡由哪些陳述式組成、各做什麼,並與架構的說明和 Python 函式比較功能是否一致,寫成 output_map_c3_0_function.md。這份文件要引用同一方塊的 c1_to 與 c2_from(上一張工單,在 /tmp/deliveries/)。這張工單不修改設計,也不提出修改方案:發現與疑問寫成假設,修改由架構決定。

輸入(機器上已經有):
  - /tmp/pilot/model_dp.json:架構模型給你的版本(只有資料路徑方塊;控制不在其中)。你負責的方塊是 blocks 裡 id = "output_map" 的那一項:看它的 ports_detail(inputs、outputs 的每個端口:寬度、類型、clock、邊緣、組合或暫存、最大與最小延遲、連到哪裡)、upstream_blocks、downstream_blocks、function_detail、python。標成「control (RTL's own; not specified by the architecture)」的連接,是架構沒有規定的控制,你要依 RTL 自己的控制去描述(不要去讀 /tmp/ip_work/arch/model.json 裡的控制部分)。
  - /tmp/ip_work/arch/model.py 與 model_cli.py:架構的 Python 函式。
  - /tmp/pilot/rtl_structure.json:工具(yosys)從 RTL 抽出的結構(模組、埠、暫存器與時脈與 reset、訊號與其依賴)。陣列已合併(current_data_ff[0][0] 到 [3][3] 是一個形狀 [4,4] 的訊號)。寬度、時脈、邊緣、reset 的事實從這裡複製。
  - RTL(rtl show 檔案 起 迄、rtl signals)、testbench(verif/tb_aes128_dec.sv)、模擬器(rtl sim、rtl probe、rtl blockcheck)。時間上的行為與延遲看不出來時,在模擬中觀察。

  - /tmp/deliveries/output_map_c1_to.md、output_map_c2_from.md:你在上一張工單寫的端口比較。
輸出:/tmp/deliveries/output_map_c3_0_function.md。
**第一個動作**:建立這個骨架檔。

--- output_map_c3_0_function.md 的骨架 ---
# output_map c3_0_function:功能理解與比較(以讀懂 RTL 為主)
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

補充:以讀懂 RTL 為主。數值比較(rtl blockcheck --in <RTL 輸入訊號串接> --out <RTL 輸出訊號串接> --model "python3 /tmp/ip_work/arch/model_cli.py block output_map")只在這個方塊在模擬裡實際運作時做;如果它沒有運作(例如被上游控制擋住),就不用硬做,把原因寫在「證據」與假設。使用 blockcheck 前需先 rtl model /tmp/ip_work/arch(需要經 orchestrator 審查)。訊號串接的順序要和架構 function_detail 說的參數順序一致。
規則:
  - 在執行任何其他指令之前,先建立骨架檔;之後邊讀邊填,不要等讀完才寫。
  - 架構的某個訊號在 RTL 找不到對應的訊號或角色時,結果欄直接寫 `no rtl signal`,在假設寫原因,不要為了「該算 same 還是 different」反覆推敲;判斷交給架構。
  - 標成「control (RTL's own...)」的連接:列出 RTL 實際用來控制這個方塊的訊號(名稱、寬度、類型、clock),結果欄寫 `not specified`;只有當 RTL 的控制行為看不清楚時才寫假設。
  - 比較的單位是「訊號」:數目、缺少什麼、多出什麼,以及每個訊號的屬性——寬度、類型(pulse 脈衝 / level 位準 / held 保持 / data(valid with X):資料,有效條件由訊號 X 限定)、屬於哪個 clock、rising 或 falling、組合或暫存、從輸入到它的最大延遲(週期)與最小延遲(週期)。
  - 行號:所有引用的 RTL 行號都必須從 rtl show 的輸出(或 cat -n)複製,不能自己計算或估計;引用程式碼時一併複製原文。
  - RTL 這一側的屬性只能從 rtl_structure.json、RTL 陳述式、testbench 或探測得到;延遲的做法要寫出來(組合 = 0 週期;暫存器串接 = 數暫存器級數;或探測輸入改變到輸出改變差幾列)。不能從名稱或註解推。
  - 只要有任何一項不同,就必須寫一條假設;只要有任何一點看不清楚,也必須寫一條假設,並在「歧義」寫明為什麼看不清楚(原因)。假設格式:編號(H30、H31…)、對象、內容、原因。不要把猜測寫成事實。
  - 順便看到的功能差異(例如位元組或索引順序與架構的說明不同)也必須寫成編號假設,並註明「交給 c3 功能比較」;不能只寫在歧義裡。
  - 標題與表格欄位一律照骨架的原字(繁體),不要改寫。
  - 工作規則:第一個動作是用 shell 建立輸出檔(骨架如下,複製),之後邊讀邊把整個檔案重寫;回報前 grep -n TODO 輸出檔必須沒有輸出。
  - 不要改設計。用 rtl next 回報(格式固定):rtl next "skill step used: ... / found: ... / evidence: 檔案與指令 / unsure: ..."
