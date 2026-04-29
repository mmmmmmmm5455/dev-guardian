# code-audit — 開源專案程式碼品質與安全審查 (v1.1.0)

自動掃描專案目錄，檢查 8 大類問題，發現問題後提供自動修復，產出結構化審查報告。基於自身 audit 經驗逐步優化。

## 觸發方式

- "audit my project" / "audit <path>"
- "檢查我的專案"
- "code audit <repo>"
- 掃描完成後自動建議

## 8 大檢查類別 (38 項檢查)

### 1. .gitignore 完整性 (11 項)
- 檢查是否存在 .gitignore
- 檢查是否遺漏：`.env`、`*.db`、`*.sqlite`、`__pycache__/`、`*.zip`、`*.tar.gz`、`node_modules/`、`*.log`、`.checkpoints/`
- 檢查 .gitignore 是否損毀（過大、重複行、混入非 gitignore 內容）
- 檢查敏感檔案是否已被 commit（`.env`、`*.db`、`sign_in_data.json`）

### 2. 硬編碼問題 (5 項)
- API Key / Token / 密碼直接寫在程式碼中
- 主機地址硬編碼（`localhost:11434`、`localhost:8765` 等非標準 port）
- `USER_NAME_MAPPING` 等應在 config 中的資料
- Flask `secret_key` / Django `SECRET_KEY` 寫死
- 檢查是否正確使用 `os.environ.get()` / 環境變數

### 3. 重複設定檔與依賴檔案 (3 項)
- 多個 `requirements.txt` 分散在不同目錄
- 多個 config 檔案散落各處
- `pyproject.toml` 與 `requirements.txt` 並存但未統一

### 4. 不該上傳的檔案 (6 項)
- ZIP / tar.gz / 7z / rar 壓縮檔
- `__pycache__/` 目錄
- `.env` 檔案（非 `.env.example`）
- 資料匯出或日誌檔
- 遊戲存檔
- `node_modules/` 目錄

### 5. Git 使用方式 (4 項)
- Commit message 是否清晰有意義（含語意化前綴：feat/fix/docs/chore）
- 是否有大量二進位檔被 commit
- 是否有「傳壓縮包上去」的情況
- 是否只有單一 commit（缺乏開發歷史）

### 6. 敏感資訊洩漏 (6 項)
- GitHub Personal Access Token (`ghp_*`、`github_pat_*`)
- SSH 私鑰 (`-----BEGIN OPENSSH PRIVATE KEY-----`)
- AWS/GCP/Azure 憑證 (`AKIA*`、`ASIA*`)
- 資料庫連線字串含密碼
- Git remote URL 中含 token
- OpenAI/Anthropic 等 API key (`sk-*`、`sk-ant-*`)
- **curl 命令含 Authorization token**（SECRET-006 — v1.1.0 強化：擴展到 .sh/.py/.js/.ts 檔案）

### 7. 前端程式碼品質 (1 項) — v1.1.0 NEW
- HTML `<img>` 缺少 `alt` 屬性（使用 Python HTMLParser 結構化解析，`alt=""` 裝飾性圖片合法）

### 8. 容器/CI 安全性 (2 項) — v1.1.0 NEW
- Dockerfile 使用 root 使用者或未指定 USER（NO_USER_SPECIFIED 與 USER root 同等風險）
- 有 Dockerfile 但缺少 .dockerignore

## 自動修復功能 — v1.1.0 NEW

### AUTO-FIX-001: 自動生成 .gitignore
- **觸發**: GITIGNORE-001 返回 MISSING
- **執行**: `python checks/auto_fix_gitignore.py`
- **行為**: 偵測專案類型（Python/Node/Go/Rust），生成對應 `.gitignore.proposed`
- **回退**: 生成提議檔，由使用者確認後改名為 `.gitignore`

### AUTO-FIX-002: 自動提取硬編碼值到 .env
- **觸發**: HARDCODE-001/002/003 任一命中
- **執行**: `python checks/auto_fix_hardcode.py`
- **行為**: 掃描硬編碼的 API key/密碼/secret_key，提取到 `.env.example`，提示替換語法
- **回退**: 不修改原始碼——只建立 .env.example 並輸出替換指引

## 執行流程

### Phase 1: 快速掃描
1. 讀取 `audit_checklist.json` 獲取檢查項目 (38 項)
2. 對每個檢查項目執行 `check_command`
3. 對每個匹配，使用 regex 提取具體位置

### Phase 2: 深度掃描
1. 逐檔案掃描（排除 .gitignore 中的檔案）
2. 對每個原始碼檔案執行敏感資訊 regex
3. 檢查 git log 找可疑 commit
4. 檢查 git remote URL 是否含 token

### Phase 3: 報告生成
1. 使用 `report_template.md` 格式
2. 每個問題必須包含：專案名稱、類別、檔案路徑、行號、描述、建議
3. 同時輸出 Markdown + JSON
4. 問題按嚴重度分組：Critical → High → Medium → Low
5. 標記「可自動修復」或「需手動處理」

### Phase 4: 自動修復 — v1.1.0 NEW
1. 偵測觸發條件（MISSING .gitignore、硬編碼密鑰）
2. 執行對應的 auto_fix 腳本
3. 修復後自動重新執行相關檢查以驗證
4. 需手動確認的變更（如原始碼替換）輸出明確指引

### Phase 5: 自我進化
1. 將新發現的問題模式加入 `known_issues.json`
2. 更新問題出現次數
3. 若發現新的正則表達式模式，加入 `audit_checklist.json`

## 輸出

- Markdown 報告：`<project>/CODE_AUDIT_REPORT.md`
- JSON 報告：`<project>/audit_report.json`
- 更新後的 `known_issues.json`
- **v1.1.0 自動修復輸出**: `.gitignore.proposed`、`.env.example`

## 約束

- **預設不修改被檢查的檔案**（自動修復僅在使用者確認後執行）
- 自動修復腳本生成提議檔（`.proposed`、`.example`），不直接覆寫
- **每個問題必須有具體檔案路徑和行號**
- **不跳過任何檢查類別**
- **不推送任何東西**
- **不刪除任何檔案**
- 發現 token/密碼時，在報告中遮蔽部分內容（只顯示前 4 字元），不在終端輸出完整 token
