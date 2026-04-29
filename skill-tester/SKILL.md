# skill-tester — 通用技能驗證與測試工具

自動化驗證任何 Claude Code 技能的功能完整性、可用性與實用性。產出結構化測試報告，並在發現問題時啟動診斷→修復→驗證→報告工作流程。

## 觸發方式

- "test skill <name>" / "測試技能 <name>"
- "verify skill <name>" / "驗證技能 <name>"
- "skill test <name>"
- "run skill-tester on <name>"
- "test all skills" / "測試所有技能"

## 6 大驗證模組

### 1. 技能存在性與結構驗證
- 檢查技能目錄是否包含必要檔案（SKILL.md、聲明的依賴）
- 驗證 SKILL.md 格式：標題、描述、觸發方式、輸入/輸出規範、使用限制
- 檢查技能是否在 skills/ 或 skills-archive/ 中正確註冊

### 2. 技能可觸發性驗證
- 測試觸發關鍵字是否有效
- 檢查是否與其他技能衝突
- 測試不同輸入情境：正常輸入、邊界輸入、無效輸入

### 3. 技能功能完整性測試
- 根據 SKILL.md 宣稱的功能設計對應測試案例
- 實際執行技能，觀察產出
- 驗證產出是否符合 SKILL.md 中宣稱的功能
- 測量 token 消耗（輸入/輸出/總計）

### 4. 技能品質評估（0-100 分）
- 輸出清晰度（20 分）：輸出是否清晰、可操作、無冗餘
- 準確性（25 分）：輸出是否正確、無誤導、無幻覺
- 精簡度（20 分）：遵循 Caveman 精簡原則，無多餘 token
- 錯誤處理（15 分）：適當的錯誤處理和邊界情況處理
- 可用性（20 分）：使用者是否容易理解和使用

### 5. 技能依賴檢查
- 檢查聲明的依賴（工具、套件、其他技能）是否可用
- 驗證依賴版本相容性
- 嘗試自動安裝缺失的依賴

### 6. 技能自我進化能力評估
- 檢查是否有自我改進機制（known_issues.json、evolution_log 等）
- 評估學習新問題模式的能力
- 檢查定期更新檢查清單的機制

## 測試工作流程（8 Steps）

對每個被測試的技能，嚴格遵循：

```
Step 1: 技能發現 → 定位技能目錄，讀取 SKILL.md，解析名稱/描述/觸發方式/輸入輸出
Step 2: 結構驗證 → 檢查必要檔案、格式、註冊狀態；缺失→STRUCTURE_ERROR
Step 3: 觸發測試 → 使用定義的觸發關鍵字觸發技能；無法觸發→TRIGGER_ERROR
Step 4: 功能測試 → 設計最小測試案例，執行技能，比較輸出；偏差→FUNCTION_ERROR
Step 5: 品質評估 → 分析輸出品質、token 消耗、錯誤處理，給出 0-100 分
Step 6: 依賴驗證 → 檢查所有聲明依賴；無法安裝→DEPENDENCY_ERROR
Step 7: 報告生成 → 產出結構化 JSON + Markdown 測試報告
Step 8: 自我進化 → 新問題模式加入 known_skill_issues.json；可自動修復→觸發修復
```

## 3 個 Agent

### Agent 1: Skill Discovery & Structure Agent
- **角色名稱**: skill-discovery-agent
- **職責**: 掃描技能目錄，建立技能清單，執行結構與格式驗證
- **指派技能**: caveman（精簡輸出）、CLI-Anything（CLI 封裝）
- **依賴**: 無（入口 Agent）
- **輸入**: `schemas/agent1_input.json`
- **輸出**: `schemas/agent1_output.json`

### Agent 2: Skill Execution & Quality Agent
- **角色名稱**: skill-execution-agent
- **職責**: 根據 Agent 1 清單，實際執行技能，設計測試案例，評估輸出品質
- **指派技能**: pua（P8 評判）、gstack-review（審查）、caveman（精簡輸出）
- **依賴**: Agent 1
- **輸入**: `schemas/agent2_input.json`
- **輸出**: `schemas/agent2_output.json`

### Agent 3: Skill Repair & Evolution Agent
- **角色名稱**: skill-repair-agent
- **職責**: 讀取 Agent 2 問題清單，診斷根因，自動修復，更新 known_skill_issues.json
- **指派技能**: skill-discovery（搜尋修復方案）、gstack-guard（品質門檻）、caveman（精簡輸出）
- **依賴**: Agent 2
- **輸入**: `schemas/agent3_input.json`
- **輸出**: `schemas/agent3_output.json`

## 輸出

- JSON 報告：`<skill-tester-output>/<skill_name>_test_report.json`
- Markdown 報告：`<skill-tester-output>/<skill_name>_test_report.md`
- 更新後的 `known_skill_issues.json`

## 約束

- **不修改被測試的技能檔案**（除非在 Agent 3 修復階段且問題可自動修復）
- **每個測試步驟必須有明確的通過/失敗狀態**
- **不跳過任何測試步驟**
- **不使用空洞詞彙**（"很棒"、"有潛力"、"不錯"）
- **品質分數必須有具體扣分原因**
- **每個 FUNCTION_ERROR 必須包含 expected vs actual 的比較**
- **token 消耗必須被估算並分類為 good/warning/wasteful**
