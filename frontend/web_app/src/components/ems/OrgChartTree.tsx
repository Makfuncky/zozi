"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Users, User, Building2, ChevronRight, ChevronDown,
  Search, Loader2, AlertCircle, Plus, Target,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

interface OrgUnit {
  id: number;
  name: string;
  path: string;
  depth: number;
  parent_unit_id: number | null;
  manager_employee_id: number | null;
  manager_name: string | null;
  employee_count?: number;
  children?: OrgUnit[];
}

interface OrgChartTreeProps {
  rootUnitId?: number;
  className?: string;
}

export default function OrgChartTree({ rootUnitId, className }: OrgChartTreeProps) {
  const [units, setUnits] = useState<OrgUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [search, setSearch] = useState("");
  const [selectedUnit, setSelectedUnit] = useState<OrgUnit | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const response = await apiFetch(rootUnitId
          ? `/hierarchy/org-units/${rootUnitId}/subtree`
          : "/hierarchy/org-units?limit=200");
        const json = await response.json();
        const list = Array.isArray(json) ? json : json?.units || json?.org_units || [];
        if (!cancelled) {
          setUnits(list);
          const roots = list.filter((u: OrgUnit) => !u.parent_unit_id);
          if (roots.length > 0) {
            setExpanded(new Set([roots[0].id]));
            setSelectedUnit(roots[0]);
          }
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [rootUnitId]);

  const filtered = search
    ? units.filter((u) => u.name.toLowerCase().includes(search.toLowerCase()))
    : units;

  const childrenOf = (parentId: number | null) =>
    filtered.filter((u) => u.parent_unit_id === parentId)
      .sort((a, b) => a.name.localeCompare(b.name));

  const roots = childrenOf(null);

  const toggleExpand = (id: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSelect = (unit: OrgUnit) => {
    setSelectedUnit(unit);
    toggleExpand(unit.id);
  };

  if (loading) {
    return (
      <div className={cn("flex items-center justify-center py-16", className)}>
        <Loader2 className="w-6 h-6 animate-spin text-text-muted" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("flex items-center gap-2 text-danger py-8", className)}>
        <AlertCircle className="w-5 h-5" /> {error}
      </div>
    );
  }

  if (units.length === 0) {
    return (
      <div className={cn("text-center py-16", className)}>
        <Building2 className="w-12 h-12 text-text-muted/30 mx-auto mb-3" />
        <p className="text-text-muted">No organization units found</p>
      </div>
    );
  }

  return (
    <div className={cn("flex gap-6", className)}>
      <div className="flex-1 min-w-0">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input type="text" placeholder="Search units..." value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-surface border border-border text-sm text-text
              placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-primary/30" />
        </div>
        <div className="space-y-0.5">
          {roots.map((unit) => (
            <OrgTreeNode key={unit.id} unit={unit} childrenOf={childrenOf}
              expanded={expanded} onToggle={handleSelect}
              selectedUnitId={selectedUnit?.id ?? null}
              depth={0} />
          ))}
        </div>
      </div>

      <AnimatePresence>
        {selectedUnit && (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }} className="w-80 flex-shrink-0 hidden lg:block">
            <div className="glass-panel rounded-2xl p-5 sticky top-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20
                  flex items-center justify-center">
                  <Building2 className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-text">{selectedUnit.name}</h3>
                  <p className="text-xs text-text-muted">Depth {selectedUnit.depth}</p>
                </div>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-text-muted">Manager</span>
                  <span className="text-text font-medium">{selectedUnit.manager_name || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Sub-units</span>
                  <span className="text-text font-medium">{childrenOf(selectedUnit.id).length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Path</span>
                  <span className="text-text font-medium text-xs truncate max-w-[140px]">{selectedUnit.path || "—"}</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function OrgTreeNode({
  unit, childrenOf, expanded, onToggle, selectedUnitId, depth,
}: {
  unit: OrgUnit;
  childrenOf: (parentId: number | null) => OrgUnit[];
  expanded: Set<number>;
  onToggle: (unit: OrgUnit) => void;
  selectedUnitId: number | null;
  depth: number;
}) {
  const children = childrenOf(unit.id);
  const hasChildren = children.length > 0;
  const isExpanded = expanded.has(unit.id);
  const isSelected = selectedUnitId === unit.id;

  return (
    <div>
      <motion.button
        whileHover={{ x: 2 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => onToggle(unit)}
        className={cn(
          "w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-left transition-all",
          isSelected
            ? "bg-primary/10 text-primary border border-primary/20"
            : "hover:bg-surface-1 text-text border border-transparent",
        )}
        style={{ paddingLeft: `${12 + depth * 20}px` }}
      >
        {hasChildren ? (
          <ChevronRight className={cn("w-3.5 h-3.5 text-text-muted transition-transform flex-shrink-0",
            isExpanded ? "rotate-90" : "")} />
        ) : (
          <div className="w-3.5 h-3.5 flex-shrink-0" />
        )}
        <div className={cn(
          "w-7 h-7 rounded-lg bg-gradient-to-br flex items-center justify-center flex-shrink-0",
          depth === 0 ? "from-primary/30 to-accent/30" : "from-surface-2 to-surface-3",
        )}>
          {depth === 0 ? (
            <Building2 className="w-3.5 h-3.5 text-primary" />
          ) : (
            <Building2 className="w-3 h-3 text-text-muted" />
          )}
        </div>
        <span className="text-sm font-medium flex-1 truncate">{unit.name}</span>
        {unit.manager_name && (
          <span className="text-xs text-text-muted hidden sm:block">{unit.manager_name}</span>
        )}
        {hasChildren && (
          <span className="text-xs text-text-muted/60 bg-surface-2 px-1.5 py-0.5 rounded-md">{children.length}</span>
        )}
      </motion.button>
      <AnimatePresence>
        {isExpanded && hasChildren && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}>
            {children.map((child) => (
              <OrgTreeNode key={child.id} unit={child} childrenOf={childrenOf}
                expanded={expanded} onToggle={onToggle}
                selectedUnitId={selectedUnitId} depth={depth + 1} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
