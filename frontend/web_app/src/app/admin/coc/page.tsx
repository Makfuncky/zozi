"use client";

import { Button } from "@/components/ui/Button";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ChevronDown,
  ChevronRight,
  Layers3,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  X,
  Tag,
  Package,
  Gem,
  Cpu,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/stores/toastStore";

interface CoCCategory {
  id: number;
  name: string;
  slug: string;
  level: number;
  description?: string | null;
  icon?: string | null;
  parent_id?: number | null;
  sort_order: number;
  is_active: boolean;
  is_deleted?: boolean;
  path?: string | null;
  depth?: number;
  commission_group_id?: number | null;
  children?: CoCCategory[];
}

interface ProductType {
  id: number;
  name: string;
  slug: string;
  icon?: string | null;
  is_active: boolean;
}

interface CategoryAttribute {
  id: number;
  product_type_id?: number;
  name: string;
  key: string;
  layer: number;
  value_type: string;
  options?: string | null;
  is_required: boolean;
  is_active: boolean;
}

interface CommissionGroup {
  id: number;
  name: string;
  slug: string;
  base_rate: number;
}

const LEVEL_LABELS: Record<number, string> = {
  1: "Department",
  2: "Category",
  3: "Sub-Category",
  4: "Product Type",
  5: "Brand / IP",
  6: "Spec / Variant",
  7: "SKU / Leaf",
};

const LEVEL_ICONS: Record<number, typeof Tag> = {
  1: Layers3,
  2: Tag,
  3: Package,
  4: Cpu,
  5: Gem,
  6: Tag,
  7: Package,
};

// ── Tree Node (L1-L3) ──────────────────────────────────────────────────────

function CoCTreeNode({
  node,
  depth = 0,
  onEdit,
  onToggle,
  onAddChild,
  onDelete,
  onAddProductType,
  expandedNodes,
  onToggleNode,
  productTypes,
  loadingPTs,
  onLoadProductTypes,
  attributes,
  loadingAttrs,
  onLoadAttributes,
  onAddAttribute,
  onEditAttribute,
  onDeleteAttribute,
  groups,
}: {
  node: CoCCategory;
  depth?: number;
  onEdit: (node: CoCCategory) => void;
  onToggle: (id: number, active: boolean) => void;
  onAddChild: (parent: CoCCategory) => void;
  onDelete: (node: CoCCategory) => void;
  onAddProductType: (cocNodeId: number) => void;
  expandedNodes: Set<number>;
  onToggleNode: (id: number) => void;
  productTypes: Record<number, ProductType[]>;
  loadingPTs: Set<number>;
  onLoadProductTypes: (cocNodeId: number) => void;
  attributes: Record<number, CategoryAttribute[]>;
  loadingAttrs: Set<number>;
  onLoadAttributes: (productTypeId: number) => void;
  onAddAttribute: (productTypeId: number, layer: number) => void;
  onEditAttribute: (attr: CategoryAttribute) => void;
  onDeleteAttribute: (attr: CategoryAttribute) => void;
  groups: CommissionGroup[];
}) {
  const isExpanded = expandedNodes.has(node.id);
  const hasChildren = node.children && node.children.length > 0;
  const pts = productTypes[node.id] || [];
  const isLoadingPT = loadingPTs.has(node.id);
  const LevelIcon = LEVEL_ICONS[node.level] || Tag;
  const group = groups.find((g) => g.id === node.commission_group_id);

  const handleExpand = () => {
    onToggleNode(node.id);
    if (!hasChildren && !isExpanded) {
      // L3 nodes load product types on expand
    }
  };

  return (
    <div className="select-none">
      <div
        className={`flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-surface-2 transition-colors ${
          !node.is_active ? "opacity-50" : ""
        }`}
        style={{ paddingLeft: `${depth * 20 + 12}px` }}
      >
        {/* Expand/collapse */}
        {hasChildren || node.level <= 2 ? (
          <button onClick={handleExpand} className="text-text-muted hover:text-text">
            {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        ) : (
          <span className="w-4" />
        )}

        {node.icon && <span className="text-lg">{node.icon}</span>}
        {!node.icon && <LevelIcon className="h-4 w-4 text-text-muted" />}

        <span className="flex-1 text-sm font-medium text-text">{node.name}</span>

        {/* Level badge */}
        <span className="rounded-full bg-surface-2 px-2 py-0.5 text-xs text-text-muted">
          L{node.level} {LEVEL_LABELS[node.level]}
        </span>

        {/* Commission group badge */}
        {group && (
          <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
            {group.base_rate}%
          </span>
        )}

        {/* Active toggle */}
        <label className="relative inline-flex items-center cursor-pointer mr-2">
          <input
            type="checkbox"
            checked={node.is_active}
            onChange={() => onToggle(node.id, !node.is_active)}
            className="sr-only peer"
          />
          <div className={`w-8 h-4 rounded-full peer ${node.is_active ? "bg-success" : "bg-border"} transition-colors`}>
            <div
              className={`absolute top-0.5 left-0.5 w-3 h-3 rounded-full bg-white shadow transition-transform ${
                node.is_active ? "translate-x-4" : ""
              }`}
            />
          </div>
        </label>

        {/* Actions */}
        {node.level < 3 && (
          <button
            onClick={() => onAddChild(node)}
            className="rounded p-1 text-text-muted hover:bg-surface-1 hover:text-primary"
            title="Add child"
          >
            <Plus className="h-3.5 w-3.5" />
          </button>
        )}
        {node.level === 3 && (
          <button
            onClick={() => onAddProductType(node.id)}
            className="rounded p-1 text-text-muted hover:bg-surface-1 hover:text-primary"
            title="Add product type"
          >
            <Package className="h-3.5 w-3.5" />
          </button>
        )}
        <button
          onClick={() => onEdit(node)}
          className="rounded p-1 text-text-muted hover:bg-surface-1 hover:text-primary"
          title="Edit"
        >
          <Pencil className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={() => onDelete(node)}
          className="rounded p-1 text-text-muted hover:bg-surface-1 hover:text-danger"
          title="Delete"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Children (L1-L3 tree) */}
      {isExpanded && hasChildren && (
        <div>
          {node.children!.map((child) => (
            <CoCTreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              onEdit={onEdit}
              onToggle={onToggle}
              onAddChild={onAddChild}
              onDelete={onDelete}
              onAddProductType={onAddProductType}
              expandedNodes={expandedNodes}
              onToggleNode={onToggleNode}
              productTypes={productTypes}
              loadingPTs={loadingPTs}
              onLoadProductTypes={onLoadProductTypes}
              attributes={attributes}
              loadingAttrs={loadingAttrs}
              onLoadAttributes={onLoadAttributes}
              onAddAttribute={onAddAttribute}
              onEditAttribute={onEditAttribute}
              onDeleteAttribute={onDeleteAttribute}
              groups={groups}
            />
          ))}
        </div>
      )}

      {/* Product Types (L4) under L3 */}
      {isExpanded && node.level === 3 && (
        <div>
          {isLoadingPT ? (
            <div className="ml-10 py-2 text-xs text-text-muted">Loading product types...</div>
          ) : pts.length > 0 ? (
            pts.map((pt) => (
              <ProductTypeNode
                key={pt.id}
                productType={pt}
                depth={depth + 1}
                attributes={attributes}
                loadingAttrs={loadingAttrs}
                onLoadAttributes={onLoadAttributes}
                onAddAttribute={onAddAttribute}
                onEditAttribute={onEditAttribute}
                onDeleteAttribute={onDeleteAttribute}
                expandedNodes={expandedNodes}
                onToggleNode={onToggleNode}
              />
            ))
          ) : (
            <div className="ml-10 py-2 text-xs text-text-faint italic">No product types — click + to add</div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Product Type Node (L4) ──────────────────────────────────────────────────

function ProductTypeNode({
  productType,
  depth,
  attributes,
  loadingAttrs,
  onLoadAttributes,
  onAddAttribute,
  onEditAttribute,
  onDeleteAttribute,
  expandedNodes,
  onToggleNode,
}: {
  productType: ProductType;
  depth: number;
  attributes: Record<number, CategoryAttribute[]>;
  loadingAttrs: Set<number>;
  onLoadAttributes: (productTypeId: number) => void;
  onAddAttribute: (productTypeId: number, layer: number) => void;
  onEditAttribute: (attr: CategoryAttribute) => void;
  onDeleteAttribute: (attr: CategoryAttribute) => void;
  expandedNodes: Set<number>;
  onToggleNode: (id: number) => void;
}) {
  const isExpanded = expandedNodes.has(productType.id);
  const attrs = attributes[productType.id] || [];
  const isLoadingAttr = loadingAttrs.has(productType.id);
  const brandAttrs = attrs.filter((a) => a.layer === 5);
  const specAttrs = attrs.filter((a) => a.layer === 6);

  const handleExpand = () => {
    onToggleNode(productType.id);
    if (!isExpanded && attrs.length === 0) {
      onLoadAttributes(productType.id);
    }
  };

  return (
    <div className="select-none">
      <div
        className={`flex items-center gap-2 rounded-lg px-3 py-1.5 hover:bg-surface-2 transition-colors ${
          !productType.is_active ? "opacity-50" : ""
        }`}
        style={{ paddingLeft: `${(depth + 1) * 20 + 12}px` }}
      >
        <button onClick={handleExpand} className="text-text-muted hover:text-text">
          {isExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        </button>

        <Cpu className="h-3.5 w-3.5 text-primary" />
        <span className="text-sm font-medium text-text">{productType.name}</span>
        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">L4</span>

        <button
          onClick={() => onAddAttribute(productType.id, 5)}
          className="rounded p-1 text-text-muted hover:bg-surface-1 hover:text-primary ml-auto"
          title="Add brand"
        >
          <Plus className="h-3 w-3" />
        </button>
      </div>

      {/* Attributes (L5-L6) */}
      {isExpanded && (
        <div>
          {isLoadingAttr ? (
            <div className="ml-12 py-1 text-xs text-text-muted">Loading attributes...</div>
          ) : (
            <>
              {/* L5: Brands */}
              {brandAttrs.length > 0 && (
                <div className="ml-12 py-1">
                  <div className="text-xs font-semibold text-text-muted mb-1">Brands (L5)</div>
                  <div className="flex flex-wrap gap-1.5">
                    {brandAttrs.map((attr) =>
                      attr.options ? (
                        <AttributeChips
                          key={attr.id}
                          attribute={attr}
                          onEdit={onEditAttribute}
                          onDelete={onDeleteAttribute}
                        />
                      ) : (
                        <span
                          key={attr.id}
                          className="inline-flex items-center gap-1 rounded-full bg-surface-2 px-2.5 py-1 text-xs text-text"
                        >
                          {attr.name}
                          <button onClick={() => onEditAttribute(attr)} className="text-text-muted hover:text-primary">
                            <Pencil className="h-2.5 w-2.5" />
                          </button>
                        </span>
                      )
                    )}
                  </div>
                </div>
              )}

              {/* L6: Specs */}
              {specAttrs.length > 0 && (
                <div className="ml-12 py-1">
                  <div className="text-xs font-semibold text-text-muted mb-1">Specs (L6)</div>
                  <div className="flex flex-wrap gap-1.5">
                    {specAttrs.map((attr) =>
                      attr.options ? (
                        <AttributeChips
                          key={attr.id}
                          attribute={attr}
                          onEdit={onEditAttribute}
                          onDelete={onDeleteAttribute}
                        />
                      ) : (
                        <span
                          key={attr.id}
                          className="inline-flex items-center gap-1 rounded-full bg-surface-2 px-2.5 py-1 text-xs text-text"
                        >
                          {attr.name}
                          <button onClick={() => onEditAttribute(attr)} className="text-text-muted hover:text-primary">
                            <Pencil className="h-2.5 w-2.5" />
                          </button>
                        </span>
                      )
                    )}
                  </div>
                </div>
              )}

              {brandAttrs.length === 0 && specAttrs.length === 0 && (
                <div className="ml-12 py-1 text-xs text-text-faint italic">
                  No attributes — click + to add brands or specs
                </div>
              )}

              {/* Add spec button */}
              <div className="ml-12 py-1">
                <button
                  onClick={() => onAddAttribute(productType.id, 6)}
                  className="text-xs text-primary hover:underline"
                >
                  + Add Spec
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ── Attribute Chips (L5/L6 values) ─────────────────────────────────────────

function AttributeChips({
  attribute,
  onEdit,
  onDelete,
}: {
  attribute: CategoryAttribute;
  onEdit: (attr: CategoryAttribute) => void;
  onDelete: (attr: CategoryAttribute) => void;
}) {
  let optionsList: string[] = [];
  try {
    optionsList = attribute.options ? JSON.parse(attribute.options) : [];
  } catch {
    optionsList = [];
  }

  return (
    <div className="inline-flex flex-wrap gap-1 items-center">
      <span className="text-xs font-medium text-text-muted mr-1">{attribute.name}:</span>
      {optionsList.map((opt, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-1 rounded-full bg-surface-2 px-2 py-0.5 text-xs text-text"
        >
          {opt}
        </span>
      ))}
      <button onClick={() => onEdit(attribute)} className="rounded p-0.5 text-text-muted hover:text-primary">
        <Pencil className="h-2.5 w-2.5" />
      </button>
    </div>
  );
}

// ── Form Components ─────────────────────────────────────────────────────────

function CategoryForm({
  editingNode,
  parentForNew,
  groups,
  onSave,
  onCancel,
}: {
  editingNode?: CoCCategory | null;
  parentForNew?: CoCCategory | null;
  groups: CommissionGroup[];
  onSave: (data: Record<string, unknown>) => void;
  onCancel: () => void;
}) {
  const isEditing = !!editingNode && !parentForNew;
  const defaultLevel = parentForNew ? Math.min(parentForNew.level + 1, 3) : editingNode?.level || 1;

  const [form, setForm] = useState({
    name: editingNode?.name || "",
    slug: editingNode?.slug || "",
    description: editingNode?.description || "",
    icon: editingNode?.icon || "",
    level: defaultLevel,
    parent_id: parentForNew?.id?.toString() || editingNode?.parent_id?.toString() || "",
    commission_group_id: editingNode?.commission_group_id?.toString() || "",
    is_active: editingNode?.is_active ?? true,
  });

  return (
    <div className="theme-card rounded-xl border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">
          {isEditing ? `Edit ${LEVEL_LABELS[editingNode.level]}` : parentForNew ? `Add Sub-Category under ${parentForNew.name}` : "New Category"}
        </h3>
        <button onClick={onCancel} className="rounded p-1 text-text-muted hover:bg-surface-2">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium text-text-muted">Name *</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Category name"
            className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-text-muted">Slug *</label>
          <input
            value={form.slug}
            onChange={(e) => setForm({ ...form, slug: e.target.value })}
            placeholder="category-slug"
            className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="text-xs font-medium text-text-muted">Level</label>
          <select
            value={form.level}
            onChange={(e) => setForm({ ...form, level: Number(e.target.value) })}
            disabled={isEditing || !!parentForNew}
            className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text disabled:opacity-50"
          >
            <option value={1}>L1 — Department</option>
            <option value={2}>L2 — Category</option>
            <option value={3}>L3 — Sub-Category</option>
          </select>
        </div>
        <div>
          <label className="text-xs font-medium text-text-muted">Icon (emoji)</label>
          <input
            value={form.icon}
            onChange={(e) => setForm({ ...form, icon: e.target.value })}
            placeholder="📦"
            className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-text-muted">Commission Group</label>
          <select
            value={form.commission_group_id}
            onChange={(e) => setForm({ ...form, commission_group_id: e.target.value })}
            className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
          >
            <option value="">None</option>
            {groups.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name} ({g.base_rate}%)
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="text-xs font-medium text-text-muted">Description</label>
        <input
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          placeholder="Optional description"
          className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
        />
      </div>

      <div className="flex items-center gap-3">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
            className="rounded border-border"
          />
          <span className="text-xs text-text-muted">Active</span>
        </label>
      </div>

      <div className="flex gap-3 pt-2">
        <button
          onClick={onCancel}
          className="flex-1 rounded-lg border border-border py-2 text-xs text-text-muted hover:bg-surface-2"
        >
          Cancel
        </button>
        <Button variant="primary" onClick={() => onSave(form)} disabled={!form.name || !form.slug} className="flex-1">
          {isEditing ? "Update" : "Create"}
        </Button>
      </div>
    </div>
  );
}

function ProductTypeForm({
  cocCategoryId,
  onSave,
  onCancel,
}: {
  cocCategoryId: number;
  onSave: (data: Record<string, unknown>) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({ name: "", slug: "", description: "", icon: "" });

  return (
    <div className="theme-card rounded-xl border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">New Product Type (L4)</h3>
        <button onClick={onCancel} className="rounded p-1 text-text-muted hover:bg-surface-2">
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium text-text-muted">Name *</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="e.g. Gaming Laptop"
            className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-text-muted">Slug *</label>
          <input
            value={form.slug}
            onChange={(e) => setForm({ ...form, slug: e.target.value })}
            placeholder="gaming-laptop"
            className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium text-text-muted">Icon (emoji)</label>
          <input
            value={form.icon}
            onChange={(e) => setForm({ ...form, icon: e.target.value })}
            placeholder="🎮"
            className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-text-muted">Description</label>
          <input
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Optional"
            className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
          />
        </div>
      </div>
      <div className="flex gap-3 pt-2">
        <button
          onClick={onCancel}
          className="flex-1 rounded-lg border border-border py-2 text-xs text-text-muted hover:bg-surface-2"
        >
          Cancel
        </button>
        <Button variant="primary" onClick={() => onSave(form)} disabled={!form.name || !form.slug} className="flex-1">
          Create Product Type
        </Button>
      </div>
    </div>
  );
}

function AttributeForm({
  productTypeId,
  editingAttr,
  layer,
  onSave,
  onCancel,
}: {
  productTypeId: number;
  editingAttr?: CategoryAttribute | null;
  layer: number;
  onSave: (data: Record<string, unknown>) => void;
  onCancel: () => void;
}) {
  const isEditing = !!editingAttr;
  const [form, setForm] = useState({
    name: editingAttr?.name || "",
    key: editingAttr?.key || "",
    value_type: editingAttr?.value_type || "select",
    options: editingAttr?.options ? (() => { try { return JSON.parse(editingAttr.options).join(", "); } catch { return ""; } })() : "",
    is_required: editingAttr?.is_required ?? false,
  });

  return (
    <div className="theme-card rounded-xl border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">
          {isEditing ? "Edit" : "New"} {layer === 5 ? "Brand" : "Spec"} Attribute (L{layer})
        </h3>
        <button onClick={onCancel} className="rounded p-1 text-text-muted hover:bg-surface-2">
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium text-text-muted">Name *</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder={layer === 5 ? "Brand" : "RAM Size"}
            className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-text-muted">Key *</label>
          <input
            value={form.key}
            onChange={(e) => setForm({ ...form, key: e.target.value })}
            placeholder={layer === 5 ? "brand" : "ram_size"}
            className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
          />
        </div>
      </div>
      <div>
        <label className="text-xs font-medium text-text-muted">
          Options (comma-separated for select type)
        </label>
        <input
          value={form.options}
          onChange={(e) => setForm({ ...form, options: e.target.value })}
          placeholder={layer === 5 ? "Apple, Samsung, Nike" : "8GB, 16GB, 32GB"}
          className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
        />
      </div>
      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={form.is_required}
            onChange={(e) => setForm({ ...form, is_required: e.target.checked })}
            className="rounded border-border"
          />
          <span className="text-xs text-text-muted">Required</span>
        </label>
      </div>
      <div className="flex gap-3 pt-2">
        <button
          onClick={onCancel}
          className="flex-1 rounded-lg border border-border py-2 text-xs text-text-muted hover:bg-surface-2"
        >
          Cancel
        </button>
        <Button
          variant="primary"
          onClick={() => onSave({ ...form, layer, product_type_id: productTypeId })}
          disabled={!form.name || !form.key}
          className="flex-1"
        >
          {isEditing ? "Update" : "Create"}
        </Button>
      </div>
    </div>
  );
}

// ── Main Page ───────────────────────────────────────────────────────────────

export default function AdminCoCPage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const addToast = useToastStore((s) => s.addToast);

  const [tree, setTree] = useState<CoCCategory[]>([]);
  const [groups, setGroups] = useState<CommissionGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  // Expanded nodes
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set());

  // Product types cache: cocNodeId → ProductType[]
  const [productTypes, setProductTypes] = useState<Record<number, ProductType[]>>({});
  const [loadingPTs, setLoadingPTs] = useState<Set<number>>(new Set());

  // Attributes cache: productTypeId → CategoryAttribute[]
  const [attributes, setAttributes] = useState<Record<number, CategoryAttribute[]>>({});
  const [loadingAttrs, setLoadingAttrs] = useState<Set<number>>(new Set());

  // Forms
  const [showForm, setShowForm] = useState(false);
  const [editingNode, setEditingNode] = useState<CoCCategory | null>(null);
  const [parentForNew, setParentForNew] = useState<CoCCategory | null>(null);
  const [showPTForm, setShowPTForm] = useState(false);
  const [ptFormCocNodeId, setPtFormCocNodeId] = useState<number | null>(null);
  const [showAttrForm, setShowAttrForm] = useState(false);
  const [attrFormProductTypeId, setAttrFormProductTypeId] = useState<number | null>(null);
  const [attrFormLayer, setAttrFormLayer] = useState<number>(5);
  const [editingAttr, setEditingAttr] = useState<CategoryAttribute | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !["admin", "sub_admin", "moderator"].includes(user?.role || "")) {
      router.push("/admin/login");
    }
  }, [authLoading, isLoggedIn, user, router]);

  const fetchTree = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/admin/coc/tree?max_depth=3");
      if (res.ok) setTree(await res.json());
    } catch {
      addToast("Failed to load categories", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  const fetchGroups = useCallback(async () => {
    try {
      const res = await apiFetch("/admin/coc/commission-groups");
      if (res.ok) setGroups(await res.json());
    } catch {
      // non-critical
    }
  }, []);

  useEffect(() => {
    if (isLoggedIn) {
      fetchTree();
      fetchGroups();
    }
  }, [fetchTree, fetchGroups, isLoggedIn]);

  // Toggle node expansion
  const handleToggleNode = useCallback((id: number) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  // Load product types for a L3 node
  const handleLoadProductTypes = useCallback(async (cocNodeId: number) => {
    setLoadingPTs((prev) => new Set(prev).add(cocNodeId));
    try {
      const res = await apiFetch(`/admin/coc/categories/${cocNodeId}/product-types`);
      if (res.ok) {
        const pts = await res.json();
        setProductTypes((prev) => ({ ...prev, [cocNodeId]: pts }));
      }
    } catch {
      // silent
    } finally {
      setLoadingPTs((prev) => {
        const next = new Set(prev);
        next.delete(cocNodeId);
        return next;
      });
    }
  }, []);

  // Load attributes for a product type
  const handleLoadAttributes = useCallback(async (productTypeId: number) => {
    setLoadingAttrs((prev) => new Set(prev).add(productTypeId));
    try {
      const res = await apiFetch(`/admin/coc/product-types/${productTypeId}/attributes`);
      if (res.ok) {
        const attrs = await res.json();
        setAttributes((prev) => ({ ...prev, [productTypeId]: attrs }));
      }
    } catch {
      // silent
    } finally {
      setLoadingAttrs((prev) => {
        const next = new Set(prev);
        next.delete(productTypeId);
        return next;
      });
    }
  }, []);

  // CRUD handlers
  const handleToggle = async (id: number, active: boolean) => {
    try {
      const res = await apiFetch(`/admin/coc/categories/${id}/toggle-active`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: active }),
      });
      if (res.ok) {
        addToast(active ? "Activated" : "Deactivated", "success");
        fetchTree();
      } else {
        addToast("Failed to toggle", "error");
      }
    } catch {
      addToast("Failed to toggle", "error");
    }
  };

  const handleSaveCategory = async (data: Record<string, unknown>) => {
    try {
      const body: Record<string, unknown> = {
        name: data.name,
        slug: data.slug,
        level: data.level,
        description: data.description || null,
        icon: data.icon || null,
        is_active: data.is_active,
      };
      if (data.parent_id) body.parent_id = Number(data.parent_id);
      if (data.commission_group_id) body.commission_group_id = Number(data.commission_group_id);

      const url = editingNode ? `/admin/coc/categories/${editingNode.id}` : `/admin/coc/categories`;
      const method = editingNode ? "PUT" : "POST";

      const res = await apiFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        addToast(editingNode ? "Updated" : "Created", "success");
        setShowForm(false);
        setEditingNode(null);
        setParentForNew(null);
        fetchTree();
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail || "Failed to save", "error");
      }
    } catch {
      addToast("Failed to save", "error");
    }
  };

  const handleDelete = async (node: CoCCategory) => {
    if (!confirm(`Archive "${node.name}"?`)) return;
    try {
      const res = await apiFetch(`/admin/coc/categories/${node.id}/archive`, { method: "POST" });
      if (res.ok) {
        addToast("Archived", "success");
        fetchTree();
      } else {
        addToast("Failed to archive", "error");
      }
    } catch {
      addToast("Failed to archive", "error");
    }
  };

  const handleSaveProductType = async (data: Record<string, unknown>) => {
    if (!ptFormCocNodeId) return;
    try {
      const res = await apiFetch(`/admin/coc/categories/${ptFormCocNodeId}/product-types`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: data.name,
          slug: data.slug,
          description: data.description || null,
          icon: data.icon || null,
        }),
      });
      if (res.ok) {
        addToast("Product type created", "success");
        setShowPTForm(false);
        setPtFormCocNodeId(null);
        handleLoadProductTypes(ptFormCocNodeId);
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail || "Failed to create", "error");
      }
    } catch {
      addToast("Failed to create", "error");
    }
  };

  const handleSaveAttribute = async (data: Record<string, unknown>) => {
    if (!attrFormProductTypeId) return;
    try {
      const options = data.options ? (data.options as string).split(",").map((s: string) => s.trim()).filter(Boolean) : null;
      const res = await apiFetch(`/admin/coc/product-types/${attrFormProductTypeId}/attributes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: data.name,
          key: data.key,
          layer: data.layer,
          value_type: data.value_type || "select",
          options,
          is_required: data.is_required || false,
        }),
      });
      if (res.ok) {
        addToast("Attribute created", "success");
        setShowAttrForm(false);
        setAttrFormProductTypeId(null);
        handleLoadAttributes(attrFormProductTypeId);
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail || "Failed to create", "error");
      }
    } catch {
      addToast("Failed to create", "error");
    }
  };

  const handleDeleteAttribute = async (attr: CategoryAttribute) => {
    if (!confirm(`Delete attribute "${attr.name}"?`)) return;
    // For now, soft-delete via archive endpoint if available
    addToast("Attribute deletion coming soon", "info");
  };

  // Filter tree by search
  const filterTree = (nodes: CoCCategory[]): CoCCategory[] => {
    if (!search.trim()) return nodes;
    return nodes
      .map((node) => ({
        ...node,
        children: node.children ? filterTree(node.children) : [],
      }))
      .filter(
        (node) =>
          node.name.toLowerCase().includes(search.toLowerCase()) ||
          node.slug.toLowerCase().includes(search.toLowerCase()) ||
          (node.children && node.children.length > 0)
      );
  };

  const filteredTree = filterTree(tree);

  if (authLoading) return null;

  return (
    <AdminLayout title="Chart of Categories" headerMode="compact">
      <PanelContent width="full" className="space-y-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search categories, product types, brands..."
              className="h-9 w-full rounded-lg border border-border bg-surface-1 pl-9 pr-3 text-xs text-text"
            />
          </div>
          <Button
            variant="primary"
            onClick={() => {
              setEditingNode(null);
              setParentForNew(null);
              setShowForm(true);
            }}
          >
            <Plus className="mr-1 h-3.5 w-3.5" />
            Add Category
          </Button>
          <Button variant="ghost" onClick={fetchTree}>
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>

        {/* Level legend */}
        <div className="flex flex-wrap gap-2 text-xs text-text-muted">
          {Object.entries(LEVEL_LABELS).map(([level, label]) => (
            <span key={level} className="rounded-full bg-surface-2 px-2 py-0.5">
              L{level}: {label}
            </span>
          ))}
        </div>

        {/* Forms */}
        {showForm && (
          <CategoryForm
            editingNode={editingNode}
            parentForNew={parentForNew}
            groups={groups}
            onSave={handleSaveCategory}
            onCancel={() => {
              setShowForm(false);
              setEditingNode(null);
              setParentForNew(null);
            }}
          />
        )}

        {showPTForm && ptFormCocNodeId && (
          <ProductTypeForm
            cocCategoryId={ptFormCocNodeId}
            onSave={handleSaveProductType}
            onCancel={() => {
              setShowPTForm(false);
              setPtFormCocNodeId(null);
            }}
          />
        )}

        {showAttrForm && attrFormProductTypeId && (
          <AttributeForm
            productTypeId={attrFormProductTypeId}
            editingAttr={editingAttr}
            layer={attrFormLayer}
            onSave={handleSaveAttribute}
            onCancel={() => {
              setShowAttrForm(false);
              setAttrFormProductTypeId(null);
              setEditingAttr(null);
            }}
          />
        )}

        {/* Tree */}
        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="h-10 rounded-lg bg-surface-2 animate-pulse" />
            ))}
          </div>
        ) : filteredTree.length === 0 ? (
          <div className="rounded-2xl border border-border bg-surface-1 px-6 py-12 text-center">
            <Layers3 className="mx-auto h-8 w-8 text-text-faint" />
            <p className="mt-3 text-sm font-semibold text-text">
              {search ? "No matching categories" : "No categories yet"}
            </p>
            <p className="mt-2 text-xs text-text-faint">
              {search ? "Try a different search term" : "Create your first L1 department to get started."}
            </p>
          </div>
        ) : (
          <div className="rounded-xl border border-border overflow-hidden">
            <div className="bg-surface-2 px-3 py-2 text-xs font-semibold text-text-muted">
              Category Tree — {tree.length} root departments
            </div>
            <div className="divide-y divide-border">
              {filteredTree.map((node) => (
                <CoCTreeNode
                  key={node.id}
                  node={node}
                  onEdit={(n) => {
                    setEditingNode(n);
                    setParentForNew(null);
                    setShowForm(true);
                  }}
                  onToggle={handleToggle}
                  onAddChild={(parent) => {
                    setParentForNew(parent);
                    setEditingNode(null);
                    setShowForm(true);
                  }}
                  onDelete={handleDelete}
                  onAddProductType={(cocNodeId) => {
                    setPtFormCocNodeId(cocNodeId);
                    setShowPTForm(true);
                  }}
                  expandedNodes={expandedNodes}
                  onToggleNode={handleToggleNode}
                  productTypes={productTypes}
                  loadingPTs={loadingPTs}
                  onLoadProductTypes={handleLoadProductTypes}
                  attributes={attributes}
                  loadingAttrs={loadingAttrs}
                  onLoadAttributes={handleLoadAttributes}
                  onAddAttribute={(ptId, layer) => {
                    setAttrFormProductTypeId(ptId);
                    setAttrFormLayer(layer);
                    setEditingAttr(null);
                    setShowAttrForm(true);
                  }}
                  onEditAttribute={(attr) => {
                    setAttrFormProductTypeId(attr.product_type_id || 0);
                    setAttrFormLayer(attr.layer);
                    setEditingAttr(attr);
                    setShowAttrForm(true);
                  }}
                  onDeleteAttribute={handleDeleteAttribute}
                  groups={groups}
                />
              ))}
            </div>
          </div>
        )}
      </PanelContent>
    </AdminLayout>
  );
}
