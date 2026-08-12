"""Temporary helper to dump coherence gate violations."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
import coherence_gate as cg

layers, allmods, graph, mc = cg.build()
hard, soft = cg.directional_violations(layers, allmods, graph)
print("HARD", len(hard), "SOFT", len(soft))
print("=== SOFT ===")
for m, r, li, lj in sorted(soft):
    print(f"  {m} -> {r} ({li}->{lj})")
print("=== HARD ===")
for m, r, li, lj in sorted(hard):
    print(f"  {m} -> {r} ({li}->{lj})")
