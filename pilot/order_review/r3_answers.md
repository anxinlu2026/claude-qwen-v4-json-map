## 問 1
1. 你會執行的前六個指令是什麼(寫出指令本身,含 rtl show 的參數)?

## 答 1(5s)
1. `cp /tmp/pilot/skeleton_c2_from.md /tmp/deliveries/load_block_c2_from.md`
2. `cat /tmp/deliveries/load_block_c1_to.md`
3. `python3 -c "import json;b=[x for x in json.load(open('/tmp/pilot/model_dp.json'))['blocks'] if x['id']=='load_block'][0];print(json.dumps({k:b[k] for k in ('upstream_blocks','ports_detail')},ensure_ascii=False,indent=1))"`
4. `rtl show rtl/aes128_decrypt.sv 1 140`
5. `cat /tmp/pilot/rtl_structure.json`
6. `rtl probe load_block --to 260`

## 問 2
2. 情境 C:rtl probe --to 40 沒有 i_start=1 且 o_done=1 的那一列。你下一個指令是什麼?如果擴大後仍然沒有,文件怎麼寫?

## 答 2(3s)
下一個指令是執行 `rtl probe load_block --to 260` 以擴大探測時間範圍。

如果擴大後仍然找不到該訊號，需在文件的「依據」欄位寫明「探測不到該方塊工作」，並具體說明已檢視過哪些時間區間或訊號列。

同時必須將此情況記錄為一條假設，說明無法取得該方塊實際運作時的訊號證據。

## 問 3
3. 情境 F:架構的 i_data 寬度 128,RTL 的 i_data 寬度 128,但有效條件不同,你的「結果」欄寫 different 還是 unknown?為什麼?

## 答 3(2s)
結果欄應寫 different。
因為工單明確規定，只要任一屬性（包含有效條件）不同，就必須判定為 different。
兩側資料均已取得且存在差異時，不適用 unknown 的定義。
