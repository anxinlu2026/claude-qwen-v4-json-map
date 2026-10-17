# 試點:架構定義方塊、HDL 對齊 RTL(AES_0005)

目的:測試「架構用規格定義資料路徑與控制流程(Python 加 JSON),HDL 把 RTL 對齊到這些方塊,有疑問就記假設,再由架構逐一證明」是否能找出 walk5 的 12 個錯誤,以及比現在的除錯流程好在哪裡。

## 角色與產出

| 步驟 | 誰 | 輸入 | 產出 |
|---|---|---|---|
| A 定義 | 架構(獨立 session,**只看規格,不看被測 RTL**) | 題目文字、docs、testbench、函式庫模型 `aes128`、標準文字 | `arch/model.json`(方塊、連線、控制流程、介面、時序表)、`arch/model.py`(每個方塊的 Python 與週期級頂層模型)、`arch/harness_check.py`(模型通過 testbench 的證明)、`arch/assumptions_arch.json` |
| B 抽取 | 工具(yosys) | 被測 RTL | `out/rtl_structure.json`(模組、埠、暫存器、訊號、依賴;陣列合併) |
| C 對齊 | HDL(Qwen) | `arch/model.json`、`out/rtl_structure.json`、RTL | `hdl/rtl_map.json`:每個架構方塊對應的 RTL 訊號與驅動;每個介面訊號的說明(clk/reset/輸入/輸出/posedge/negedge/脈衝/多週期/功能);缺少或多出的功能;假設清單 |
| D 審查 | 架構 | `hdl/rtl_map.json` | `review/review.md`:接受、退回、補問;合併後的假設總表 |
| E 證明 | 架構排順序,HDL 執行 | 假設總表、模型、工具 | 每個假設的證明紀錄(blockcheck、探測);HDL 從失敗輸出沿 JSON 的依賴往上游找第一個偏離的驅動 |

## JSON 草案

`arch/model.json`:
```json
{
  "design": "aes128_decrypt",
  "interface": [{"name":"clk","dir":"in","width":1,"role":"clock","edge":"pos"},
                {"name":"i_update_key","dir":"in","width":1,"role":"control","timing":"level, sampled with i_start; may be 0 in later rows","function":"..."}],
  "blocks": [{"id":"add_round_key","kind":"datapath","inputs":[{"name":"state","width":128,"layout":"byte n = row n%4, col n/4"},{"name":"round_key","width":128}],
              "outputs":[{"name":"state_out","width":128}],
              "timing":{"type":"combinational","valid_when":"round >= 1"},"python":"model.py:add_round_key"}],
  "edges": [{"from":"state_reg.q","to":"add_round_key.state"}],
  "control": {"round_counter": {"states":"0 idle, 1..12","events":[{"name":"start","when":"i_start & idle","effect":"..."}],"latency":{"with_key_update":"11 rows in round 1","without":"1 row"}}},
  "schedule": [{"case":"update","rows":{"i_start":[...],"round":[...],"key_done":[...]}}]
}
```
`hdl/rtl_map.json`:
```json
{
  "blocks": [{"arch_id":"add_round_key","rtl_in":["current_data_ff","expanded_key"],"rtl_out":["AddRoundKey"],"driver":"always_comb decypher_logic","assumptions":["A7"]}],
  "interface_notes": [{"port":"i_update_key","observed":"...","description":"..."}],
  "missing_in_rtl": [], "extra_in_rtl": [],
  "assumptions": [{"id":"A7","subject":"add_round_key.round_key","statement":"...","source":"rtl|spec|inferred","status":"open"}]
}
```

## 衡量(對照 walk5 的 12 個已知錯誤)
- 只靠對齊與介面說明(不跑模擬)能找出幾個;需要數值比對才找到的有幾個。
- 假設數量、命中率、誤報;架構審查退回幾次。
- 各步驟的工單數、時間、token。

## 規則
- 架構在步驟 A 不讀被測 RTL,避免被錯誤影響模型。
- Qwen 的 JSON 中不確定的地方一律寫成假設,不得猜成事實。
- 結構由工具抽取;Qwen 補語意。
- 這個試點的工具與 skills 改動放另一份快照,不碰 `snapshot-walk5-rerun`。

## 修訂(2026-10-17):HDL 的交付改成每個方塊三份比較文件

HDL 仍然拿到架構的 model.json(含每個端口的屬性),但每個方塊要交三份 Markdown(放在 /tmp/deliveries/):

| 文件 | 比較的內容 |
|---|---|
| `<方塊>_c1_to.md` | 這個方塊的輸出端口,與架構對下游宣告的端口:訊號數、缺少什麼、多出什麼,以及每個訊號的屬性(pulse 或 level、屬於哪個 clock、rising 或 falling、位寬、組合或暫存、最大延遲、最小延遲) |
| `<方塊>_c2_from.md` | 這個方塊的輸入端口,與架構對上游宣告的端口:同上 |
| `<方塊>_c3_0_function.md` | 引用 c1_to 與 c2_from;加上 RTL 與架構 Python 在功能實作上的差異(讀程式、rtl blockcheck 數值比較);有差異或不確定一律寫假設;歧義點寫明原因 |

規則:任何一項不同就必須寫假設;任何一點看不清楚也必須寫假設並在「歧義」寫明原因。延遲的量法要寫出來(組合 = 0;暫存器串接 = 級數;或探測差幾列)。
工單依方塊分成兩張(iface:c1_to 加 c2_from;func:c3),由 `tools/make_block_orders.py` 產生(繁體中文),放在 `hdl_orders/blocks/`。另有 clock、reset 的獨立工單 `C1clk`、`C1rst`。架構的 model.json 需要有 `ports_detail`、`upstream_blocks`、`downstream_blocks`、`function_detail`、`python`,以及 `model_cli.py`(給 rtl blockcheck 用),已請架構補上(步驟 A 補充)。
先拿 load_block 與 inv_mix_columns 兩個方塊試跑,確認格式與時間可行後再展開。
