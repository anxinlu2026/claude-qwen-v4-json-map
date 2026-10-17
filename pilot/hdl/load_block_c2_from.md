# load_block c2_from:與上游的端口比較
## 摘要
- 架構預期的上游(方塊與訊號數):`design port`,1 個訊號(`i_data`,128 bit)
- RTL 實際從上游接進來的訊號數與名稱:1 個訊號 — `i_data`(top-level input port,128 bit)
- 缺少(架構有、RTL 沒有):無
- 多出(RTL 有、架構沒有):無
## 逐訊號比較
| 架構訊號 | RTL 訊號 | 寬度(架構/RTL) | 類型 pulse·level·held(架構/RTL) | clock(架構/RTL) | 邊緣 rising·falling(架構/RTL) | 組合或暫存(架構/RTL) | 最大延遲(架構/RTL) | 最小延遲(架構/RTL) | 結果 same·different·unknown | 假設編號 |
|---|---|---|---|---|---|---|---|---|---|---|
| i_data | i_data | 128/128 | level/level | none(組合)/none(組合) | n/a/n/a | 組合/組合 | 0/0 | 0/0 | same | H11 |

## 依据
- 架構:/tmp/ip_work/arch/model.json 中 `load_block.upstream_blocks = [{block: design port, signals: [i_data], count: 1}]`;`ports_detail.inputs[0] = {name: i_data, width: 128, kind: "data-valid-with(i_start)", clock: "none (combinational)", edge: "n/a", storage: "combinational", latency_min_cycles: 0, latency_max_cycles: 0, connected_to: [{block: design port, port: i_data}], valid_when: "row 0 (start row)", note: "byte 0 = bits[127:120]"}`。
- RTL:rtl/aes128_decrypt.sv 第 11 行 `input logic [NBW_DATA-1:0] i_data`(NBW_DATA=128,為 top-level 輸入端口)。rtl_structure.json:`aes128_decrypt.ports` 有 `i_data`(direction input, width 128);`signals` 有 `i_data`(kind input, width 128, depends_on 空)。
- 探測:`rtl probe i_data current_data_ff[0][0] current_data_ff[0][1] --max 8`(RUN #2):t=25 行 `i_data=3925841d02dc09fbdc118597196a0b32`,確認 `i_data` 為 128-bit 輸入,start 行有效。
- 延遲量法:`i_data` 為 top-level 輸入端口(組合,無 clock),從上游到 load_block 輸入為 0 週期,與架構一致。

## 假设
- H11:對象 = `i_data` 的「類型」欄。內容 = 架構 kind `"data-valid-with(i_start)"` 映射為 `level`(資料位準,valid 由 `i_start` 限定)。原因 = 同 H10,骨架類型欄只有 pulse/level/held 三選一,此資料訊號在 `i_start` 期間保持位準,故歸為 level。

## 歧義
- 無端口歧義:`i_data` 的寬度/類型/clock/邊緣/組合/延遲皆 same。
- 資料位元排列(功能,超出本工單):同 c1_to,RTL load 的 byte 排列為 row-major,與 FIPS 197 的 column-major 為轉置;這是功能問題,本工單不找功能錯誤,僅記明。
- valid 條件(功能/控制,超出本工單):架構說 `i_data` valid_when "row 0 (start row)"(由 `i_start` 限定);RTL 的 load 條件是 `i_start & o_done`(第 79 行)。`o_done = (round_ff == 4'd0)`,在 start 行為 1,故在 start 行等价。這是功能/控制細節,不影響端口屬性,故結果仍記 `same`。
