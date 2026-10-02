import os
import re
from collections import defaultdict

DIMENSIONS_DIR = "_audit/dimensions"
OUTPUT_FILE = "_audit/COMPLETION_BLOCKERS.md"

# Define phase mapping based on dimension file names and content
PHASE_MAP = {
    "00_boot_smoke_test.md": "boot",
    "01_architectural.md": "arch",
    "02_technological.md": "tech",
    "03_logical.md": "logic",
    "04_operational.md": "infra",
    "05_wiring.md": "arch",
    "06_database.md": "db",
    "07_tables_fields.md": "db",
    "08_providers.md": "providers",
    "09_laws.md": "compliance",
    "10_migrations.md": "db",
    "11_environmental.md": "infra",
    "12_tests.md": "testing",
    "12_tests_collection_verify.md": "testing",
    "13_dev_to_prod.md": "infra",
    "13_dev_to_prod_docker_verify.md": "infra",
    "14_frontend_web.md": "frontend",
    "15_frontend_mobile.md": "mobile",
    "16_features.md": "features",
    "17_code_file_management.md": "arch",
    "18_security.md": "security",
    "19_performance.md": "perf",
    "20_observability_resilience.md": "infra",
    "21_contradictions.md": "tech",
    "22_anti_patterns.md": "logic",
    "23_code_intent.md": "code_intent",
    "24_browser_behavior.md": "testing",
    "25_ai_drift.md": "arch",
    "26_code_alignment.md": "routing",
    "27_project_completion_blockers.md": "boot",
    "28_supply_chain_security.md": "security",
    "config_verification.md": "config",
    "suppliers.md": "suppliers",
}

def parse_finding_line(line, source_file):
    """Parse a finding table row and return dict if it's a blocker, else None."""
    line = line.strip()
    if not line.startswith("|"):
        return None
    
    # Remove leading/trailing pipes and split
    parts = [p.strip() for p in line.strip("|").split("|")]
    
    if len(parts) < 5:
        return None
    
    # The last column should be the completion blocker
    completion_blocker = parts[-1].lower()
    if completion_blocker not in ("yes", "partial"):
        return None
    
    # Try to identify the columns
    # Common format: ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker
    finding_id = parts[0]
    phase = parts[1] if len(parts) > 1 else ""
    status = parts[2] if len(parts) > 2 else ""
    cluster = parts[3] if len(parts) > 3 else ""
    file_line = parts[4] if len(parts) > 4 else ""
    current = parts[5] if len(parts) > 5 else ""
    target = parts[6] if len(parts) > 6 else ""
    delta = parts[7] if len(parts) > 7 else ""
    fix = parts[8] if len(parts) > 8 else ""
    effort = parts[9] if len(parts) > 9 else ""
    priority = parts[10] if len(parts) > 10 else ""
    confidence = parts[11] if len(parts) > 11 else ""
    evidence = parts[12] if len(parts) > 12 else ""
    truth = parts[13] if len(parts) > 13 else ""
    claim = parts[14] if len(parts) > 14 else ""
    sibling = parts[15] if len(parts) > 15 else ""
    verify = parts[16] if len(parts) > 16 else ""
    test = parts[17] if len(parts) > 17 else ""
    rollback = parts[18] if len(parts) > 18 else ""
    blast = parts[19] if len(parts) > 19 else ""
    depends = parts[20] if len(parts) > 20 else ""
    blocks = parts[21] if len(parts) > 21 else ""
    
    # Determine phase from file if not clear
    base_name = os.path.basename(source_file)
    file_phase = PHASE_MAP.get(base_name, phase)
    
    return {
        "id": finding_id,
        "phase": file_phase,
        "status": status,
        "cluster": cluster,
        "file_line": file_line,
        "current": current,
        "target": target,
        "delta": delta,
        "fix": fix,
        "effort": effort,
        "priority": priority.upper(),
        "confidence": confidence,
        "evidence": evidence,
        "truth": truth,
        "claim": claim,
        "sibling": sibling,
        "verify": verify,
        "test": test,
        "rollback": rollback,
        "blast": blast,
        "depends": depends,
        "blocks": blocks,
        "completion_blocker": completion_blocker,
        "source": source_file,
    }

def main():
    blockers = []
    seen = set()
    
    for root, dirs, files in os.walk(DIMENSIONS_DIR):
        for filename in sorted(files):
            if not filename.endswith(".md"):
                continue
            filepath = os.path.join(root, filename)
            
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            
            for line in lines:
                result = parse_finding_line(line, filepath)
                if result and result["priority"] in ("P0", "P1", "P2", "P3"):
                    # Deduplicate by file_line + finding_id
                    dedup_key = (result["file_line"], result["id"])
                    if dedup_key not in seen:
                        seen.add(dedup_key)
                        blockers.append(result)
    
    # Sort by Priority (P0, P1, P2, P3) then Effort (S, M, L)
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    effort_order = {"S": 0, "M": 1, "L": 2}
    
    def sort_key(b):
        return (
            priority_order.get(b["priority"], 99),
            effort_order.get(b["effort"], 99),
            b["id"],
        )
    
    blockers.sort(key=sort_key)
    
    # Group by phase
    phase_order = ["emergency", "boot", "tech", "db", "logic", "arch", "security", "payment", "compliance", "frontend", "mobile", "testing", "infra", "docs"]
    phase_blockers = defaultdict(list)
    for b in blockers:
        phase_blockers[b["phase"]].append(b)
    
    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("# Project Completion Blockers\n\n")
        out.write("## Summary\n\n")
        out.write("| Phase | Count |\n")
        out.write("|---|---|\n")
        for phase in phase_order:
            if phase in phase_blockers:
                out.write(f"| {phase} | {len(phase_blockers[phase])} |\n")
        # Add any phases not in the predefined list
        for phase in sorted(phase_blockers.keys()):
            if phase not in phase_order:
                out.write(f"| {phase} | {len(phase_blockers[phase])} |\n")
        out.write(f"| **Total** | **{len(blockers)}** |\n\n")
        
        out.write("## Blockers by Phase\n\n")
        for phase in phase_order:
            if phase not in phase_blockers:
                continue
            out.write(f"### {phase.title()}\n\n")
            out.write("| ID | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Unblocks | Status | Completion blocker |\n")
            out.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
            for b in phase_blockers[phase]:
                out.write(f"| {b['id']} | {b['file_line']} | {b['current']} | {b['target']} | {b['delta']} | {b['fix']} | {b['effort']} | {b['priority']} | {b['confidence']} | {b['verify']} | {b['test']} | {b['rollback']} | {b['blast']} | {b['depends']} | {b['blocks']} | {b['sibling']} | {b['status']} | {b['completion_blocker']} |\n")
            out.write("\n")
        
        # Add any remaining phases
        for phase in sorted(phase_blockers.keys()):
            if phase in phase_order:
                continue
            out.write(f"### {phase.title()}\n\n")
            out.write("| ID | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Unblocks | Status | Completion blocker |\n")
            out.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
            for b in phase_blockers[phase]:
                out.write(f"| {b['id']} | {b['file_line']} | {b['current']} | {b['target']} | {b['delta']} | {b['fix']} | {b['effort']} | {b['priority']} | {b['confidence']} | {b['verify']} | {b['test']} | {b['rollback']} | {b['blast']} | {b['depends']} | {b['blocks']} | {b['sibling']} | {b['status']} | {b['completion_blocker']} |\n")
            out.write("\n")
        
        out.write("## Top 20 Blockers\n\n")
        out.write("| ID | Phase | File:Line | Priority | Effort | Blast radius | Fix |\n")
        out.write("|---|---|---|---|---|---|---|\n")
        for b in blockers[:20]:
            out.write(f"| {b['id']} | {b['phase']} | {b['file_line']} | {b['priority']} | {b['effort']} | {b['blast']} | {b['fix']} |\n")
        out.write("\n")
    
    print(f"Extracted {len(blockers)} unique blockers to {OUTPUT_FILE}")
    print(f"Breakdown by phase:")
    for phase in sorted(phase_blockers.keys()):
        print(f"  {phase}: {len(phase_blockers[phase])}")

if __name__ == "__main__":
    main()
