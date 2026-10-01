"use client";

import { Button } from "@/components/ui/Button";

import { useState, useRef, useEffect } from "react";
import { Plus, Save, X, RefreshCw, Globe, AtSign, Search, Sparkles } from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";

interface GhostRowFormProps {
	onCountryCreated?: () => void;
}

export default function GhostRowForm({ onCountryCreated }: GhostRowFormProps) {
	const addToast = useToastStore((state) => state.addToast);
	const [showForm, setShowForm] = useState(false);
	const [code, setCode] = useState("");
	const [name, setName] = useState("");
	const [currency, setCurrency] = useState("SAR");
	const [timezone, setTimezone] = useState("UTC");
	const [currencySymbol, setCurrencySymbol] = useState("");
	const [phoneCode, setPhoneCode] = useState("");
	const [language, setLanguage] = useState("en");
	const [isActive, setIsActive] = useState(true);
	const [creating, setCreating] = useState(false);

	// Auto-populate search state
	const [searchTerm, setSearchTerm] = useState("");
	const [searching, setSearching] = useState(false);

	const formRef = useRef<HTMLDivElement>(null);

	useEffect(() => {
		if (showForm && formRef.current) {
			const firstInput = formRef.current.querySelector('input[type="text"]') as HTMLInputElement | null;
			firstInput?.focus();
		}
	}, [showForm]);

	const applyAutoPopulate = (data: any) => {
		// The backend returns an UNWRAPPED country payload.
		if (data?.code) setCode(String(data.code).toUpperCase());
		if (data?.name) setName(data.name);
		if (data?.currency) setCurrency(String(data.currency).toUpperCase());
		if (data?.currency_symbol) setCurrencySymbol(data.currency_symbol);
		if (data?.phone_code) setPhoneCode(data.phone_code);
		if (data?.language) setLanguage(data.language);
		if (data?.timezone) setTimezone(data.timezone || "UTC");
		// Tax overlay (suggested_* aliases kept for backwards-compat)
		if (data?.suggested_tax_rate != null) {
			// no-op for the quick-create form, but surface nothing breaking
		}
		addToast(`Auto-populated ${data?.name || data?.code || "country"}`, "success");
	};

	const runSearch = async () => {
		const term = searchTerm.trim();
		if (!term) {
			addToast("Enter a country name or code to search", "warning");
			return;
		}
		setSearching(true);
		try {
			const response = await apiFetch("/admin/countries/auto-populate", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ search_term: term }),
			});
			const data = await parseJsonResponse(response);
			if (!response.ok) {
				throw new Error(data?.detail || "Auto-populate failed");
			}
			applyAutoPopulate(data);
		} catch (err: any) {
			addToast(err?.message || "Auto-populate failed", "error");
		} finally {
			setSearching(false);
		}
	};

	const handleSubmit = async () => {
		if (!code.trim() || !name.trim() || !currency.trim() || !timezone.trim()) {
			addToast("Code, name, currency, and timezone are required", "warning");
			return;
		}

		setCreating(true);
		try {
			const response = await apiFetch("/admin/countries", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					code: code.trim().toUpperCase(),
					name: name.trim(),
					currency: currency.trim().toUpperCase(),
					timezone: timezone.trim(),
					currency_symbol: currencySymbol.trim() || null,
					phone_code: phoneCode.trim() || null,
					language: language.trim(),
					is_active: isActive,
				}),
			});

			const data = await parseJsonResponse(response);
			if (!response.ok) {
				throw new Error(data?.detail || "Failed to create country");
			}

			addToast(`Country ${code.trim().toUpperCase()} created successfully`, "success");
			setCode("");
			setName("");
			setCurrency("SAR");
			setTimezone("UTC");
			setCurrencySymbol("");
			setPhoneCode("");
			setLanguage("en");
			setIsActive(true);
			setSearchTerm("");
			setShowForm(false);
			onCountryCreated?.();
		} catch (err: any) {
			addToast(err.message, "error");
		} finally {
			setCreating(false);
		}
	};

	if (!showForm) {
		return (
			<div className="mb-3">
				<Button variant="primary" className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold hover:opacity-90 transition shadow" type="button"
					onClick={() => setShowForm(true)}
					data-testid="add-country-button"
				>
					<Plus className="h-3.5 w-3.5" />
					Add Country
				</Button>
			</div>
		);
	}

	return (
		<div
			ref={formRef}
			className="mb-4 border-2 border-primary/30 rounded-lg bg-primary/5 overflow-hidden animate-in slide-in-from-top-2 duration-200"
			data-testid="new-country-modal"
		>
			<div className="p-4 space-y-3">
				<div className="flex items-center justify-between">
					<div className="flex items-center gap-2">
						<Globe className="h-4 w-4 text-primary" />
						<span className="text-xs font-bold text-text uppercase tracking-wide">New Country (Quick Create)</span>
					</div>
					<button
						type="button"
						onClick={() => setShowForm(false)}
						className="text-text-muted hover:text-text transition"
					>
						<X className="h-4 w-4" />
					</button>
				</div>

				{/* ── Auto-populate from web ───────────────────────────────── */}
				<div className="rounded-lg border border-border bg-surface p-3 space-y-2">
					<div className="flex items-center gap-1.5 text-[11px] font-bold text-text uppercase tracking-wide">
						<Sparkles className="h-3.5 w-3.5 text-primary" />
						Auto-populate from web
					</div>
					<div className="flex flex-col gap-2 sm:flex-row sm:items-center">
						<input
							type="text"
							className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text"
							value={searchTerm}
							onChange={(e) => setSearchTerm(e.target.value)}
							placeholder="Type a country name or code"
							aria-label="Search country"
							data-testid="auto-populate-search-input"
							onKeyDown={(e) => {
								if (e.key === "Enter") {
									e.preventDefault();
									runSearch();
								}
							}}
						/>
						<Button variant="secondary" type="button"
							onClick={runSearch}
							disabled={searching}
							className="inline-flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold transition"
							data-testid="auto-populate-search-button"
						>
							{searching ? (
								<RefreshCw className="h-3.5 w-3.5 animate-spin" />
							) : (
								<Search className="h-3.5 w-3.5" />
							)}
							{searching ? "Searching..." : "Search"}
						</Button>
					</div>
					<p className="text-[10px] text-text-faint">
						Search a country name or ISO code (e.g. &quot;Saudi Arabia&quot; or &quot;SA&quot;) to auto-fill the form with researched details.
					</p>
				</div>

				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
					<label className="space-y-1 text-[10px] text-text-muted">
						<span className="flex items-center gap-1">
							Code *
						</span>
						<input
							type="text"
							className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text font-mono"
							value={code}
							onChange={(e) => setCode(e.target.value.toUpperCase())}
							placeholder="AE"
							maxLength={10}
							required
							aria-label="Country Code"
							data-testid="ghost-code-input"
						/>
					</label>

					<label className="space-y-1 text-[10px] text-text-muted">
						Name *
						<input
							type="text"
							className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text"
							value={name}
							onChange={(e) => setName(e.target.value)}
							placeholder="United Arab Emirates"
							required
							aria-label="Country Name"
							data-testid="ghost-name-input"
						/>
					</label>

					<label className="space-y-1 text-[10px] text-text-muted">
						Currency *
						<input
							type="text"
							className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text font-mono"
							value={currency}
							onChange={(e) => setCurrency(e.target.value.toUpperCase())}
							placeholder="AED"
							maxLength={3}
							required
							aria-label="Currency Code"
							data-testid="ghost-currency-input"
						/>
					</label>

					<label className="space-y-1 text-[10px] text-text-muted">
						Timezone *
						<input
							type="text"
							className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text font-mono"
							value={timezone}
							onChange={(e) => setTimezone(e.target.value)}
							placeholder="Asia/Dubai"
							required
							aria-label="Timezone"
							data-testid="ghost-timezone-input"
						/>
					</label>

					<label className="space-y-1 text-[10px] text-text-muted">
						Currency Symbol
						<input
							type="text"
							className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text"
							value={currencySymbol}
							onChange={(e) => setCurrencySymbol(e.target.value)}
							placeholder="د.إ"
							aria-label="Currency Symbol"
						/>
					</label>

					<label className="space-y-1 text-[10px] text-text-muted">
						Phone Code
						<div className="relative">
							<AtSign className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-text-muted" />
							<input
								type="text"
								className="w-full rounded border border-border bg-surface pl-7 px-2 py-1.5 text-sm text-text"
								value={phoneCode}
								onChange={(e) => setPhoneCode(e.target.value)}
								placeholder="+971"
								aria-label="Phone Code"
							/>
						</div>
					</label>

					<label className="space-y-1 text-[10px] text-text-muted">
						Language
						<select
							className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text"
							value={language}
							onChange={(e) => setLanguage(e.target.value)}
							aria-label="Language"
						>
							<option value="en">English</option>
							<option value="ar">Arabic</option>
						</select>
					</label>

					<label className="space-y-1 text-[10px] text-text-muted">
						Status
						<select
							className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text"
							value={isActive ? "active" : "inactive"}
							onChange={(e) => setIsActive(e.target.value === "active")}
							aria-label="Status"
						>
							<option value="active">Active</option>
							<option value="inactive">Inactive</option>
						</select>
					</label>
				</div>

				<div className="flex justify-end gap-2 pt-2 border-t border-border/40">
					<button
						type="button"
						onClick={() => setShowForm(false)}
						className="rounded-lg border border-border px-3 py-2 text-xs font-semibold text-text-muted hover:bg-surface-2 transition"
					>
						Cancel
					</button>
					<Button variant="primary" type="button"
						onClick={handleSubmit}
						disabled={creating}>
						{creating ? (
							<RefreshCw className="h-3.5 w-3.5 animate-spin" />
						) : (
							<Save className="h-3.5 w-3.5" />
						)}
						{creating ? "Creating..." : "Create Country"}
					</Button>
				</div>
			</div>
		</div>
	);
}
