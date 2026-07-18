"use client";

import { Button } from "@/components/ui/Button";

import { useState, useCallback, useEffect, useRef } from 'react';
import { Copy, Wand2, AlertCircle, Plus, Trash2 } from '@/lib/icons';

interface VariantCell {
  stock: string;
  price: string;
  sku: string;
}

interface SmartVariantMatrixProps {
  colors: string[];
  sizes: string[];
  initialValues?: Record<string, Record<string, VariantCell>>;
  onChange: (values: Record<string, Record<string, VariantCell>>) => void;
  onTotalChange: (total: number) => void;
}

export default function SmartVariantMatrix({
  colors: initialColors,
  sizes: initialSizes,
  initialValues,
  onChange,
  onTotalChange,
}: SmartVariantMatrixProps) {
  const [colors, setColors] = useState<string[]>(initialColors.length > 0 ? initialColors : ['Default']);
  const [sizes, setSizes] = useState<string[]>(initialSizes.length > 0 ? initialSizes : ['One Size']);
  const [values, setValues] = useState<Record<string, Record<string, VariantCell>>>(initialValues || {});
  const [newColor, setNewColor] = useState('');
  const [newSize, setNewSize] = useState('');
  const [warnings, setWarnings] = useState<string[]>([]);
  const didAutoFill = useRef(false);

  // Smart default-seeding: when the board opens (or colors/sizes change) and
  // nothing has been entered yet, pre-fill sensible stock so the supplier only
  // has to tweak instead of typing every cell. Runs once per mount.
  useEffect(() => {
    if (didAutoFill.current) return;
    const hasStock = (val: Record<string, VariantCell>) => Object.values(val).some(c => (parseInt(c.stock) || 0) > 0);
    const anyStock = Object.values(values).some(hasStock);
    if (anyStock) { didAutoFill.current = true; return; }
    if (colors.length && sizes.length) {
      const next: Record<string, Record<string, VariantCell>> = { ...values };
      for (const color of colors) {
        if (!next[color]) next[color] = {};
        for (const size of sizes) {
          const suggested = size === 'S' ? 50 : size === 'M' ? 100 : size === 'L' ? 100
            : size === 'XL' ? 25 : size === 'XXL' ? 15 : size === 'XS' ? 30 : 50;
          if (!next[color][size] || !next[color][size].stock) {
            next[color][size] = { stock: String(suggested), price: '', sku: '' };
          }
        }
      }
      setValues(next);
      onChange(next);
      didAutoFill.current = true;
    }
  }, [colors, sizes, values, onChange]);

  const getCell = (color: string, size: string): VariantCell => {
    return values[color]?.[size] || { stock: '', price: '', sku: '' };
  };

  const setCell = (color: string, size: string, field: keyof VariantCell, value: string) => {
    setValues(prev => {
      const next = { ...prev };
      if (!next[color]) next[color] = {};
      if (!next[color][size]) next[color][size] = { stock: '', price: '', sku: '' };
      next[color] = { ...next[color], [size]: { ...next[color][size], [field]: value } };
      onChange(next);
      // Calculate total
      const total = Object.values(next).reduce((sum, row) =>
        sum + Object.values(row).reduce((r, cell) => r + (parseInt(cell.stock) || 0), 0), 0);
      onTotalChange(total);
      // Validate
      const warns: string[] = [];
      for (const [c, row] of Object.entries(next)) {
        for (const [s, cell] of Object.entries(row)) {
          const st = parseInt(cell.stock) || 0;
          if (st > 0 && st < 5) warns.push(`${c} ${s}: low stock (${st})`);
          if (st > 1000) warns.push(`${c} ${s}: high stock (${st})`);
        }
      }
      setWarnings(warns.slice(0, 3));
      return next;
    });
  };

  const copyFromFirst = useCallback(() => {
    if (colors.length < 2) return;
    const firstColor = colors[0];
    const firstRow = values[firstColor];
    if (!firstRow) return;
    for (let i = 1; i < colors.length; i++) {
      const c = colors[i];
      setValues(prev => {
        const next = { ...prev };
        if (!next[c]) next[c] = {};
        for (const [size, cell] of Object.entries(firstRow)) {
          if (!next[c][size]) next[c][size] = { stock: cell.stock, price: cell.price, sku: '' };
        }
        return next;
      });
    }
  }, [colors, values]);

  const autoFillSuggested = useCallback(() => {
    for (const color of colors) {
      for (const size of sizes) {
        const cell = getCell(color, size);
        if (!cell.stock) {
          const suggested = size === 'S' ? 50 : size === 'M' ? 100 : size === 'L' ? 100 : size === 'XL' ? 25 : 50;
          setCell(color, size, 'stock', String(suggested));
        }
      }
    }
  }, [colors, sizes]);

  const totalStock = Object.values(values).reduce((sum, row) =>
    sum + Object.values(row).reduce((r, cell) => r + (parseInt(cell.stock) || 0), 0), 0);

  return (
    <div className="space-y-4">
      {/* Header with actions */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-800">Variant Stock Matrix</h3>
        <div className="flex items-center gap-2">
          <button onClick={copyFromFirst}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200">
            <Copy className="w-3.5 h-3.5" /> Copy from 1st
          </button>
          <Button variant="primary" onClick={autoFillSuggested}>
            <Wand2 className="w-3.5 h-3.5" /> Auto-fill
          </Button>
        </div>
      </div>

      {/* Add color / size row */}
      <div className="flex items-center gap-2">
        <input placeholder="Add color" value={newColor}
          onChange={(e) => setNewColor(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && newColor.trim()) {
            setColors(prev => [...prev, newColor.trim()]);
            setNewColor('');
          }}}
          className="flex-1 px-3 py-1.5 text-xs border border-gray-200 rounded-lg focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none" />
        <input placeholder="Add size" value={newSize}
          onChange={(e) => setNewSize(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && newSize.trim()) {
            setSizes(prev => [...prev, newSize.trim()]);
            setNewSize('');
          }}}
          className="flex-1 px-3 py-1.5 text-xs border border-gray-200 rounded-lg focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none" />
        <Button variant="primary" className="p-1.5 text-primary rounded-lg transition-colors" onClick={() => {
          if (newColor.trim()) { setColors(prev => [...prev, newColor.trim()]); setNewColor(''); }
          if (newSize.trim()) { setSizes(prev => [...prev, newSize.trim()]); setNewSize(''); }
        }}>
          <Plus className="w-4 h-4" />
        </Button>
      </div>

      {/* Matrix table */}
      <div className="overflow-x-auto rounded-xl border border-gray-200">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left py-2.5 px-3 font-medium text-gray-500 min-w-[80px]">Color \ Size</th>
              {sizes.map(size => (
                <th key={size} className="py-2.5 px-2 font-medium text-gray-500 text-center min-w-[90px]">
                  <div className="flex items-center justify-center gap-1">
                    {size}
                    <button onClick={() => setSizes(prev => prev.filter(s => s !== size))}
                      className="text-gray-300 hover:text-danger transition-colors">
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </th>
              ))}
              <th className="py-2.5 px-2 font-medium text-gray-500 text-center min-w-[60px]">Total</th>
            </tr>
          </thead>
          <tbody>
            {colors.map(color => (
              <tr key={color} className="border-b border-gray-100 hover:bg-gray-50/50 transition-colors">
                <td className="py-2 px-3 font-medium text-gray-600">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded-full border border-gray-200" style={{ backgroundColor: color.toLowerCase() }} />
                    {color}
                    <button onClick={() => setColors(prev => prev.filter(c => c !== color))}
                      className="text-gray-300 hover:text-danger transition-colors ml-1">
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </td>
                {sizes.map(size => (
                  <td key={`${color}-${size}`} className="py-1.5 px-1">
                    <input type="number" min="0" placeholder="0"
                      value={getCell(color, size).stock}
                      onChange={(e) => setCell(color, size, 'stock', e.target.value)}
                      className="w-full px-2 py-1.5 text-center border border-gray-100 rounded-lg text-xs focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none bg-white hover:border-gray-200 transition-colors" />
                  </td>
                ))}
                <td className="py-2 px-2 text-center font-medium text-gray-700">
                  {Object.values(values[color] || {}).reduce((s, c) => s + (parseInt(c.stock) || 0), 0)}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="bg-primary/5 border-t border-gray-200">
              <td className="py-2.5 px-3 font-medium text-gray-600">Total</td>
              {sizes.map(size => (
                <td key={`total-${size}`} className="py-2.5 px-2 text-center font-semibold text-gray-700">
                  {colors.reduce((sum, color) => sum + (parseInt(values[color]?.[size]?.stock) || 0), 0)}
                </td>
              ))}
              <td className="py-2.5 px-2 text-center font-bold text-primary">{totalStock}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="space-y-1">
          {warnings.map((w, i) => (
            <div key={i} className="flex items-start gap-1.5 text-xs text-amber-600">
              <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-gray-400 text-right">Total Stock: <strong className="text-gray-700">{totalStock} units</strong></p>
    </div>
  );
}
