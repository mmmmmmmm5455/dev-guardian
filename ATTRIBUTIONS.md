# Attributions

This project builds on open-source work. Each dependency is acknowledged below.

## Direct Dependencies

### pua — P8 Pressure-Driven Programming
- **Repository**: https://github.com/tanweai/pua
- **License**: MIT
- **Author**: 探微安全实验室 (Tanwei Security Lab)
- **Usage**: skill-tester's Agent 2 uses pua for P8 high-standard quality judgment. Agent 3 uses pua for relentless root-cause diagnosis.
- **Version used**: v3.2.3

### gstack — Engineering Quality Framework
- **Repository**: https://github.com/garry/gstack (via Claude Code skill ecosystem)
- **License**: MIT
- **Skills used**:
  - `gstack-review` — structured code/design review for Agent 2 quality assessment
  - `gstack-guard` — quality gates preventing broken fixes from shipping
  - `gstack-qa` — test strategy and quality measurement patterns

### caveman — Minimalist Output Convention
- **Origin**: Claude Code skill ecosystem
- **Usage**: All 3 skill-tester agents use caveman style for concise, no-fluff output. code-audit reports follow caveman principles.

## Design Inspiration

### Vibe Coding Problem Patterns
The 38 checks in code-audit are derived from real-world Vibe Coding anti-patterns observed in:
- GitHub repositories with leaked credentials
- Claude Code session transcripts with embedded tokens
- Dockerfiles running as root in production
- Frontend code with missing accessibility attributes
- Multi-agent pipeline output directories committed to version control

### skill-tester Architecture
The 3-agent pipeline (Discovery → Execution → Repair) is inspired by:
- CI/CD quality gates (build → test → deploy)
- Medical diagnosis workflow (scan → diagnose → treat)
- The self-referential principle: a skill-testing skill must itself be testable

## License

This project is licensed under the MIT License. See individual skill directories for third-party license details.
