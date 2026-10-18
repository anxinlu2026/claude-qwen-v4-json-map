# multi-ai v4

AES_0005 除錯的 v4 流程(端口對齊)。計畫見 [PLAN.md](PLAN.md)。

## 目錄
| 路徑 | 內容 |
|---|---|
| `tools/rtl/rtl`、`tools/agentic/` | `rtl` 工具、runner、映像 Dockerfile |
| `skills/`、`image_skills/`、`resources/`、`kickoff/` | 技能、標準與 IP 模型、HDL 開工提示 |
| `roles/` | orchestrator、architecture、HDL 的角色文件 |
| `pilot/` | 架構套件(Python 模型、`model.json`)、工具、工單檢討、設計文件 |
| `pilot_tools/` | 端口填表工具(也烘進映像 `/opt/pilot_tools`) |
| `prepared/` | 已核准任務單、基準 RUN #1、模型已驗證的起始狀態 |
| `seed_run/`、`reference_solution/` | 問題原檔;參考解(只用於 verify) |
| `dashboard/` | `orch.py`(寫看板與決策日誌)、`serve.py`(看板伺服器)、`refresh.py` |
| `scripts/` | `build_image.sh`、`verify.sh`、`make_cell.sh`、`start_runner.sh`、`adv.sh` |

## 使用
```bash
scripts/prepare_seed.sh
scripts/build_image.sh          # multi-ai/cvdp-qwen-agent:0.26.0-v4-ports
scripts/make_cell.sh v4a        # 新 cell
scripts/start_runner.sh runs/<cell> 900
```
需要映像 `multi-ai/cvdp-sim:8e894cf-arm64` 與 `multi-ai/cvdp-qwen-agent:0.25.0`(見 `scripts/build_image.sh`)。

## 看板
```bash
python3 dashboard/serve.py --port 8767     # http://127.0.0.1:8767/ ,讀本 repo 的 runs/
```
看板的 port 若被其他 repo 的舊看板佔用,換一個。看板的工單欄位由檔案自動推得,日誌由 orchestrator 以 `dashboard/orch.py` 寫入。
