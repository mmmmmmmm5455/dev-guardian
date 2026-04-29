# {{SKILL_NAME}} — 技能測試報告

> **測試日期：** {{TEST_DATE}}
> **測試工具：** skill-tester v{{VERSION}}
> **測試範圍：** {{SCOPE_PATH}}

---

## 總覽

| 指標 | 結果 |
|------|------|
| 整體狀態 | {{OVERALL_STATUS}} |
| 品質分數 | {{QUALITY_SCORE}}/100 |
| 結構驗證 | {{STRUCTURE_STATUS}} |
| 觸發測試 | {{TRIGGER_STATUS}} |
| 功能測試 | {{FUNCTION_STATUS}} |
| 依賴驗證 | {{DEPENDENCY_STATUS}} |
| Token 效率 | {{TOKEN_EFFICIENCY}} |

---

## 1. 結構驗證

| 檢查項 | 狀態 | 詳情 |
|--------|------|------|
| SKILL.md 存在 | {{STRUCT_SKILLMD}} | {{STRUCT_SKILLMD_DETAIL}} |
| SKILL.md 格式完整 | {{STRUCT_FORMAT}} | {{STRUCT_FORMAT_DETAIL}} |
| 必要檔案齊全 | {{STRUCT_FILES}} | {{STRUCT_FILES_DETAIL}} |
| 技能註冊狀態 | {{STRUCT_REGISTERED}} | {{STRUCT_REGISTERED_DETAIL}} |

## 2. 觸發測試

| 檢查項 | 狀態 | 詳情 |
|--------|------|------|
| 關鍵字有效 | {{TRIGGER_VALID}} | {{TRIGGER_VALID_DETAIL}} |
| 無衝突 | {{TRIGGER_CONFLICT}} | {{TRIGGER_CONFLICT_DETAIL}} |
| 邊界輸入 | {{TRIGGER_EDGE}} | {{TRIGGER_EDGE_DETAIL}} |

## 3. 功能測試

| 檢查項 | 狀態 | 詳情 |
|--------|------|------|
| 測試案例 | {{FUNC_CASE}} | {{FUNC_CASE_DETAIL}} |
| 預期輸出 | {{FUNC_EXPECTED}} | |
| 實際輸出 | {{FUNC_ACTUAL}} | |
| 輸出比較 | {{FUNC_MATCH}} | {{FUNC_MATCH_DETAIL}} |

## 4. 品質評估

| 維度 | 分數 | 評語 |
|------|------|------|
| 輸出清晰度 (20) | {{QUAL_CLARITY}} | {{QUAL_CLARITY_NOTE}} |
| 準確性 (25) | {{QUAL_ACCURACY}} | {{QUAL_ACCURACY_NOTE}} |
| 精簡度 (20) | {{QUAL_CONCISENESS}} | {{QUAL_CONCISENESS_NOTE}} |
| 錯誤處理 (15) | {{QUAL_ERROR}} | {{QUAL_ERROR_NOTE}} |
| 可用性 (20) | {{QUAL_USABILITY}} | {{QUAL_USABILITY_NOTE}} |
| **總分** | **{{QUAL_TOTAL}}** | |

## 5. 依賴驗證

| 依賴 | 類型 | 狀態 | 詳情 |
|------|------|------|------|
{{DEPENDENCY_ROWS}}

## 6. Token 消耗分析

| 指標 | 數值 |
|------|------|
| 輸入 token (估算) | {{TOKEN_INPUT}} |
| 輸出 token (估算) | {{TOKEN_OUTPUT}} |
| 總計 | {{TOKEN_TOTAL}} |
| 效率評級 | {{TOKEN_EFFICIENCY_RATING}} |

## 7. 發現的問題

| 嚴重度 | 類別 | 描述 | 可自動修復 |
|--------|------|------|------------|
{{ISSUES_ROWS}}

## 8. 修復建議

{{REPAIR_SUGGESTIONS}}

---

*報告由 skill-tester v{{VERSION}} 自動生成 | 下次測試將自動套用已知問題模式*
