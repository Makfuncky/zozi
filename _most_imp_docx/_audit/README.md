# Zozi Codebase Forensic Audit — `_audit/`

This directory contains a **forensic, evidence-based, skeptical** audit of the
Zozi e-commerce platform, executed against `CODEBASE_AUDIT_BY_ASHER.md`.

## Contents

| Path | Purpose |
|------|---------|
| `MASTER_RULES.md` | The forensic rules every audit subagent must obey |
| `AUDIT_PLAN.md` | Phase → report → wave mapping and orchestration model |
| `findings/` | One detailed report per phase (18 total) |
| `_logs/AUDIT_LOG.md` | Chronological log of every subagent run + skeptical review |
| `_logs/agent-tracking.json` | Machine-readable agent performance tracking |
| `EXECUTIVE_SUMMARY.md` | Final consolidated findings (written last) |

## Method

18 narrow-scope forensic subagents examine the actual source (not docs), cite
`file:line` evidence, and label every claim **VERIFIED / INFERRED / UNKNOWN**.
Subagents are read-only on the codebase and only write their own report here.
The orchestrator logs and skeptically reviews each run.

## Status

See `_logs/AUDIT_LOG.md` for live progress.
