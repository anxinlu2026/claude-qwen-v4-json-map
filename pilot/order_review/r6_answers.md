## 問 1
1. 你怎麼把 i_data 這個輸入端口的資料寫進 JSON？寫出你要執行的完整指令（值可以用示意）。

## 答 1(6s)
我會在確認 RTL 中 `i_data` 對應的訊號名、寬度及有效條件後，執行 `fill_port.py` 指令。指令格式為：`python3 /tmp/pilot/fill_port.py /tmp/deliveries/load_block_ports.json inputs i_data signal=<RTL訊號名> width=<位元數> kind=data "valid_when=<有效條件>" clock=<時脈名> edge=<邊緣> storage=register latency_min_cycles=<最小延遲> latency_max_cycles=<最大延遲> source="rtl line X; rtl_structure.json"`。此指令會自動將值寫入 JSON 並保留原有結構，若某欄位無法從 RTL 確定，則填入 `unknown` 讓腳本自動標記。

## 問 2
2. 你想把 signal 欄位改成兩個訊號用 + 連起來，可以嗎？指令怎麼寫？

## 答 2(3s)
可以，工單明確規定當多個訊號組成一個端口時，要用 `+` 連起來寫在 `signal` 欄位中。指令寫法為：`python3 /tmp/pilot/fill_port.py /tmp/deliveries/load_block_ports.json inputs <arch_port> signal=<訊號A>+<訊號B> width=<總位元數> ...`。請確保 `width` 填入這兩個訊號位寬的總和，其他欄位依實際 RTL 事實填寫。

## 問 3
3. 你發現 kind 想填「sticky」，腳本拒絕了。你怎麼辦？

## 答 3(3s)
根據工單規定，`kind` 欄位只能填 `pulse`、`level`、`held` 或 `data`，因此「sticky」是無效值。我應改填最符合該訊號行為的合法值（例如若訊號一旦觸發就保持不變，應填 `held`）。若確實無法歸類於這四種，則該欄位填 `unknown` 並讓腳本自動記錄。
