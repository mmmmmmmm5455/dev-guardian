# code-audit-suite

Claude Code 技能品质生态系统：代码审计 + 技能测试 + 自动修复。

## 包含的技能

### code-audit (v1.1.0)
38 项检查 · 8 大类 · 2 项自动修复

扫描项目发现安全漏洞、硬编码密钥、缺失的 .gitignore 条目、Git 不良实践、前端可访问性问题以及容器安全风险。发现问题后自动修复。

```
audit my project
```

### skill-tester (v1.0.0)
3 Agent · 6 JSON Schema · 1 Orchestrator

通用 Claude Code 技能验证框架。Agent 1 发现并验证结构。Agent 2 执行并评分质量。Agent 3 诊断并自动修复。

```
test skill <name>
```

## 快速开始

```bash
# 安装技能到 Claude Code
cp -r code-audit ~/.claude/skills/code-audit
cp -r skill-tester ~/.claude/skills/skill-tester

# 审计当前项目
# （在 Claude Code 中输入）: audit my project

# 测试一个技能
# （在 Claude Code 中输入）: test skill code-audit
```

## 仓库结构

```
code-audit-suite/
├── code-audit/              # 代码审计技能 (v1.1.0)
│   ├── SKILL.md
│   ├── audit_checklist.json # 38 项检查定义
│   ├── known_issues.json    # 自学习问题数据库
│   └── checks/              # Auto-fix scripts
├── skill-tester/            # 技能测试框架 (v1.0.0)
│   ├── SKILL.md
│   ├── orchestrator.py      # 3-agent pipeline orchestrator
│   ├── prompts/             # Agent 1/2/3 系统提示
│   ├── schemas/             # 6 个 JSON 数据契约
│   └── known_skill_issues.json
├── CODE_AUDIT_UPGRADE_PRD.md # v1.0.1 → v2.0.0 升级规划
├── ATTRIBUTIONS.md           # 开源致谢
└── README.md
```

## 致谢

本项目基于开放源码构建。参见 [ATTRIBUTIONS.md](ATTRIBUTIONS.md)。

## 许可

MIT License。
