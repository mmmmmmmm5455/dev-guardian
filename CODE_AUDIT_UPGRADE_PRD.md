# CODE_AUDIT Upgrade PRD — v1.0.1 → v2.0.0

> **撰寫日期**: 2026-04-30
> **基於**: skill-tester 測試結果 + P8 內部審查
> **目標**: 將 code-audit 從「檢查工具」升級為「診斷→修復→驗證→報告」完整的程式碼品質生態系統

---

## 1. 現狀分析

### 1.1 目前覆蓋範圍

code-audit v1.0.1 有 35 項檢查，分為 6 大類別：

| 類別 | 檢查數 | 覆蓋範圍 |
|------|--------|----------|
| .gitignore 完整性 | 11 | .env, *.db, __pycache__, *.zip, node_modules, *.log, .checkpoints |
| 硬編碼問題 | 5 | API key, 密碼, Flask secret_key, localhost port, USER_NAME_MAPPING |
| 重複設定檔 | 3 | requirements.txt, pyproject.toml, config 散落 |
| 不該上傳的檔案 | 6 | ZIP, __pycache__, 日誌, 存檔, node_modules, .env.sh |
| Git 使用方式 | 4 | 單一 commit, commit message, 二進位檔, remote URL token |
| 敏感資訊洩漏 | 6 | GitHub PAT (classic+fine-grained), SSH key, AWS key, API key, 資料庫密碼, curl token |

### 1.2 skill-tester 測試發現

| 測試 | 結果 | 發現 |
|------|------|------|
| 結構驗證 | PASS | SKILL.md 格式完整，5 個必要檔案齊全 |
| 觸發測試 | PASS | 4 組觸發關鍵字有效，無衝突 |
| 功能測試 | PASS (1 issue) | 對 multi-agent-plan 執行檢查：發現 `.checkpoints/` 未被根 .gitignore 覆蓋 |
| 品質評估 | **79/100** | 清晰度 16/20, 準確性 22/25, 精簡度 17/20, 錯誤處理 8/15, 可用性 16/20 |
| 依賴檢查 | PASS | 所有 check_command 依賴的 CLI 工具可用 (grep, find, git, wc) |

### 1.3 被遺漏的常見問題

以下 Vibe Coding 問題完全未被現有檢查覆蓋：

| 遺漏領域 | 問題範例 | 影響 |
|----------|----------|------|
| 程式碼品質 | 未使用 import、dead code、裸 except | 安全性/效能 |
| 前端問題 | 缺少 alt、console.log 殘留、無障礙 | 可用性/SEO |
| 語言特定 | Python mutable default args、JS var 使用 | 正確性 |
| 容器/CI | Dockerfile root 使用者、缺少 .dockerignore | 安全性 |
| 授權 | 缺少 LICENSE | 法律風險 |
| 大型檔案 | >10MB 二進位檔直接 commit | 儲存庫膨脹 |
| 套件衝突 | requirements.txt vs pyproject.toml 版本不一致 | 建置失敗 |
| 設定檔錯誤 | JSON/YAML 語法錯誤 | 執行時期 crash |

---

## 2. 新增檢查項目（10 項）

### 2.1 LINT-001: 未使用的 Python import
- **id**: `LINT-001`
- **category**: `lint`
- **name**: 未使用的 Python import
- **severity**: `medium`
- **check_command**: `grep -rn '^import \|^from ' --include='*.py' . 2>/dev/null | sed 's/:#.*//' | sort | uniq -c | grep '^\s*1' | head -5 || echo OK`
- **regex**: N/A（靜態分析）
- **fix_suggestion**: 移除未使用的 import，使用 `autoflake --remove-all-unused-imports` 或 `ruff check --fix`

### 2.2 LINT-002: 裸 except（Python）
- **id**: `LINT-002`
- **category**: `lint`
- **name**: Python 裸 except（無例外類型）
- **severity**: `high`
- **check_command**: `grep -rn 'except:' --include='*.py' . 2>/dev/null | grep -v 'except Exception' | grep -v '# noqa' || echo PASS`
- **regex**: `except\s*:`
- **fix_suggestion**: 改為 `except Exception:` 或具體例外類型

### 2.3 LINT-003: Python mutable default arguments
- **id**: `LINT-003`
- **category**: `lint`
- **name**: Python mutable default arguments
- **severity**: `high`
- **check_command**: `grep -rnE 'def \w+\([^)]*=\s*[\[\{]' --include='*.py' . 2>/dev/null || echo PASS`
- **regex**: `def \w+\([^)]*=\s*[\[\{]`
- **fix_suggestion**: 改用 `None` 作為 default，在函數體內初始化

### 2.4 LINT-004: JavaScript `var` 使用
- **id**: `LINT-004`
- **category**: `lint`
- **name**: JavaScript var 使用（應改用 let/const）
- **severity**: `medium`
- **check_command**: `grep -rnE '\bvar\s+\w+\s*=' --include='*.js' --include='*.ts' . 2>/dev/null | grep -v 'node_modules/' | head -10 || echo PASS`
- **regex**: `\bvar\s+\w+\s*=`
- **fix_suggestion**: `var` → `let`（可變）或 `const`（不可變）

### 2.5 LINT-005: JavaScript `==` 使用
- **id**: `LINT-005`
- **category**: `lint`
- **name**: JavaScript == 使用（應改用 ===）
- **severity**: `medium`
- **check_command**: `grep -rnE '[^=!]==[^=]' --include='*.js' --include='*.ts' . 2>/dev/null | grep -v 'node_modules/' | head -10 || echo PASS`
- **regex**: `[^=!]==[^=]`
- **fix_suggestion**: `==` → `===`，`!=` → `!==`（避免型別強制轉換）

### 2.6 FRONTEND-001: 缺少 img alt 屬性
- **id**: `FRONTEND-001`
- **category**: `frontend`
- **name**: HTML img 缺少 alt 屬性（使用 HTML parser，非 regex）
- **severity**: `medium`
- **check_command**: `python -c "from html.parser import HTMLParser; import sys,glob; class AltCheck(HTMLParser): pass" 2>/dev/null && echo PARSER_READY || echo NO_PARSER`
- **regex**: N/A（使用 Python HTMLParser 結構化解析；對 `<img>` 檢查 alt 屬性存在性；`alt=""` 對裝飾性圖片合法→PASS；完全缺少 alt→FAIL）
- **fix_suggestion**: 加入 `alt="描述性文字"` 屬性；若為純裝飾性圖片，使用 `alt=""` 並加入 `role="presentation"`

### 2.7 FRONTEND-002: console.log 殘留
- **id**: `FRONTEND-002`
- **category**: `frontend`
- **name**: console.log 殘留在生產程式碼中
- **severity**: `low`
- **check_command**: `grep -rn 'console\.\(log\|debug\|warn\)' --include='*.js' --include='*.ts' --include='*.jsx' --include='*.tsx' . 2>/dev/null | grep -v 'node_modules/' | grep -v '\.test\.' | grep -v '\.spec\.' | head -10 || echo PASS`
- **regex**: `console\.(log|debug|warn)`
- **fix_suggestion**: 移除或改用正式的 logging 機制

### 2.8 CONTAINER-001: Dockerfile 中的 root 使用者
- **id**: `CONTAINER-001`
- **category**: `container`
- **name**: Dockerfile 使用 root 使用者
- **severity**: `high`
- **check_command**: `test -f Dockerfile && (grep -qiE '^USER root|^USER 0' Dockerfile 2>/dev/null && echo "ROOT_USER" || (grep -q '^USER ' Dockerfile 2>/dev/null && echo "PASS" || echo "NO_USER_SPECIFIED")) || echo "NO_DOCKERFILE"`
- **regex**: `^USER (root|0)`
- **fix_suggestion**: 加入 `RUN adduser --disabled-password appuser` 並在 Dockerfile 末加入 `USER appuser`

### 2.9 CONTAINER-002: 缺少 .dockerignore
- **id**: `CONTAINER-002`
- **category**: `container`
- **name**: 有 Dockerfile 但缺少 .dockerignore
- **severity**: `medium`
- **check_command**: `test -f Dockerfile && (test -f .dockerignore && echo PASS || echo MISSING) || echo NO_DOCKERFILE`
- **fix_suggestion**: 建立 .dockerignore，排除 node_modules、.git、__pycache__、*.log

### 2.10 LICENSE-001: 缺少 LICENSE 檔案
- **id**: `LICENSE-001`
- **category**: `license`
- **name**: 缺少 LICENSE 檔案
- **severity**: `high`
- **check_command**: `ls LICENSE* LICENCE* COPYING* 2>/dev/null | head -1 || echo MISSING`
- **fix_suggestion**: 加入 LICENSE 檔案（MIT/Apache 2.0/GPL；GitHub 可自動生成）

---

## 3. 自動修復功能

### 3.1 自動生成 .gitignore（AUTO-FIX-001）
- **觸發條件**: GITIGNORE-001 返回 MISSING
- **執行動作**: 基於專案語言偵測（Python/Node/Go/Rust），生成對應的 .gitignore 模板
- **回退機制**: 生成 `.gitignore.proposed`，由使用者確認後改名

### 3.2 自動將硬編碼值提取到 .env（AUTO-FIX-002）
- **觸發條件**: HARDCODE-001/002/003 任一命中
- **執行動作**: 建立 `.env.example`，將硬編碼值替換為 `os.environ.get('KEY')` 或 `process.env.KEY`
- **回退機制**: 原始檔案備份為 `<filename>.bak`；不修改 `.env` 檔案內容（只改程式碼）

### 3.3 自動清理不該上傳的檔案（AUTO-FIX-003）
- **觸發條件**: FILE-001 到 FILE-006 任一命中
- **執行動作**: `git rm --cached <file>` 移出追蹤，加入 .gitignore
- **回退機制**: 檔案仍在本地；重新 commit 即可還原

### 3.4 自動修正常見 JSON/YAML 語法錯誤（AUTO-FIX-004）
- **觸發條件**: 新增 JSON/YAML 語法驗證檢查（LINT-006）返回 ERROR
- **執行動作**: 對 JSON 使用 `python -m json.tool` 嘗試格式化；對 YAML 使用 `yaml.safe_load` 驗證
- **回退機制**: 備份原始檔案；只在語法確定可修復時才修改

### 3.5 自動格式化 commit message（AUTO-FIX-005）
- **觸發條件**: GIT-002 返回無語意化前綴
- **執行動作**: 分析 commit 內容，建議合適前綴（feat/fix/docs/chore），提供 `git commit --amend` 指令
- **回退機制**: 不自動執行 amend——只提供建議指令

---

## 4. 報告增強

### 4.1 視覺化摘要
- 加入 ASCII 儀表板：通過/失敗數量、嚴重度分布柱狀圖
- 用顏色標記：紅色 Critical、黃色 High、藍色 Medium、灰色 Low
- 加入「上次審查 vs 本次審查」對比圖

### 4.2 修復優先級排序
- 自動按嚴重度分組：Critical → High → Medium → Low
- 每個問題標記「可自動修復」或「需手動處理」
- 預估修復時間（分鐘）

### 4.3 「快速修復」區塊
- 彙總所有可自動修復的問題
- 提供「一鍵修復」選項（由使用者確認後執行 AUTO-FIX-001 到 AUTO-FIX-005）
- 修復後自動重新執行相關檢查以驗證

### 4.4 歷史追蹤
- 在審查報告中加入「上次審查日期」與 delta
- 追蹤每個問題類別的趨勢（改善/惡化/持平）
- 將每次審查結果存入 `audit_history.jsonl`

---

## 5. 自我進化機制增強

### 5.1 自動學習新問題模式
- 每次審查後，將新發現的問題自動加入 `known_issues.json` 的 `patterns` 中
- 使用 AI 自動生成 regex 和 check_command
- 連續 3 次出現的 mode 自動提升為 `audit_checklist.json` 的正式檢查項目

### 5.2 從 GitHub Issues/PR 學習
- 定期掃描 GitHub Issues 中標記為 bug 或 security 的問題
- 從 PR discussions 中提取常見的 code review 意見
- 將模式抽象化並加入 `known_issues.json`

### 5.3 定期自動更新
- 每 7 天檢查是否有新的常見問題模式需要加入
- 使用 `skill-tester` 自我驗證：檢查更新後的 code-audit 是否仍正確運作
- 版本自動遞增（patch → minor → major 基於變更程度）

---

## 6. 技能整合

### 6.1 應嵌入 SKILL.md 的技能
| 技能 | 整合方式 | 價值 |
|------|----------|------|
| caveman | 輸出模式 | 讓審查報告更精簡，減少 60-70% token |
| gstack-guard | 品質門檻 | 審查結果自動通過品質門檻檢查 |
| gstack-review | 程式碼審查 | 對發現的問題進行更深層的 code review |

### 6.2 應動態調用的技能
| 技能 | 觸發時機 | 價值 |
|------|----------|------|
| skill-tester | 每次 code-audit 自我更新後 | 驗證更新沒有破壞現有功能 |
| skill-discovery | 需要搜尋修復方案時 | 尋找能幫助修復的技能 |
| prd-writer | 需要產生升級 PRD 時 | 結構化升級規劃 |

### 6.3 協同工作流程
```
使用者觸發 code-audit
  → code-audit 執行掃描
  → gstack-guard 檢查掃描結果品質
  → 報告生成（caveman 壓縮）
  → 可選：skill-tester 自我驗證
  → 可選：gstack-review 對發現的問題進行 deeper review
```

---

## 7. 使用者體驗

### 7.1 更容易觸發
- **目前**: 需輸入 "audit my project" 或 "檢查我的專案"
- **改善**: 
  - 加入 `/audit` 作為快捷指令
  - 在每次 `git commit` 後自動提示是否要審查
  - 提供 GitHub Action 整合（`code-audit-action`）

### 7.2 更容易閱讀
- **目前**: Markdown 報告（.md）
- **改善**:
  - 保留 Markdown（終端機最易讀）
  - 同時產出 JSON（供 CI 整合）
  - 加入簡短的一行摘要（"3 critical, 5 high, 12 medium — 8 auto-fixable"）

### 7.3 更容易修復
- **目前**: 報告中提供 fix_suggestion，但需手動執行
- **改善**:
  - 互動式模式：逐項詢問是否要自動修復
  - 批次模式：一次修復所有可自動修復的問題
  - PR 模式：自動建立 PR 來修復所有問題

---

## 8. 實施評估

| 功能 | 難度 | 預估時間 | 優先級 | 本次升級 |
|------|------|----------|--------|----------|
| 10 項新檢查 (LINT-001~005, FRONTEND-001~002, CONTAINER-001~002, LICENSE-001) | easy | 2h | P0 | ✅ |
| 自動修復 .gitignore (AUTO-FIX-001) | easy | 1h | P0 | ✅ |
| 自動提取硬編碼到 .env (AUTO-FIX-002) | medium | 3h | P0 | ✅ |
| 自動清理檔案 (AUTO-FIX-003) | easy | 1h | P0 | ✅ |
| JSON/YAML 自動修復 (AUTO-FIX-004) | medium | 2h | P1 | ✅ |
| 自動格式化 commit message (AUTO-FIX-005) | easy | 1h | P1 | ⏳ |
| 視覺化摘要 | easy | 2h | P1 | ✅ |
| 修復優先級排序 | easy | 1h | P1 | ✅ |
| 快速修復區塊 | medium | 2h | P1 | ⏳ |
| 歷史追蹤 (audit_history.jsonl) | medium | 2h | P2 | ⏳ |
| 自動學習新問題模式 | hard | 5h | P2 | ❌ |
| GitHub Issues/PR 學習 | hard | 8h | P2 | ❌ |
| 定期自動更新 | medium | 3h | P2 | ❌ |
| 技能協同工作流程 | medium | 3h | P1 | ⏳ |
| GitHub Action 整合 | medium | 4h | P2 | ❌ |
| 互動式修復模式 | medium | 3h | P2 | ❌ |

**總預估**: P0+P1 項目約 18h；完整 v2.0.0 約 42h

---

## 9. 附錄：技能對齊審查

| 技能 | 當前狀態 | 對齊度 | 差距 | 補償措施 |
|------|----------|--------|------|----------|
| caveman | ACTIVE | HIGH | 無 | 直接使用——嵌入 SKILL.md 的輸出模式 |
| pua | **MISSING** | HIGH | 不存在於本地 | 從 GitHub (`tanweai/pua`) 拉取或手動建立 |
| gstack-review | ACTIVE | HIGH | 無 | 直接使用 |
| gstack-guard | ACTIVE | HIGH | 無 | 直接使用 |
| gstack-qa | ACTIVE | MEDIUM | 需要客製化以適應 code-audit 輸出格式 | 建立適配層 |
| skill-tester | ACTIVE (剛建立) | HIGH | 無 | 直接使用 |
| skill-discovery | ACTIVE | MEDIUM | 技能修復方案搜尋能力未充分使用 | 在 AUTO-FIX 流程中調用 |
| prd-writer | ACTIVE | MEDIUM | 僅在升級時使用 | 按需調用 |
| CLI-Anything | MISSING | LOW | 不存在，但 code-audit 的 check_commands 已足夠 | 不需要優先拉取 |
| prompt-optimizer | MISSING | LOW | 不存在 | 低優先級——code-audit 的 prompt 不複雜 |
| page-agent | MISSING | LOW | 不存在 | 低優先級——code-audit 不需要瀏覽器 |

---

*PRD 由 skill-tester v1.0.0 測試結果驅動撰寫 | 等待使用者審核後實施*
