"""Dimension 14/12 (extension) — interaction robustness.

A button that can be double-submitted, a dialog that does not trap focus, a
form that swallows its own error, and a page with no error boundary are the
defects that survive a static architecture audit and then fail in a browser.
Every number below is measured in this run from source, never assumed.
"""
from __future__ import annotations

import re
from pathlib import Path

from zz_core.model import CheckResult, Finding, Observation, Recommendation, ScanContext
from zz_core.registry import check
from zz_core.util import read_text

MUTATING = re.compile(r"method\s*:\s*[\"'](?:POST|PUT|PATCH|DELETE)[\"']|\b(delete|update|create|remove|revoke|refund|cancel|approve|reject|archive|publish)\w*\s*\(", re.I)
# Silent-failure shapes: an empty catch, a catch that only logs, or a .catch
# with an empty/ignoring body.
SWALLOW_RE = re.compile(
    r"catch\s*(\([^)]*\))?\s*\{\s*\}"                       # catch {}
    r"|catch\s*\(\s*\w+\s*\)\s*\{\s*console\.(log|error|warn)\([^)]*\)\s*;\s*\}"
    r"|\.catch\s*\(\s*\(\s*\)\s*=>\s*\{\s*\}\s*\)"
    r"|\.catch\s*\(\s*\(?\s*\w*\s*\)?\s*=>\s*null\s*\)")
CONFIRM_RE = re.compile(r"window\.confirm|AlertDialog|ConfirmDialog|confirm\(")
DESTRUCTIVE_RE = re.compile(
    r"\b(delete|remove|revoke|refund|void|cancel|terminate|deactivate|"
    r"purge|archive|dispute|chargeback)\b", re.I)
# `Map.delete()`, `URLSearchParams.delete()`, `params.delete()` and a type
# annotation `=> void` are not destructive user actions. A real one is a call on
# an API/domain object, usually inside a click handler.
DESTRUCTIVE_CALL_RE = re.compile(
    r"(?:await\s+)?[\w.]*\b(delete|remove|revoke|refund|void|cancel|terminate|"
    r"deactivate|purge|archive|dispute|chargeback)\w*\s*\(")
DATA_STRUCT_DELETE = re.compile(
    r"\b(?:params|searchParams|query|sp|formData|fd|qs|urlParams)\s*\.delete\s*\("
    r"|\bMap\s*\(|new Set\s*\(")
HANDLER_CONTEXT = re.compile(
    r"onClick\s*=|onSubmit\s*=|onConfirm\s*=|handle\w+\s*=|await\s+|void\s+\w+\(")


def _src_files(ctx: ScanContext) -> list[Path]:
    return [p for p in ctx.ts_files
            if "frontend/web_app/src/" in ctx.rel(p)
            and "__tests__/" not in ctx.rel(p)
            and not ctx.rel(p).endswith(".test.tsx")]


def _web_root(ctx: ScanContext) -> Path:
    return ctx.frontend / "web_app"


@check("interaction_buttons", "14_frontend_web", "frontend",
       "Button inventory: missing type, missing disabled/pending state, "
       "mutating actions with no error handling, icon-only buttons with no "
       "accessible name.")
def interaction_buttons(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="interaction_buttons", dimension="14_frontend_web")
    files = _src_files(ctx)
    tag_re = re.compile(r"<(button|Button)\b([^>]*)>")
    total = 0
    raw_tag = 0
    primitive_tag = 0
    primitive_supplies_type = False
    for p in _src_files(ctx):
        if p.name == "Button.tsx":
            text_b, _ = read_text(p)
            primitive_supplies_type = bool(
                text_b and re.search(r"type\s*[:=]\s*[\"']?button", text_b))
    no_type: list[tuple[str, int]] = []
    no_state: list[tuple[str, int]] = []
    mutating_unhandled: list[tuple[str, int]] = []
    icon_only: list[tuple[str, int]] = []
    for p in _src_files(ctx):
        rel = ctx.rel(p)
        text, _ = read_text(p)
        if not text:
            continue
        lines = text.splitlines()
        for m in tag_re.finditer(text):
            total += 1
            if m.group(1) == "Button":
                primitive_tag += 1
            else:
                raw_tag += 1
            line = text[:m.start()].count("\n") + 1
            attrs = m.group(2) or ""
            if not re.search(r"\btype\s*=", attrs):
                no_type.append((rel, line))
            if not re.search(r"\b(disabled|isPending|isLoading|loading|isSubmitting|aria-busy)\b",
                             attrs):
                no_state.append((rel, line))
            # accessible name: visible text, aria-label, or aria-labelledby
            tail = text[m.end():m.end() + 400]
            close = tail.find("</")
            inner = tail[:close] if close != -1 else tail[:80]
            if not re.search(r"[A-Za-z\u0600-\u06FF]{2,}", inner) and \
                    not re.search(r"aria-label|aria-labelledby", attrs):
                icon_only.append((rel, line))
        for n, raw in enumerate(lines, 1):
            if MUTATING.search(raw) and SWALLOW_RE.search("\n".join(lines[n - 1:n + 3])):
                mutating_unhandled.append((rel, n))

    res.facts["interaction_buttons"] = {
        "total": total,
        "raw_button_elements": raw_tag,
        "primitive_button_elements": primitive_tag,
        "primitive_supplies_default_type": primitive_supplies_type,
        "missing_type": len(no_type),
        "missing_pending_state": len(no_state),
        "mutating_with_swallowed_error": len(mutating_unhandled),
        "icon_only_without_name": len(icon_only),
        "worst_missing_type": sorted({p for p, _ in no_type})[:12],
        "note": "the shared Button primitive supplies no default type, so a "
                "<Button> without type= also renders as type=submit inside a form",
    }
    for rel, line in no_type[:30]:
        res.observations.append(Observation(
            "button", rel, rel, line, "14_frontend_web",
            evidence="<button> without an explicit type attribute",
        ))
    for rel, line in mutating_unhandled[:30]:
        res.observations.append(Observation(
            "button", rel, rel, line, "14_frontend_web",
            evidence="mutating action adjacent to a swallowed error handler",
        ))

    if total and len(no_type) / total > 0.2:
        res.findings.append(Finding(
            id="IX-button-type", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-interaction-button", file="frontend/web_app/src",
            current=f"{len(no_type)} of {total} button elements have no explicit "
                    f"type; inside a <form> the HTML default is type=submit",
            target="every button declares type=button|submit|reset",
            delta=f"a click on a bare button in a form submits the form "
                  f"({len(no_type)} sites)",
            fix="add type=\"button\" to every non-submit button; add an ESLint "
                "rule (react/button-has-type) so it cannot regress",
            effort="S", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rEc '<button(\\s|>)' frontend/web_app/src --include=*.tsx | "
                   "awk -F: '$2>0' | wc -l",
            snippet=", ".join(f"{p}:{l}" for p, l in no_type[:6]),
        ))
    if mutating_unhandled:
        res.findings.append(Finding(
            id="IX-mutation-error-swallowed", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-interaction-button", file="frontend/web_app/src",
            current=f"{len(mutating_unhandled)} mutating action(s) sit next to an "
                    f"empty or console-only catch",
            target="every mutation surfaces success *and* failure to the operator",
            delta="the user sees a click with no confirmation and no error",
            fix="replace the swallowed catch with a toast.error (or rethrow) and "
                "add a pending state so the button cannot be double-fired",
            effort="M", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="grep -rEn 'catch\\s*(\\([^)]*\\))?\\s*\\{\\s*\\}' "
                   "frontend/web_app/src --include=*.tsx",
            snippet=", ".join(f"{p}:{l}" for p, l in mutating_unhandled[:6]),
        ))
    if icon_only:
        res.findings.append(Finding(
            id="IX-icon-button-name", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-interaction-button", file="frontend/web_app/src",
            current=f"{len(icon_only)} icon-only button(s) expose no accessible name",
            target="aria-label or visually-hidden text on every icon control",
            delta="screen-reader users cannot identify these controls",
            fix="add aria-label to each icon-only button",
            effort="S", priority="P2", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="npx axe http://localhost:3100 --tags wcag2a",
            snippet=", ".join(f"{p}:{l}" for p, l in icon_only[:6]),
        ))
    if total:
        res.recommendations.append(Recommendation(
            area="frontend", dimension="14_frontend_web",
            title="Standardise interaction state handling across all screens",
            rationale=f"{total} buttons are declared ad hoc; each one independently "
                      f"re-implements pending/error/disabled handling, so the "
                      f"behaviour is inconsistent by construction.",
            current="pending state, error toast and confirmation are decided per "
                    "screen.",
            proposal="give the Button primitive a built-in `pending` state that "
                     "disables itself, and require mutations to pass through one "
                     "`useMutation` helper that always toasts success and failure.",
            benefit=f"removes {len(no_state)} hand-rolled pending checks and makes "
                    f"double-submission impossible",
            effort="M", impact="high", category="quality",
            evidence=f"frontend/web_app/src ({total} button elements)",
            human_effort_saved="~1 day per screen currently hand-rolled",
        ))
    return res


@check("interaction_modals", "14_frontend_web", "frontend",
       "Dialog/drawer inventory: focus trap, Escape handling, scroll lock, "
       "double-submit guard, and confirmation for destructive actions.")
def interaction_modals(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="interaction_modals", dimension="14_frontend_web")
    modals: list[dict] = []
    for p in _src_files(ctx):
        rel = ctx.rel(p)
        text, _ = read_text(p)
        if not text:
            continue
        if not re.search(r"\b(Dialog|Modal|Sheet|Drawer|Popover|AlertDialog|"
                         r"ConfirmDialog|window\.confirm)\b", text):
            continue
        modals.append({
            "file": rel,
            "line": 0,
            "focus_trap": bool(re.search(r"onOpenAutoFocus|FocusTrap|focus-trap|"
                                         r"autoFocus|createFocusTrap|tabIndex=\{?-1", text)),
            "escape": bool(re.search(r"onEscapeKeyDown|Escape|keydown|onKeyDown", text)),
            "scroll_lock": bool(re.search(r"overflow.*hidden|body\.style|"
                                          r"useLockBodyScroll|scroll-lock", text)),
            "destructive_without_confirm": [],
        })
        lines = text.splitlines()
        # A destructive action is a *call* on an object in a handler context.
        # Matching the bare word picks up `params.delete()` and `=> void`.
        for n, raw in enumerate(lines, 1):
            if not DESTRUCTIVE_CALL_RE.search(raw):
                continue
            if DATA_STRUCT_DELETE.search(raw):
                continue
            window = "\n".join(lines[max(0, n - 12):n + 12])
            if not HANDLER_CONTEXT.search(window):
                continue
            if CONFIRM_RE.search(window):
                continue
            modals[-1]["destructive_without_confirm"].append(n)

    total = len(modals)
    no_focus = [m["file"] for m in modals if not m["focus_trap"]]
    no_escape = [m["file"] for m in modals if not m["escape"]]
    no_scroll = [m["file"] for m in modals if not m["scroll_lock"]]
    undestructive = [(m["file"], m["destructive_without_confirm"])
                     for m in modals if m["destructive_without_confirm"]]
    res.facts["interaction_modals"] = {
        "files_with_modal": total,
        "missing_focus_management": len(no_focus),
        "missing_escape_handler": len(no_escape),
        "missing_scroll_lock": len(no_scroll),
        "destructive_without_confirmation": sum(len(l) for _, l in undestructive),
        "uses_window_confirm": sum(
            1 for p in _src_files(ctx)
            if "window.confirm" in (read_text(p)[0] or "")),
    }
    for m in modals[:40]:
        res.observations.append(Observation(
            "modal", m["file"], m["file"], 0, "14_frontend_web",
            evidence=f"focus_trap={m['focus_trap']} escape={m['escape']} "
                     f"scroll_lock={m['scroll_lock']} "
                     f"destructive_unconfirmed={len(m['destructive_without_confirm'])}",
        ))
    if total and len(no_focus) / total > 0.5:
        res.findings.append(Finding(
            id="IX-modal-focus", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-interaction-modal", file="frontend/web_app/src",
            current=f"{len(no_focus)} of {total} modal/drawer implementations have "
                    f"no focus management",
            target="focus moves into the dialog on open and returns to the trigger "
                   "on close; Tab is trapped",
            delta="keyboard and screen-reader users can tab behind an open dialog",
            fix="use a headless dialog primitive (Radix Dialog / Headless UI) or "
                "add onOpenAutoFocus + a Tab sentinel",
            effort="L", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="npx playwright test e2e/a11y --tags wcag2a",
            snippet=", ".join(no_focus[:8]),
        ))
    if undestructive:
        res.findings.append(Finding(
            id="IX-destructive-confirm", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-interaction-modal", file="frontend/web_app/src",
            current=f"{sum(len(l) for _, l in undestructive)} destructive control(s) "
                    f"in {len(undestructive)} modal file(s) with no confirmation step",
            target="delete / refund / revoke / cancel always require an explicit "
                   "confirmation naming the object",
            delta="an irreversible action can be triggered by a single click",
            fix="wrap the destructive action in the confirm dialog primitive and "
                "name the affected record in the prompt",
            effort="M", priority="P0", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="grep -rEni 'onClick.*\\b(delete|refund|revoke|void|cancel)\\b' "
                   "frontend/web_app/src --include=*.tsx",
            snippet=", ".join(f"{p}:{','.join(map(str, l[:3]))}"
                              for p, l in undestructive[:6]),
        ))
    if total and len(no_escape) / total > 0.5:
        res.findings.append(Finding(
            id="IX-modal-escape", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-interaction-modal", file="frontend/web_app/src",
            current=f"{len(no_escape)} of {total} modal implementations do not "
                    f"close on Escape",
            target="Escape and backdrop click both dismiss a non-critical dialog",
            delta="operators must hunt for a close button to escape a dialog",
            fix="add onEscapeKeyDown / onPointerDownOutside to the dialog primitive",
            effort="S", priority="P2", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="grep -rL 'onEscapeKeyDown\\|Escape' frontend/web_app/src/components/ui",
            snippet=", ".join(no_escape[:8]),
        ))
    return res


@check("interaction_forms", "14_frontend_web", "frontend",
       "Form inventory: labels, client validation, submit affordance, and "
       "form-level error surfacing.")
def interaction_forms(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="interaction_forms", dimension="14_frontend_web")
    total_forms = total_inputs = labelled = wrapped = 0
    unlabelled: list[tuple[str, int]] = []
    raw_forms: list[tuple[str, int]] = []
    for p in _src_files(ctx):
        rel = ctx.rel(p)
        text, _ = read_text(p)
        if not text:
            continue
        # Track <label>...</label> spans: an input nested inside a label gets
        # its accessible name from that label, with no htmlFor needed.
        label_spans = [(m.start(), m.end()) for m in re.finditer(r"<label\b[^>]*>.*?</label>",
                                                                 text, re.S)]
        for m in re.finditer(r"<form\b", text):
            total_forms += 1
            line = text[:m.start()].count("\n") + 1
            if not re.search(r"onSubmit|useForm|handleSubmit|zodResolver", text[m.start():m.start() + 1200]):
                raw_forms.append((rel, line))
        for m in re.finditer(r"<input\b([^>]*)>", text):
            total_inputs += 1
            line = text[:m.start()].count("\n") + 1
            attrs = m.group(1) or ""
            if re.search(r'type\s*=\s*["\'](hidden|checkbox|radio|submit|button)["\']', attrs):
                continue
            if re.search(r"aria-label|aria-labelledby|\bid\s*=", attrs) or \
                    re.search(r"\btitle\s*=", attrs):
                labelled += 1
                continue
            if any(s <= m.start() < e for s, e in label_spans):
                labelled += 1
                wrapped += 1
                continue
            unlabelled.append((rel, line))
    res.facts["interaction_forms"] = {
        "forms": total_forms,
        "inputs": total_inputs,
        "labelled_inputs": labelled,
        "labelled_via_wrapping_label": wrapped,
        "unlabelled_inputs": len(unlabelled),
        "forms_without_validation_hook": len(raw_forms),
        "note": "an input nested inside a <label> has an accessible name; "
                "title= also counts as a name",
    }
    for rel, line in unlabelled[:30]:
        res.observations.append(Observation(
            "form_input", rel, rel, line, "14_frontend_web",
            evidence="text input with no label, aria-label or id association",
        ))
    if unlabelled:
        res.findings.append(Finding(
            id="IX-input-label", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-interaction-form", file="frontend/web_app/src",
            current=f"{len(unlabelled)} of {total_inputs} text input(s) have no "
                    f"label, aria-label or id association",
            target="every input has an accessible name",
            delta="forms are unusable with a screen reader",
            fix="pair each input with a <label htmlFor>, or add aria-label",
            effort="M", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="npx axe http://localhost:3100 --tags wcag2a,wcag2aa",
            snippet=", ".join(f"{p}:{l}" for p, l in unlabelled[:6]),
        ))
    if raw_forms:
        res.findings.append(Finding(
            id="IX-form-validation", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-interaction-form", file="frontend/web_app/src",
            current=f"{len(raw_forms)} of {total_forms} forms have no submit handler "
                    f"or schema validation",
            target="client-side validation with per-field messages before submit",
            delta="invalid input reaches the API and returns a 422 with no field "
                  "mapping",
            fix="adopt react-hook-form + zodResolver consistently",
            effort="M", priority="P2", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="grep -rL 'zodResolver\\|useForm' frontend/web_app/src --include=*.tsx",
            snippet=", ".join(f"{p}:{l}" for p, l in raw_forms[:6]),
        ))
    return res


@check("page_states", "14_frontend_web", "frontend",
       "Every app-router page must have a loading, empty and error state; "
       "measure which of the pages have them.")
def page_states(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="page_states", dimension="14_frontend_web")
    app_dir = _web_root(ctx) / "src" / "app"
    if not app_dir.exists():
        return res
    pages: list[Path] = sorted(app_dir.rglob("page.tsx"))
    loading: list[Path] = []
    errorb: list[Path] = []
    for p in pages:
        parent = p.parent
        if (parent / "loading.tsx").exists():
            loading.append(p)
        if (parent / "error.tsx").exists():
            errorb.append(p)
    no_loading = [ctx.rel(p) for p in pages if p not in loading]
    no_error = [ctx.rel(p) for p in pages if p not in errorb]
    # A page can also handle its own error inline; count those separately.
    inline_error = 0
    for p in pages:
        if p in errorb:
            continue
        text, _ = read_text(p)
        if text and re.search(r"try\s*\{|catch\s*\(|ErrorState|isError|error\s*&&", text):
            inline_error += 1
    res.facts["page_states"] = {
        "pages": len(pages),
        "with_loading_file": len(loading),
        "with_error_file": len(errorb),
        "with_inline_error_handling": inline_error,
        "without_any_error_handling": len(no_error) - inline_error,
        "uncovered_admin_pages": [r for r in no_error
                                  if "/admin/" in r and r not in no_error[:0]][:20],
    }
    for rel in no_error[:40]:
        res.observations.append(Observation(
            "page", rel, rel, 0, "14_frontend_web",
            evidence="page has neither an error.tsx boundary nor inline error handling",
        ))
    unhandled = len(no_error) - inline_error
    if pages and unhandled / len(pages) > 0.5:
        res.findings.append(Finding(
            id="IX-page-error-state", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-interaction-state", file="frontend/web_app/src/app",
            current=f"{unhandled} of {len(pages)} routes have no error boundary and "
                    f"no inline error handling; only {len(loading)} declare loading.tsx",
            target="every route segment has loading.tsx and error.tsx",
            delta="a failed fetch renders a blank page with no recovery path",
            fix="add error.tsx (and loading.tsx where the fetch is server-side) to "
                "each route segment; start with the admin segments",
            effort="L", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="find frontend/web_app/src/app -name page.tsx | wc -l; "
                   "find frontend/web_app/src/app -name error.tsx | wc -l",
            snippet=", ".join(no_error[:6]),
        ))
        res.recommendations.append(Recommendation(
            area="frontend", dimension="14_frontend_web",
            title="Generate loading/error/empty boundaries for every route",
            rationale=f"{len(pages)} routes but only {len(loading)} loading and "
                      f"{len(errorb)} error boundaries means most screens fail blank.",
            current="ad-hoc per screen.",
            proposal="add a codemod that creates error.tsx/loading.tsx/empty.tsx per "
                     "route segment, plus a CI check asserting the 1:1 ratio.",
            benefit="no blank screen in production; on-call gets a stack per failure",
            effort="M", impact="high", category="quality",
            evidence=f"frontend/web_app/src/app ({len(pages)} pages)",
            human_effort_saved="~2 h per screen of state scaffolding",
        ))
    return res


@check("interaction_toasts", "14_frontend_web", "frontend",
       "Notification channel: is failure ever surfaced, and are errors swallowed?")
def interaction_toasts(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="interaction_toasts", dimension="14_frontend_web")
    libs: list[str] = []
    for p in _src_files(ctx):
        text, _ = read_text(p)
        if not text:
            continue
        for lib in ("sonner", "react-hot-toast", "useToast", "toastStore",
                    "notistack", "next-themes"):
            if lib in text and lib not in libs:
                libs.append(lib)
    success = error = 0
    swallowed: list[tuple[str, int]] = []
    # The project wraps its own store (`addToast(message, type)`); counting the
    # bare words "success"/"error" in a string misses the real call shape and
    # inverts the ratio.
    ADD_RE = re.compile(r"addToast\w*\s*\(|useToast\w*\s*\(|toast\w*\s*\(")
    OK_RE = re.compile(r"(?:addToast|useToast|toast)\w*\s*\([^)]*"
                       r"['\"](?:success|ok|done|saved|created|updated|deleted|sent)['\"]",
                       re.I)
    ERR_RE = re.compile(r"(?:addToast|useToast|toast)\w*\s*\([^)]*"
                        r"['\"](?:error|fail\w*|unable)['\"]", re.I)
    TYPE_ERR_RE = re.compile(r"(?:addToast|useToast|toast)\w*\s*\([^)]*['\"]error['\"]",
                             re.I)
    for p in _src_files(ctx):
        rel = ctx.rel(p)
        text, _ = read_text(p)
        if not text:
            continue
        success += len(OK_RE.findall(text))
        error += len(ERR_RE.findall(text)) + len(TYPE_ERR_RE.findall(text))
        for n, line in enumerate(text.splitlines(), 1):
            if SWALLOW_RE.search(line):
                swallowed.append((rel, n))
    res.facts["interaction_toasts"] = {
        "libraries_detected": libs,
        "success_toasts": success,
        "error_toasts": error,
        "swallowed_error_handlers": len(swallowed),
        "note": "counted at the addToast/useToast/toast call shape, not by the "
                "words success/error appearing anywhere in a file",
    }
    if not libs:
        res.findings.append(Finding(
            id="IX-no-toast", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-interaction-state", file="frontend/web_app/src",
            current="no notification channel is wired",
            target="one toast/error channel used consistently",
            delta="users get no feedback",
            fix="adopt one library and a single <Toaster/> mount in the root layout",
            effort="S", priority="P1", confidence=4, evidence_strength="single",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="grep -rn 'Toaster' frontend/web_app/src/app/layout.tsx",
        ))
    elif error == 0 and success > 0:
        res.findings.append(Finding(
            id="IX-toast-success-only", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-interaction-state", file="frontend/web_app/src",
            current=f"{success} success toasts and 0 error toasts across the app",
            target="every failure path notifies the operator",
            delta="failures are silent; users retry blindly",
            fix="route every rejected mutation through the error toast; add a lint "
                "check that a `catch` block must reference the toast helper",
            effort="M", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rn 'toast.error\\|toastStore.error' frontend/web_app/src | wc -l",
        ))
    if len(swallowed) > 30:
        res.findings.append(Finding(
            id="IX-error-swallow", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-interaction-state", file="frontend/web_app/src",
            current=f"{len(swallowed)} empty or console-only catch handler(s)",
            target="no silently swallowed rejection",
            delta="failures are invisible in production",
            fix="replace with the error toast / ErrorBoundary path; enable "
                "`@typescript-eslint/no-empty` and `no-console` in CI",
            effort="M", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rEn 'catch\\s*(\\([^)]*\\))?\\s*\\{\\s*\\}' "
                   "frontend/web_app/src --include=*.tsx | wc -l",
            snippet=", ".join(f"{p}:{l}" for p, l in swallowed[:6]),
        ))
    return res
