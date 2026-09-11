# CODEBASE FORENSIC AUDIT — MASTER RULES

> Every audit subagent MUST obey these rules. They are derived verbatim from
> `CODEBASE_AUDIT_BY_ASHER.md`. This is a **forensic, evidence-based, skeptical**
> audit of the Zozi e-commerce platform. Determine what the application **IS**,
> not what it was intended to be.

## ABSOLUTE RULES

1. NEVER assume a technology, library, package, architecture, feature, security
   mechanism, database behavior, API, or configuration exists unless you can
   prove it from the repository.
2. NEVER infer implementation details from: folder names alone, README files
   alone, package names alone, comments alone, variable names alone, or
   documentation alone.
3. Every important finding MUST contain evidence: file path, line number/range
   whenever possible, and the relevant symbol/function/class/config name.
4. Clearly distinguish:
   - **VERIFIED** — directly confirmed from source/configuration
   - **INFERRED** — strongly suggested but not directly confirmed
   - **UNKNOWN** — insufficient evidence
5. Do NOT invent missing information.
6. If something cannot be determined, explicitly write:
   `NOT DETERMINABLE FROM AVAILABLE CODE.`
7. Do not recommend migration/rewriting during forensic phases (1–16).
8. Do not judge code quality merely because it uses an older technology.
9. Do not recommend replacing a technology simply because a newer one exists.
10. Identify contradictions between source, config, manifests, DB models, API
    definitions, deployment config, and documentation.
11. Never silently resolve contradictions. Report them.
12. An unused dependency is NOT proof the library is used.
13. An imported library is NOT proof its functionality is meaningfully used.
14. Trace important functionality through actual call paths whenever possible.
15. For security findings distinguish: confirmed vulnerability / security
    weakness / potential risk requiring verification.
16. For production-readiness findings distinguish: blocking / high / medium /
    low / informational.
17. **Do NOT modify any file in the codebase under audit.** The ONLY files you
    may create/write are your own report under `_audit/`.
18. Do not execute destructive commands.
19. Do not expose or reproduce secrets, API keys, passwords, tokens, private
    keys, payment credentials, or PII. Report their existence and location
    WITHOUT revealing the secret value.

## EVIDENCE STANDARD (use for every major conclusion)

```
Finding:
Status: VERIFIED / INFERRED / UNKNOWN
Evidence: <file path : line(s)>
Files:
Symbols:
Impact:
Confidence: High / Medium / Low
```

If evidence is insufficient, say so.

## SKEPTICISM CHECKLIST (self-verify before finalizing)

- [ ] Did I open the actual file and cite real line numbers (not guesses)?
- [ ] Did I distinguish application-level checks from framework/DB-level enforcement?
- [ ] Did I separate "declared/imported" from "actually used"?
- [ ] Did I label every claim VERIFIED / INFERRED / UNKNOWN?
- [ ] Did I avoid inferring behavior from names/docs alone?
- [ ] Did I report contradictions instead of resolving them silently?
- [ ] Did I avoid exposing any secret values?

## MANDATORY OUTPUT: LOGGING CONTRACT

At the END of your returned message (and at the top of your report file),
include this exact structured block so the orchestrator can log your run:

```
=== AGENT LOG ===
PHASE: <NN — name>
STATUS: COMPLETED | PARTIAL | BLOCKED
REPORT_FILE: _audit/findings/PHASE_XX_....md
SCOPE_COVERED: <what you examined>
FILES_EXAMINED: <approx count>
EVIDENCE_ITEMS: <count of file:line citations>
FINDINGS_TOTAL: <n>  (VERIFIED: x / INFERRED: y / UNKNOWN: z)
SEVERITY_BREAKDOWN: BLOCKER: a / HIGH: b / MEDIUM: c / LOW: d / INFO: e
TOP_FINDINGS:
  1. <finding> — <file:line>
  2. ...
GAPS / NOT DETERMINABLE: <list>
SELF_SKEPTICISM_RATING: <1-5, 5 = fully evidence-backed>
=== END AGENT LOG ===
```
