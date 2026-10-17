## 問 1
1. 這張工單要你交出什麼？它不要你做什麼？

## 答 1(8s)
1. 這張工單要求你將 RTL 中 `load_block` 方塊的實際端口資訊如實填入指定的 JSON 檔案中。
2. 它明確禁止你進行任何比較、判斷對錯、追查原因或修改設計，僅限於記錄事實。

## 問 2
2. 你會執行的前六個指令是什麼（寫出指令本身，含 rtl probe 的參數）？

## 答 2(7s)
1. `cp /tmp/pilot/load_block_ports.skeleton.json /tmp/deliveries/load_block_ports.json`
2. `cat /tmp/deliveries/load_block_ports.json`
3. `rtl show rtl/aes128_decrypt.sv 1 140`
4. `cat /tmp/pilot/rtl_structure.json`
5. `rtl probe <rtl_signal_name> --to <sim_end_time> --max 40`
6. `python3 -c "import json; f='/tmp/deliveries/load_block_ports.json'; d=json.load(open(f)); [d[k]['rtl'].update({'signal':'...','width':...}) for k in d if 'TODO' in str(d[k]['rtl'])]; json.dump(d, open(f,'w'), indent=2)"`

*註：第5步的 `<rtl_signal_name>` 與 `<sim_end_time>` 需根據第3、4步讀到的 RTL 訊號名與模擬結束時間替換；第6步為示意性 Python 指令，實際執行時需依 JSON 結構精確修改對應欄位。*

## 問 3
3. 情境 A：某個端口的資料，RTL 要在兩個訊號同時為真時才有效。valid_when 和 kind 各填什麼？

## 答 3(1s)
kind 應填 "data"，因為這是帶有有效條件的資料訊號。
valid_when 應填入 RTL 中描述該兩個訊號同時為真的具體邏輯條件表達式。

## 問 4
4. 情境 B：骨架裡有個 arch_port，你在 RTL 裡找不到任何對應的訊號。signal、width 和其他欄位各填什麼？

## 答 4(2s)
signal 欄位填 "none"。
width 及其他所有欄位（如 kind、clock、edge 等）皆填 "n/a"。
這符合工單中「RTL 裡沒有對應的訊號就寫 "none"（其餘欄位寫 "n/a"）」的規定。

## 問 5
5. 情境 C：你看得出一個端口的寬度，但它的延遲從 RTL、testbench 和探測都看不出來。延遲欄位和 unknown 怎麼填？

## 答 5(2s)
latency_min_cycles 和 latency_max_cycles 欄位應填 "unknown"。
unknown 欄位應填入 ["latency_min_cycles", "latency_max_cycles"]，以標示這些資訊無法從現有證據中獲得。

## 問 6
6. 情境 D：RTL 有一個控制訊號接到這個方塊，骨架裡沒有它。你放在哪裡？要不要寫它在做什麼？

## 答 6(2s)
應將其記錄在 JSON 的 "rtl_extra_ports" 欄位中，並包含 signal、width、kind 和 source。
不需要分析或說明它的行為，僅列出這些基本事實即可。

## 問 7
7. 情境 E：你猜架構模型裡這個端口的寬度是 128，而 RTL 的寬度你還沒查。你可以直接填 128 嗎？

## 答 7(2s)
不可以，工單明確規定只記錄 RTL 實際有的東西，且禁止比較或判斷對錯。
必須先從 RTL 中查出實際寬度，若查不到則填入 "unknown" 並記錄在 unknown 欄位中，絕不能基於架構模型的假設直接填入 128。

## 問 8
8. 你怎麼修改 JSON 才能保證鍵名和結構不變？完成前要檢查什麼？

## 答 8(2s)
使用 Python 載入 JSON 並僅修改對應的 "rtl" 欄位值，確保不變更鍵名或整體結構，最後寫回檔案。
完成後需執行 `grep -n TODO` 確認無剩餘 TODO，並用 `python3 -m json.tool` 驗證檔案為合法 JSON。

## 問 9
9. 你估計要花多久？分配是什麼？

## 答 9(3s)
預計總耗時約 10-12 分鐘，以符合 15 分鐘的限時要求。
時間分配為：複製骨架與讀取 RTL/結構檔約 3-4 分鐘，探測訊號行為約 2-3 分鐘，填寫 JSON 並驗證約 3-4 分鐘，最後提交約 1 分鐘。

## 問 10
10. 工單裡哪些地方不確定或前後矛盾？沒有就寫「沒有」並說明你檢查了什麼。

## 答 10(4s)
沒有。
我檢查了工單中關於「只記錄事實」、「禁止比較/判斷/修改」的指令與各欄位填寫規則（如 signal 為 none 時其他欄位填 n/a、unknown 欄位的用法）是否一致，確認所有要求均指向「如實記錄 RTL 事實」且無邏輯衝突。
我也核對了操作流程（複製骨架、讀取 RTL、探測、修改 JSON、驗證）與欄位定義之間的對應關係，確認步驟清晰且無矛盾之處。
