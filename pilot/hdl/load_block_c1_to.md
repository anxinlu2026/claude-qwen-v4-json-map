# load_block c1_to:與下游的端口比較
## 摘要
- 架構預期的下游(方塊與訊號數):`state_reg`,1 個訊號(`state_in`,128 bit)
- RTL 實際接到下游的訊號數與名稱:1 個訊號 — `current_data_nx`(load 分支,128 bit / 16 bytes)→ `current_data_ff`(state 暫存器,128 bit)
- 缺少(架構有、RTL 沒有):無
- 多出(RTL 有、架構沒有):無
## 逐訊號比較
| 架構訊號 | RTL 訊號 | 寬度(架構/RTL) | 類型 pulse·level·held(架構/RTL) | clock(架構/RTL) | 邊緣 rising·falling(架構/RTL) | 組合或暫存(架構/RTL) | 最大延遲(架構/RTL) | 最小延遲(架構/RTL) | 結果 same·different·unknown | 假設編號 |
|---|---|---|---|---|---|---|---|---|---|---|
| state_in | current_data_nx(load 分支)→ current_data_ff | 128/128 | level/level | none(組合)/none(組合) | n/a/n/a | 組合/組合 | 0/0 | 0/0 | same | H10 |

## 依据
- 架構:/tmp/ip_work/arch/model.json 中 `load_block.downstream_blocks = [{block: state_reg, signals: [state_in], count: 1}]`;`ports_detail.outputs[0] = {name: state_in, width: 128, kind: "data-valid-with(i_start)", clock: "none (combinational)", edge: "n/a", storage: "combinational", latency_min_cycles: 0, latency_max_cycles: 0, connected_to: [{block: state_reg, port: state_in}], valid_when: "row 0; captured by state_reg at the start edge", note: "pure wiring, same bits; row n%4, col n//4"}`。
- RTL:rtl/aes128_decrypt.sv 第 78-92 行 `always_comb next_data` 的 load 分支:`if(i_start & o_done) current_data_nx[i][j] = i_data[NBW_DATA-(4*i+j)*NBW_BYTE-1-:NBW_BYTE];`(純組合,0 週期)。`current_data_ff` 為 state 暫存器(第 56-76 行 `always_ff`,posedge clk,async reset,reset 0)。rtl_structure.json:`current_data_nx` kind=combinational(width 8, shape [16]);`current_data_ff` kind=register(clock clk, posedge, async reset, count 16)。
- 探測:`rtl probe i_data current_data_ff[0][0] current_data_ff[0][1] --max 8`(RUN #2):t=25 行 `i_data=3925841d02dc09fbdc118597196a0b32`(start 行,`i_start=1`),`current_data_ff` 在該 posedge 後更新,確認 load 路徑 `i_data → current_data_nx → current_data_ff` 存在。
- 延遲量法:load 分支為組合(`always_comb`),`i_data` 改變到 `current_data_nx` 改變為 0 週期;`current_data_ff` 在 posedge 捕獲(1 個暫存器級,但該級屬於 state_reg,不屬於 load_block 的輸出端口)。load_block 的輸出端口 `state_in` 本身為組合,延遲 0,與架構一致。

## 假设
- H10:對象 = `state_in` 的「類型」欄。內容 = 架構 kind 字串 `"data-valid-with(i_start)"` 映射為 `level`(資料位準,valid 由 `i_start` 限定)。原因 = 骨架的類型欄只有 pulse/level/held 三選一,而架構用 `"data-valid-with(i_start)"` 描述;此資料訊號在 `i_start` 期間保持位準,故歸為 level,非脈衝(pulse)或保持(held)。

## 歧義
- 訊號命名/結構差異(非端口屬性):架構有專屬訊號 `state_in`;RTL 沒有專屬 `state_in`,load 是 `current_data_nx` 的一個分支(`current_data_nx` 同時也處理 round 邏輯,第 80-90 行)。這是結構/命名差異,不影響端口屬性(寬度/類型/clock/邊緣/組合/延遲皆 same),故結果仍記 `same`。
- 資料位元排列(功能,超出本工單):RTL load 把 byte n 放到 `[n//4][n%4]`(row-major),而 testbench 註解與 FIPS 197 期望 `[n%4][n//4]`(column-major),兩者為轉置。這是功能(資料布局)問題,本工單(ALIGN-IFACE)不找功能錯誤,故不作為端口 mismatch;僅在此記明,以免後續誤判。
- 探測值解讀:probe 行顯示「邊沿前」的暫存器值,t=25 行 `current_data_ff[0][0]=f7` 為邊沿前舊值;load 在該 posedge 捕獲,新值在下一行體現。此為 probe 取樣時點問題,不影響端口結論。
