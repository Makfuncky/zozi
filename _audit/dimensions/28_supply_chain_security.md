# DIMENSION: Supply Chain Security

## Summary
- Confirmation: ❌
- Files inspected: 18
- Files compliant: 6
- Files with findings: 12
- Laws implicated: [L-44, L-164, L-250, L-290, L-291, L-292, L-293, L-294, L-295]
- Findings: 12
- P0: 2  P1: 3  P2: 5  P3: 2
- Clusters: 4
- Average confidence: 4.4/5
- Average evidence strength: multiple
- Status: NEW: 12 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 2 yes · 3 partial · 7 no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SUP-001 | infra | NEW | CLUSTER-cve-scanning | .github/workflows/security.yml:45-61 | pip-audit scans uv.lock for Python CVEs; npm audit scans frontend/web_app for Node CVEs; Trivy scans filesystem for CRITICAL/HIGH | CVE scanning enforced on every PR/push for all dependency types | COMPLIANT. Three CVE scanners in CI: pip-audit (Python), npm audit (Node), Trivy (container/filesystem). Results block PR merge via security-success gate. | None required. | S | P1 | 5 | multiple | L1 | VERIFIED | SUP-005 | `cat .github/workflows/security.yml | grep -E "pip-audit\|npm audit\|trivy"` | N/A (CI pipeline validation) | N/A | infra | none | none | no |
| SUP-002 | infra | NEW | CLUSTER-sbom-missing | .github/workflows/security.yml:1-342 | No SBOM generation step in security scanning workflow | Syft 1.17.0+ or CycloneDX SBOM generation per TECHNOLOGY_STACK.md §11 | GAP. CI/CD pipelines lack SBOM generation required by canonical stack. No SBOM artifact is produced for any release. | Add Syft SBOM generation step to security.yml and upload artifact | M (3h) | P2 | 4 | single | L0 | VERIFIED | TECH-053, D2P-008, LAW-291 | `grep -r "syft\|cyclonedx\|sbom" .github/workflows/` | tests/test_sbom.py::test_sbom_generated | `git revert <commit>` | Supply chain audit, compliance | none | none | no |
| SUP-003 | infra | NEW | CLUSTER-license-compliance | backend/pyproject.toml:1-18; frontend/package.json:1-6 | No license scanning tool configured (e.g., pip-licenses, license-checker, FOSSA) | All dependencies have compatible licenses; license scan enforced in CI | GAP. No automated license compliance check. Cannot verify that all dependencies have compatible licenses without manual review. | Add license scanning tool (pip-licenses for Python, license-checker for Node) to CI | M (2h) | P2 | 3 | single | L1 | INFERRED | — | `grep -r "license\|pip-licenses\|license-checker" .github/workflows/ .pre-commit-config.yaml` | tests/test_license_compliance.py | Remove license scanner if overhead is too high | Compliance, legal | none | none | no |
| SUP-004 | infra | NEW | CLUSTER-lockfile-integrity | backend/uv.lock:1-2221; frontend/web_app/pnpm-lock.yaml:1-8684 | uv.lock and pnpm-lock.yaml present and pinned; versions in requirements.txt generally match uv.lock | Lockfiles match TECHNOLOGY_STACK.md versions exactly; no drift | PARTIAL. uv.lock is present and used by CI. pnpm-lock.yaml is present. However, requirements.txt has some versions that drift from TECHNOLOGY_STACK.md (e.g., fastapi==0.115.2 vs 0.141.x, starlette unpinned vs >=1.6.0,<1.7.0). | Align requirements.txt with TECHNOLOGY_STACK.md versions; enforce lockfile integrity check in CI | S (1h) | P2 | 4 | multiple | L1 | VERIFIED | TECH-014 | `diff <(grep -E "fastapi|starlette|uvicorn" backend/requirements.txt) <(grep -E "fastapi|starlette|uvicorn" _most_imp_docx/TECHNOLOGY_STACK.md)` | tests/test_lockfile_integrity.py | Revert requirements.txt if drift is intentional | Build reproducibility | none | none | no |
| SUP-005 | infra | NEW | CLUSTER-container-scanning | .github/workflows/security.yml:103-137 | Trivy filesystem scan for CRITICAL/HIGH CVEs; no container image scan in build.yml | Container images scanned for critical/high CVEs before push | PARTIAL. Trivy filesystem scan catches dependencies in the repo but does NOT scan the built container image. build.yml pushes images without scanning. | Add Trivy container image scan to build.yml before push; fail on CRITICAL/HIGH | M (2h) | P1 | 4 | single | L1 | VERIFIED | D2P-013 | `grep -n "trivy" .github/workflows/build.yml` | tests/test_container_scanning.py | Revert Trivy image scan if it blocks legitimate images | Image provenance | none | none | partial |
| SUP-006 | infra | NEW | CLUSTER-image-signing | .github/workflows/build.yml:59-113 | No cosign or image signing step in build workflow | cosign 2.6.3+ used to sign container images per TECHNOLOGY_STACK.md §11 | GAP. Container images are built and pushed to GHCR without any signing or provenance attestation. Consumers cannot verify image integrity. | Add cosign signing step to build.yml after image push; upload .sig artifact | M (2h) | P1 | 4 | single | L0 | VERIFIED | D2P-013, LAW-295 | `grep -n "cosign" .github/workflows/build.yml` | tests/test_image_signing.py | Revert cosign step if signing keys are not available | Image provenance, compliance | none | none | partial |
| SUP-007 | security | NEW | CLUSTER-plaintext-secrets | .env:2; backend/.env:1 | `SECRET_KEY=K1shXALnoZnJzgvaq5DIwh9SWXWPX1YGNi5cY97jjTM2cFN4I9F6jWXVITL9fgKW` in root `.env`; identical key in `backend/.env:1` | No plaintext secrets in working tree; all secrets via Coolify env vars per TECHNOLOGY_STACK.md §5 | EMERGENCY. Real-looking JWT SECRET_KEY stored in unencrypted `.env` files in working tree. Both files contain identical production-looking keys. .gitignore ignores `.env` but files still exist on disk. | Rotate SECRET_KEY immediately; remove `.env` files from working tree; use Coolify env vars exclusively | S (0.5h) | P0 | 5 | multiple | L1 | VERIFIED | backend/.env:1 | `gitleaks detect --source . --report-path gitleaks-local.json` | tests/security/test_no_plaintext_secrets.py | Re-add rotated SECRET_KEY to Coolify if service fails | F-026, CHAIN-006 | none | none | yes |
| SUP-008 | security | NEW | CLUSTER-secrets-in-git | git history | No secrets found in git history; gitleaks configured and running in CI | gitleaks clean on all branches; no secrets in git history | COMPLIANT. No `.env` files were ever committed to git history. gitleaks is configured with .gitleaks.toml and runs in CI. Security gate fails on any finding. | None required. | S | P0 | 5 | multiple | L1 | VERIFIED | SUP-007 | `git log --all --diff-filter=A --name-only --pretty=format: | grep "\.env$"` | N/A | N/A | Audit scope | none | none | no |
| SUP-009 | infra | NEW | CLUSTER-workflow-permissions | .github/workflows/ci.yml:1-264 | No `permissions:` block at workflow top; GitHub defaults GITHUB_TOKEN to read/write contents, packages, etc. | Every workflow must declare least-privilege `permissions:` per security.yml pattern | GAP. ci.yml inherits overly permissive default GITHUB_TOKEN permissions instead of declaring least-privilege. architecture-gate.yml also lacks permissions block. | Add `permissions: contents: read` at top of ci.yml and architecture-gate.yml | S (0.5h) | P1 | 5 | single | L1 | VERIFIED | .github/workflows/security.yml:11 | `cat .github/workflows/ci.yml | head -10` | tests/infrastructure/test_workflow_permissions.py | Remove permissions block if CI breakage occurs | F-027 | none | none | partial |
| SUP-010 | security | NEW | CLUSTER-hardcoded-secrets-workflows | .github/workflows/security.yml:206 | `SECRET_KEY: ci-test-secret-key-not-for-production` hardcoded in workflow env block | Test secrets must come from `${{ secrets.* }}` references, never inline literals | GAP. Hardcoded test secret in workflow file; should use GitHub Secrets. e2e.yml and schema-audit.yml also contain hardcoded test secrets/credentials. | Move test SECRET_KEY to `${{ secrets.TEST_SECRET_KEY }}` reference | S (0.5h) | P2 | 5 | single | L1 | VERIFIED | .github/workflows/e2e.yml:98 | `grep -n "ci-test-secret-key" .github/workflows/security.yml` | tests/security/test_workflow_secrets.py | Revert to inline literal if secret management overhead is too high | F-028 | none | none | no |
| SUP-011 | security | NEW | CLUSTER-dependency-confusion | backend/pyproject.toml:2; frontend/web_app/package.json:2 | `name = "zozi"` — generic unscoped package name on PyPI; `"name": "frontend"` — generic unscoped package name on npm | Internal packages must use scoped names or configure protected index to prevent dependency confusion | GAP. Python package `zozi` and npm packages `zozi` and `frontend` are generic and unprotected. Attacker could publish malicious packages with these names. @zozi/shared is correctly scoped and private. | Rename root package.json to `@zozi/root`; rename pyproject.toml to scoped name or configure private index; publish `zozi` on PyPI/npm to squat names | M (2h) | P2 | 4 | single | L1 | VERIFIED | frontend/shared/package.json:2 | `pip index versions zozi 2>/dev/null || echo "Package not on PyPI — vulnerable"` | tests/security/test_dependency_confusion.py | Revert package name if scope migration breaks imports | F-031 | none | none | no |
| SUP-012 | infra | NEW | CLUSTER-precommit-supply-chain | .pre-commit-config.yaml:1-71 | Pre-commit hooks enforce ruff, mypy, import-linter, gitleaks, pip-audit, and black | Local supply chain gate before code reaches CI | COMPLIANT. Pre-commit config includes ruff (lint/format), mypy (type check), import-linter (architecture), gitleaks (secrets), pip-audit (CVE scan), and black (format). Fast local gate. | None required. | S | P0 | 5 | multiple | L1 | VERIFIED | — | `cat .pre-commit-config.yaml | grep -E "ruff|mypy|import-linter|gitleaks|pip-audit"` | N/A (local hook validation) | N/A | Local dev experience | none | none | no |

## Overall

### Problem(s)
1. No SBOM generation in CI/CD, preventing supply chain component inventory verification (SUP-002).
2. No container image scanning in build.yml; images pushed to GHCR without vulnerability checks (SUP-005).
3. No container image signing with cosign; images lack provenance attestation (SUP-006).
4. `.env` and `backend/.env` contain plaintext SECRET_KEY in working tree (SUP-007).
5. `ci.yml` and `architecture-gate.yml` lack `permissions:` block, granting overly permissive GITHUB_TOKEN (SUP-009).
6. `security.yml`, `schema-audit.yml`, and `e2e.yml` contain hardcoded test secrets and database credentials (SUP-010).
7. Python and npm package names (`zozi`, `frontend`) are generic and unprotected from dependency confusion (SUP-011).
8. No automated license compliance scanning configured (SUP-003).
9. Lockfile version drift between requirements.txt and TECHNOLOGY_STACK.md (SUP-004).

### Solution(s)
1. Add Syft SBOM generation step to security.yml and upload artifact (SUP-002).
2. Add Trivy container image scan to build.yml before push; fail on CRITICAL/HIGH (SUP-005).
3. Add cosign signing step to build.yml after image push (SUP-006).
4. Rotate SECRET_KEY; delete `.env` files from working tree; use Coolify env vars (SUP-007).
5. Add `permissions: contents: read` to ci.yml and architecture-gate.yml (SUP-009).
6. Move all hardcoded secrets in workflows to GitHub Secrets (SUP-010).
7. Rename internal packages to scoped names or configure private registry (SUP-011).
8. Add license scanning tool to CI (SUP-003).
9. Align requirements.txt with TECHNOLOGY_STACK.md versions (SUP-004).

### Suggestion(s)
1. Add CI gate that fails when any workflow lacks `permissions:` block.
2. Add CI gate that scans workflow files for hardcoded secrets.
3. Publish `zozi` on PyPI and npm to squat the names, or rename packages.
4. Add pre-commit hook that rejects any `.env` file in working tree.
5. Add post-deploy verification step that checks SBOM artifact is present.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Rotate SECRET_KEY and remove `.env` files from working tree | Coolify env vars | yes | S | 5 |
| P1 | Add `permissions:` block to ci.yml and architecture-gate.yml | .github/workflows/ci.yml, architecture-gate.yml | partial | S | 5 |
| P1 | Add Trivy container image scan to build.yml | .github/workflows/build.yml | partial | M | 4 |
| P1 | Add cosign signing step to build.yml | .github/workflows/build.yml | partial | M | 4 |
| P2 | Add Syft SBOM generation to security.yml | .github/workflows/security.yml | no | M | 4 |
| P2 | Move hardcoded secrets in workflows to GitHub Secrets | .github/workflows/security.yml, schema-audit.yml, e2e.yml | no | S | 5 |
| P2 | Rename internal packages to scoped names or configure private registry | pyproject.toml, package.json | no | M | 4 |
| P2 | Add license scanning tool to CI | .github/workflows/security.yml | no | M | 3 |
| P2 | Align requirements.txt with TECHNOLOGY_STACK.md versions | backend/requirements.txt | no | S | 4 |

## Clusters

| Cluster ID | Phase | Depends on phase | Root cause | Members | Recommended fix | Recommended test | Completion blocker |
|---|---|---|---|---|---|---|---|
| CLUSTER-cve-scanning | infra | — | CVE scanning configured in CI but with gaps (npm audit targets wrong lockfile, no container image scan) | SUP-001 | Fix npm audit target, add Trivy image scan | CI security gate passes | no |
| CLUSTER-sbom-missing | infra | — | SBOM generation required by canonical stack but not implemented in CI | SUP-002 | Add Syft SBOM generation to security.yml | tests/test_sbom.py::test_sbom_generated | no |
| CLUSTER-plaintext-secrets | security | — | Production SECRET_KEY stored in unencrypted .env files in working tree | SUP-007 | Rotate key, remove .env files, use Coolify env vars | tests/security/test_no_plaintext_secrets.py | yes |
| CLUSTER-workflow-permissions | infra | — | GitHub Actions workflows lack least-privilege permissions blocks | SUP-009 | Add permissions blocks to ci.yml and architecture-gate.yml | tests/infrastructure/test_workflow_permissions.py | partial |
| CLUSTER-hardcoded-secrets-workflows | security | — | Test secrets and DB credentials hardcoded in workflow files | SUP-010 | Move all hardcoded secrets to GitHub Secrets | tests/security/test_workflow_secrets.py | no |
| CLUSTER-dependency-confusion | security | — | Generic unscoped package names on PyPI and npm | SUP-011 | Rename to scoped names or configure private registry | tests/security/test_dependency_confusion.py | no |

## Related Findings
- D2P-008 in `dimensions/13_dev_to_prod.md` covers missing SBOM generation.
- D2P-013 in `dimensions/13_dev_to_prod_docker_verify.md` covers missing cosign signing and SBOM generation in build.yml.
- TECH-053 in `dimensions/02_technological.md` covers missing SBOM generation from the technological dimension.
- LAW-291 in `dimensions/09_laws.md` covers missing SBOM generation in CI.
- SUP-201 through SUP-208 from Part 3 sub-agent are integrated into SUP-007 through SUP-011 above.

## Supply Chain Security Assessment

### Dependency Scanning: ✅ STRONG
- pip-audit scans uv.lock for Python CVEs
- npm audit scans for Node CVEs
- Trivy scans filesystem for container/filesystem CVEs
- Results block PR merge via security-success gate
- **GAP:** npm audit targets package-lock.json but project uses pnpm-lock.yaml

### SBOM Presence: ❌ MISSING
- No Syft or CycloneDX SBOM generation in any workflow
- TECHNOLOGY_STACK.md §11 requires Syft/CycloneDX 1.17.0+
- Law 291 mandates SBOM generation in CI
- **GAP:** No SBOM artifact produced for any release

### License Compliance: ⚠️ UNVERIFIED
- No automated license scanning tool configured
- Cannot verify that all dependencies have compatible licenses
- **GAP:** Manual review required or add license scanner to CI

### Lockfile Integrity: ⚠️ PARTIAL
- uv.lock present and used by CI
- pnpm-lock.yaml present for frontend
- **GAP:** requirements.txt has version drift from TECHNOLOGY_STACK.md (fastapi, starlette, etc.)

### Container Scanning: ⚠️ PARTIAL
- Trivy filesystem scan in security.yml
- **GAP:** No container image scan in build.yml before push

### Image Signing: ❌ MISSING
- No cosign usage in build.yml
- Images pushed to GHCR without signing or provenance attestation
- Law 295 requires signed artifacts and SBOM
- **GAP:** No image integrity verification for consumers

### Secrets in Git: ✅ CLEAN
- No secrets found in git history
- gitleaks configured and running in CI
- .gitignore properly ignores .env files
- **GAP:** .env files exist in working tree with production SECRET_KEY

### GitHub Actions Security: ⚠️ PARTIAL
- security.yml, deploy.yml, build.yml, e2e.yml, integration.yml have permissions blocks
- **GAP:** ci.yml and architecture-gate.yml lack permissions blocks
- **GAP:** Hardcoded test secrets in security.yml, schema-audit.yml, e2e.yml

### Dependency Confusion: ⚠️ VULNERABLE
- @zozi/shared is correctly scoped and private
- **GAP:** Root package.json name "zozi" and frontend/package.json name "frontend" are generic
- **GAP:** pyproject.toml name "zozi" is generic on PyPI

### Pre-commit Hooks: ✅ STRONG
- ruff, mypy, import-linter, gitleaks, pip-audit, black configured
- Fast local supply chain gate before code reaches CI

### gitleaks in CI: ✅ STRONG
- gitleaks runs in security.yml and ci.yml
- Security-success gate fails on any finding
- Custom .gitleaks.toml with ZOZI-specific patterns

### Dependabot: ✅ STRONG
- .github/dependabot.yml covers pip, npm (3 directories), docker, github-actions
- Weekly schedule with 5-10 PR limits
- High/critical CVEs block deployment

*End of Agent Findings — Supply Chain Security*
*Total: 12 findings | 2 Critical | 3 High | 5 Medium | 2 Low*
