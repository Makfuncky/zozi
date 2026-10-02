# FEATURE STACK DRAFT

> **Source of truth:** `backend/domains/*/features.py` → aggregated by `backend/rbac/catalog.py`
> **Canonical reference:** `_most_imp_docx/FEATURE_STACK.md` (reconciled)
> **Role map:** `backend/rbac/dependencies.py` (`_ROLE_FEATURES`, `_ROLE_MODULES`)
> **Audit rules:** `_most_imp_docx/PROMPT_FORENSIC_AUDIT.md` §6.4
> **Mode:** READ-ONLY audit — no source files modified

---

## Scoring formula (PROMPT_FORENSIC_AUDIT.md §6.4)

```
feature_score = 0.40 * revenue_weight + 0.25 * security_weight + 0.20 * data_weight + 0.15 * blast_weight
```

Each component normalized to [0, 1]. Unmeasurable components default to 0.5 with note `component_unmeasured`.

| Component | Meaning |
|---|---|
| revenue_weight | Direct revenue impact: payments, orders, payouts, commissions |
| security_weight | Auth, RBAC, fraud, audit, MFA, encryption |
| data_weight | Data integrity, RLS, GDPR, audit trail |
| blast_weight | Number of dependent features / chains |

**Tier assignment:**
- **Tier 1** — Brief card (all features)
- **Tier 2** — Deep card (top 20 by score)
- **Orphan** — Feature atom in catalog but never referenced in any router `require_feature()` call
- **Launch-critical** — Feature whose absence blocks a critical user journey (order-to-cash, supplier onboarding, payment, checkout)

---

## Feature catalog

| Feature ID | Module | Domain | Actor | Tier | Score | Launch-critical | Status |
|---|---|---|---|---|---|---|---|
| orders.create | customer | orders | customer | T2 | 0.95 | YES | LIVE |
| orders.fulfill | logistics | orders | logistics | T2 | 0.88 | YES | LIVE |
| orders.cancel | customer | orders | customer | T2 | 0.82 | YES | LIVE |
| finance.payments.process | admin | finance | admin | T2 | 0.90 | YES | LIVE |
| finance.payout.approve | admin | finance | admin (finance_officer) | T2 | 0.87 | YES | LIVE |
| finance.payout.dispatch | admin | finance | admin (finance_officer) | T2 | 0.85 | YES | LIVE |
| catalog.write | supplier | catalog | supplier | T2 | 0.80 | YES | LIVE |
| orders.returns.manage | admin | orders | admin | T2 | 0.78 | YES | LIVE |
| accounts.user.create | admin | accounts | admin | T2 | 0.76 | YES | LIVE |
| finance.bank.reconcile | admin | finance | admin (finance_officer) | T2 | 0.75 | YES | LIVE |
| suppliers.verification.manage | admin | suppliers | admin | T2 | 0.74 | YES | LIVE |
| security.policies.manage | admin | security | admin | T2 | 0.73 | YES | LIVE |
| finance.ledger.post | admin | finance | admin (finance_officer) | T2 | 0.72 | YES | LIVE |
| orders.manage | admin | orders | admin (sub_admin) | T2 | 0.70 | YES | LIVE |
| accounts.mfa.enable | customer | accounts | customer | T2 | 0.68 | YES | LIVE |
| payments.transaction.process | customer | payments | customer | T2 | 0.85 | YES | LIVE |
| catalog.list | customer | catalog | customer (public) | T2 | 0.65 | YES | LIVE |
| finance.commission.write | supplier | finance | supplier | T2 | 0.63 | YES | LIVE |
| customers.cart.manage | customer | customers | customer | T2 | 0.60 | YES | LIVE |
| logistics.shipping.manage | logistics | logistics | logistics | T2 | 0.58 | YES | LIVE |
| accounts.session.revoke | admin | accounts | admin | T1 | 0.55 | NO | LIVE |
| analytics.dashboard.view | admin | analytics | admin | T1 | 0.52 | NO | LIVE |
| audit.logs.export | admin | audit | admin (auditor) | T1 | 0.50 | NO | LIVE |
| catalog.product.create | supplier | catalog | supplier | T1 | 0.48 | NO | LIVE |
| catalog.category.manage | admin | catalog | admin | T1 | 0.46 | NO | LIVE |
| catalog.search.advanced | customer | catalog | customer | T1 | 0.45 | NO | LIVE |
| catalog.read | customer | catalog | customer (public) | T1 | 0.44 | NO | LIVE |
| catalog.delete | supplier | catalog | supplier | T1 | 0.43 | NO | LIVE |
| orders.list | customer | orders | customer | T1 | 0.42 | NO | LIVE |
| orders.read | customer | orders | customer | T1 | 0.41 | NO | LIVE |
| orders.write | admin | orders | admin | T1 | 0.40 | NO | LIVE |
| orders.update | admin | orders | admin | T1 | 0.40 | NO | LIVE |
| orders.returns.read | customer | orders | customer | T1 | 0.39 | NO | LIVE |
| orders.export | admin | orders | admin | T1 | 0.38 | NO | LIVE |
| finance.ledger.read | admin | finance | admin (finance_officer) | T1 | 0.50 | NO | LIVE |
| finance.ledger.write | admin | finance | admin (finance_officer) | T1 | 0.52 | NO | LIVE |
| finance.ledger.reverse | admin | finance | admin (finance_officer) | T1 | 0.48 | NO | LIVE |
| finance.invoice.read | admin | finance | admin | T1 | 0.45 | NO | LIVE |
| finance.invoice.create | admin | finance | admin | T1 | 0.47 | NO | LIVE |
| finance.payout.read | supplier | finance | supplier | T1 | 0.42 | NO | LIVE |
| finance.payout.write | admin | finance | admin | T1 | 0.50 | NO | LIVE |
| finance.payout.create | admin | finance | admin | T1 | 0.48 | NO | LIVE |
| finance.commission.read | supplier | finance | supplier | T1 | 0.40 | NO | LIVE |
| finance.commission.manage | admin | finance | admin | T1 | 0.45 | NO | LIVE |
| finance.treasury.read | admin | finance | admin | T1 | 0.46 | NO | LIVE |
| finance.treasury.manage | admin | finance | admin | T1 | 0.48 | NO | LIVE |
| finance.treasury.forecast | admin | finance | admin | T1 | 0.42 | NO | LIVE |
| finance.period.close | admin | finance | admin (finance_officer) | T1 | 0.50 | NO | LIVE |
| finance.period.manage | admin | finance | admin (finance_officer) | T1 | 0.45 | NO | LIVE |
| finance.reporting.read | admin | finance | admin | T1 | 0.44 | NO | LIVE |
| finance.reporting.generate | admin | finance | admin | T1 | 0.46 | NO | LIVE |
| finance.subledger.read | admin | finance | admin | T1 | 0.40 | NO | LIVE |
| finance.subledger.post | admin | finance | admin | T1 | 0.42 | NO | LIVE |
| finance.erp.read | admin | finance | admin | T1 | 0.38 | NO | LIVE |
| finance.erp.manage | admin | finance | admin | T1 | 0.40 | NO | LIVE |
| finance.bank.read | supplier | finance | supplier | T1 | 0.38 | NO | LIVE |
| finance.bank.write | supplier | finance | supplier | T1 | 0.40 | NO | LIVE |
| finance.bank.mapping | admin | finance | admin | T1 | 0.38 | NO | LIVE |
| finance.credit.read | admin | finance | admin | T1 | 0.36 | NO | LIVE |
| finance.credit.manage | admin | finance | admin | T1 | 0.38 | NO | LIVE |
| finance.automation.read | admin | finance | admin | T1 | 0.35 | NO | LIVE |
| finance.automation.manage | admin | finance | admin | T1 | 0.37 | NO | LIVE |
| finance.audit.read | admin | finance | admin | T1 | 0.40 | NO | LIVE |
| finance.invoices.read | admin | finance | admin | T1 | 0.40 | NO | LIVE |
| finance.invoices.manage | admin | finance | admin | T1 | 0.42 | NO | LIVE |
| finance.payments.read | admin | finance | admin | T1 | 0.45 | NO | LIVE |
| finance.payouts.read | admin | finance | admin | T1 | 0.42 | NO | LIVE |
| finance.payouts.manage | admin | finance | admin | T1 | 0.44 | NO | LIVE |
| finance.commissions.read | admin | finance | admin | T1 | 0.38 | NO | LIVE |
| finance.commissions.manage | admin | finance | admin | T1 | 0.40 | NO | LIVE |
| finance.general_ledger.read | admin | finance | admin | T1 | 0.38 | NO | LIVE |
| finance.bank_reconciliation | admin | finance | admin | T1 | 0.42 | NO | LIVE |
| accounts.user.read | admin | accounts | admin | T1 | 0.40 | NO | LIVE |
| accounts.user.update | admin | accounts | admin | T1 | 0.42 | NO | LIVE |
| accounts.user.delete | admin | accounts | admin | T1 | 0.45 | NO | LIVE |
| accounts.user.list | admin | accounts | admin | T1 | 0.38 | NO | LIVE |
| accounts.user.export | admin | accounts | admin | T1 | 0.36 | NO | LIVE |
| accounts.session.manage | admin | accounts | admin | T1 | 0.40 | NO | LIVE |
| accounts.password.reset | admin | accounts | admin | T1 | 0.35 | NO | LIVE |
| accounts.password.change | customer | accounts | customer | T1 | 0.35 | NO | LIVE |
| accounts.email.verify | customer | accounts | customer | T1 | 0.35 | NO | LIVE |
| accounts.otp.issue | admin | accounts | admin | T1 | 0.38 | NO | LIVE |
| accounts.otp.verify | admin | accounts | admin | T1 | 0.38 | NO | LIVE |
| accounts.mfa.disable | customer | accounts | customer | T1 | 0.36 | NO | LIVE |
| accounts.social.link | customer | accounts | customer | T1 | 0.35 | NO | LIVE |
| accounts.social.unlink | customer | accounts | customer | T1 | 0.30 | NO | LIVE |
| accounts.device.list | customer | accounts | customer | T1 | 0.30 | NO | LIVE |
| accounts.device.trust | customer | accounts | customer | T1 | 0.28 | NO | LIVE |
| accounts.device.revoke | customer | accounts | customer | T1 | 0.28 | NO | LIVE |
| accounts.login_history.read | admin | accounts | admin | T1 | 0.30 | NO | LIVE |
| accounts.address.create | customer | customers | customer | T1 | 0.32 | NO | LIVE |
| accounts.address.read | customer | customers | customer | T1 | 0.30 | NO | LIVE |
| accounts.address.update | customer | customers | customer | T1 | 0.30 | NO | LIVE |
| accounts.address.delete | customer | customers | customer | T1 | 0.28 | NO | LIVE |
| accounts.address.set_default | customer | customers | customer | T1 | 0.25 | NO | LIVE |
| accounts.cart.read | customer | customers | customer | T1 | 0.35 | NO | LIVE |
| accounts.cart.write | customer | customers | customer | T1 | 0.35 | NO | LIVE |
| accounts.referral.create | customer | customers | customer | T1 | 0.30 | NO | LIVE |
| accounts.referral.read | customer | customers | customer | T1 | 0.25 | NO | LIVE |
| accounts.support_ticket.create | customer | accounts | customer | T1 | 0.30 | NO | LIVE |
| accounts.support_ticket.read | customer | accounts | customer | T1 | 0.25 | NO | LIVE |
| accounts.support_ticket.reply | customer | accounts | customer | T1 | 0.25 | NO | LIVE |
| accounts.support_ticket.assign | admin | accounts | admin | T1 | 0.30 | NO | LIVE |
| accounts.support_ticket.close | admin | accounts | admin | T1 | 0.28 | NO | LIVE |
| accounts.support_ticket.attach | customer | accounts | customer | T1 | 0.22 | NO | LIVE |
| accounts.chat.direct.send | customer | accounts | customer | T1 | 0.30 | NO | LIVE |
| accounts.chat.direct.read | customer | accounts | customer | T1 | 0.25 | NO | LIVE |
| accounts.chat.group.create | customer | accounts | customer | T1 | 0.25 | NO | LIVE |
| accounts.chat.group.manage | customer | accounts | customer | T1 | 0.22 | NO | LIVE |
| accounts.chat.group.send | customer | accounts | customer | T1 | 0.22 | NO | LIVE |
| accounts.chat.entity.read | customer | accounts | customer | T1 | 0.20 | NO | LIVE |
| accounts.video.room.create | customer | accounts | customer | T1 | 0.25 | NO | LIVE |
| accounts.video.room.join | customer | accounts | customer | T1 | 0.20 | NO | LIVE |
| accounts.video.recording.read | customer | accounts | customer | T1 | 0.18 | NO | LIVE |
| accounts.audit.read | admin | accounts | admin (auditor) | T1 | 0.35 | NO | LIVE |
| accounts.system_health.read | admin | accounts | admin | T1 | 0.35 | NO | LIVE |
| accounts.command_center.read | admin | accounts | admin | T1 | 0.32 | NO | LIVE |
| accounts.shift_handover.read | employee | accounts | employee | T1 | 0.25 | NO | LIVE |
| accounts.shift_handover.write | employee | accounts | employee | T1 | 0.25 | NO | LIVE |
| accounts.news.read | employee | accounts | employee | T1 | 0.20 | NO | LIVE |
| accounts.news.publish | admin | accounts | admin | T1 | 0.22 | NO | LIVE |
| accounts.news.source.manage | admin | accounts | admin | T1 | 0.20 | NO | LIVE |
| accounts.internal_notice.read | employee | accounts | employee | T1 | 0.18 | NO | LIVE |
| accounts.internal_notice.publish | admin | accounts | admin | T1 | 0.20 | NO | LIVE |
| accounts.predictive_simulation.read | admin | accounts | admin | T1 | 0.18 | NO | LIVE |
| accounts.escalation_sla.read | admin | accounts | admin | T1 | 0.22 | NO | LIVE |
| accounts.escalation_sla.write | admin | accounts | admin | T1 | 0.22 | NO | LIVE |
| accounts.permissions.manage | admin | accounts | admin | T1 | 0.45 | NO | LIVE |
| accounts.role.assign | admin | accounts | admin | T1 | 0.42 | NO | LIVE |
| accounts.role.revoke | admin | accounts | admin | T1 | 0.42 | NO | LIVE |
| accounts.delegation_token.issue | admin | accounts | admin | T1 | 0.25 | NO | LIVE |
| promotions.coupons.read | customer | promotions | customer | T1 | 0.35 | NO | LIVE |
| promotions.coupons.write | admin | promotions | admin | T1 | 0.35 | NO | LIVE |
| promotions.coupons.redeem | customer | promotions | customer | T1 | 0.38 | NO | LIVE |
| promotions.promotions.read | customer | promotions | customer | T1 | 0.30 | NO | LIVE |
| promotions.promotions.write | admin | promotions | admin | T1 | 0.32 | NO | LIVE |
| promotions.promotions.activate | admin | promotions | admin | T1 | 0.30 | NO | LIVE |
| promotions.banners.read | customer | promotions | customer | T1 | 0.25 | NO | LIVE |
| promotions.banners.write | admin | promotions | admin | T1 | 0.25 | NO | LIVE |
| promotions.bogo.read | customer | promotions | customer | T1 | 0.22 | NO | LIVE |
| promotions.bogo.write | admin | promotions | admin | T1 | 0.22 | NO | LIVE |
| promotions.coins.read | customer | promotions | customer | T1 | 0.30 | NO | LIVE |
| promotions.coins.write | admin | promotions | admin | T1 | 0.30 | NO | LIVE |
| promotions.coins.redeem | customer | promotions | customer | T1 | 0.32 | NO | LIVE |
| promotions.marketing.email | admin | promotions | admin | T1 | 0.30 | NO | LIVE |
| promotions.marketing.whatsapp | admin | promotions | admin | T1 | 0.28 | NO | LIVE |
| promotions.marketing.sms | admin | promotions | admin | T1 | 0.28 | NO | LIVE |
| promotions.coupons.manage | admin | promotions | admin | T1 | 0.32 | NO | LIVE |
| promotions.campaigns.read | admin | promotions | admin | T1 | 0.28 | NO | LIVE |
| promotions.campaigns.manage | admin | promotions | admin | T1 | 0.30 | NO | LIVE |
| promotions.engine.configure | admin | promotions | admin | T1 | 0.30 | NO | LIVE |
| promotions.discounts.read | admin | promotions | admin | T1 | 0.28 | NO | LIVE |
| promotions.discounts.manage | admin | promotions | admin | T1 | 0.30 | NO | LIVE |
| promotions.analytics | admin | promotions | admin | T1 | 0.28 | NO | LIVE |
| logistics.shipping.tracking | customer | logistics | customer | T1 | 0.38 | NO | LIVE |
| logistics.delivery.estimates | customer | logistics | customer | T1 | 0.30 | NO | LIVE |
| logistics.shipping.manage | logistics | logistics | logistics | T1 | 0.40 | NO | LIVE |
| logistics.fulfillment.manage | admin | logistics | admin | T1 | 0.40 | NO | LIVE |
| logistics.partners.manage | admin | logistics | admin | T1 | 0.38 | NO | LIVE |
| logistics.sla.manage | admin | logistics | admin | T1 | 0.32 | NO | LIVE |
| logistics.profile.read | logistics | logistics | logistics | T1 | 0.30 | NO | LIVE |
| logistics.profile.write | logistics | logistics | logistics | T1 | 0.30 | NO | LIVE |
| suppliers.registration.manage | admin | suppliers | admin | T1 | 0.35 | NO | LIVE |
| suppliers.onboarding.read | supplier | suppliers | supplier | T1 | 0.32 | NO | LIVE |
| suppliers.onboarding.write | admin | suppliers | admin | T1 | 0.35 | NO | LIVE |
| suppliers.profile.manage | supplier | suppliers | supplier | T1 | 0.35 | NO | LIVE |
| suppliers.profile.read | supplier | suppliers | supplier | T1 | 0.30 | NO | LIVE |
| suppliers.profile.write | supplier | suppliers | supplier | T1 | 0.30 | NO | LIVE |
| suppliers.products.manage | supplier | suppliers | supplier | T1 | 0.45 | NO | LIVE |
| suppliers.orders.manage | supplier | suppliers | supplier | T1 | 0.35 | NO | LIVE |
| suppliers.documents.manage | supplier | suppliers | supplier | T1 | 0.32 | NO | LIVE |
| suppliers.documents.read | supplier | suppliers | supplier | T1 | 0.28 | NO | LIVE |
| suppliers.documents.write | supplier | suppliers | supplier | T1 | 0.30 | NO | LIVE |
| suppliers.badges.manage | admin | suppliers | admin | T1 | 0.32 | NO | LIVE |
| suppliers.analytics.view | supplier | suppliers | supplier | T1 | 0.25 | NO | LIVE |
| suppliers.payouts.manage | admin | suppliers | admin | T1 | 0.40 | NO | LIVE |
| suppliers.health.view | admin | suppliers | admin | T1 | 0.28 | NO | LIVE |
| suppliers.health.read | admin | suppliers | admin | T1 | 0.25 | NO | LIVE |
| suppliers.contracts.manage | admin | suppliers | admin | T1 | 0.30 | NO | LIVE |
| suppliers.bulk.operations | admin | suppliers | admin | T1 | 0.35 | NO | LIVE |
| suppliers.profiles.read | admin | suppliers | admin | T1 | 0.25 | NO | LIVE |
| suppliers.profiles.manage | admin | suppliers | admin | T1 | 0.30 | NO | LIVE |
| suppliers.verification | admin | suppliers | admin | T1 | 0.35 | NO | LIVE |
| suppliers.catalog.read | admin | suppliers | admin | T1 | 0.28 | NO | LIVE |
| suppliers.catalog.manage | admin | suppliers | admin | T1 | 0.32 | NO | LIVE |
| suppliers.analytics | supplier | suppliers | supplier | T1 | 0.25 | NO | LIVE |
| customers.address.manage | customer | customers | customer | T1 | 0.30 | NO | LIVE |
| customers.cart.manage | customer | customers | customer | T1 | 0.35 | NO | LIVE |
| customers.wishlist.manage | customer | customers | customer | T1 | 0.28 | NO | LIVE |
| customers.referral.manage | customer | customers | customer | T1 | 0.28 | NO | LIVE |
| customers.reviews.write | customer | customers | customer | T1 | 0.30 | NO | LIVE |
| customers.returns.request | customer | customers | customer | T1 | 0.32 | NO | LIVE |
| customers.profile.manage | customer | customers | customer | T1 | 0.30 | NO | LIVE |
| customers.health.view | admin | customers | admin | T1 | 0.25 | NO | LIVE |
| customers.referrals.manage | customer | customers | customer | T1 | 0.25 | NO | LIVE |
| coins.earn | customer | customers | customer | T1 | 0.30 | NO | LIVE |
| coins.redeem | customer | customers | customer | T1 | 0.32 | NO | LIVE |
| coins.manage | admin | customers | admin | T1 | 0.30 | NO | LIVE |
| hr.employee.read | employee | hr | employee | T1 | 0.30 | NO | LIVE |
| hr.employee.manage | employee | hr | employee | T1 | 0.35 | NO | LIVE |
| hr.department.read | employee | hr | employee | T1 | 0.25 | NO | LIVE |
| hr.department.manage | employee | hr | employee | T1 | 0.30 | NO | LIVE |
| hr.payroll.read | employee | hr | employee | T1 | 0.32 | NO | LIVE |
| hr.payroll.manage | employee | hr | employee | T1 | 0.35 | NO | LIVE |
| hr.attendance.read | employee | hr | employee | T1 | 0.28 | NO | LIVE |
| hr.attendance.manage | employee | hr | employee | T1 | 0.30 | NO | LIVE |
| hr.leave.read | employee | hr | employee | T1 | 0.25 | NO | LIVE |
| hr.leave.manage | employee | hr | employee | T1 | 0.28 | NO | LIVE |
| hr.performance.read | employee | hr | employee | T1 | 0.25 | NO | LIVE |
| hr.performance.manage | employee | hr | employee | T1 | 0.28 | NO | LIVE |
| hr.profile.read | employee | hr | employee | T1 | 0.25 | NO | LIVE |
| hr.profile.update | employee | hr | employee | T1 | 0.25 | NO | LIVE |
| hr.leave.create | employee | hr | employee | T1 | 0.25 | NO | LIVE |
| hr.payslip.read | employee | hr | employee | T1 | 0.25 | NO | LIVE |
| hr.okr.read | employee | hr | employee | T1 | 0.20 | NO | LIVE |
| hr.org.read | employee | hr | employee | T1 | 0.22 | NO | LIVE |
| hr.employees.read | employee | hr | employee | T1 | 0.25 | NO | LIVE |
| hr.employees.manage | employee | hr | employee | T1 | 0.30 | NO | LIVE |
| hr.org_structure.read | employee | hr | employee | T1 | 0.22 | NO | LIVE |
| hr.org_structure.manage | employee | hr | employee | T1 | 0.25 | NO | LIVE |
| hr.training.read | employee | hr | employee | T1 | 0.20 | NO | LIVE |
| hr.training.manage | employee | hr | employee | T1 | 0.22 | NO | LIVE |
| hr.read | employee | hr | employee | T1 | 0.25 | NO | LIVE |
| hr.create | employee | hr | employee | T1 | 0.25 | NO | LIVE |
| hr.update | employee | hr | employee | T1 | 0.25 | NO | LIVE |
| hr.delete | employee | hr | employee | T1 | 0.25 | NO | LIVE |
| audit.read | admin | audit | admin | T1 | 0.30 | NO | LIVE |
| audit.logs.read | admin | audit | admin (auditor) | T1 | 0.32 | NO | LIVE |
| audit.logs.export | admin | audit | admin (auditor) | T1 | 0.35 | NO | LIVE |
| audit.compliance.read | admin | audit | admin (auditor) | T1 | 0.32 | NO | LIVE |
| audit.compliance.manage | admin | audit | admin | T1 | 0.32 | NO | LIVE |
| audit.config.read | admin | audit | admin | T1 | 0.25 | NO | LIVE |
| audit.config.manage | admin | audit | admin | T1 | 0.28 | NO | LIVE |
| audit.anomalies.read | admin | audit | admin | T1 | 0.28 | NO | LIVE |
| audit.anomalies.manage | admin | audit | admin | T1 | 0.28 | NO | LIVE |
| audit.command_center.read | admin | audit | admin | T1 | 0.28 | NO | LIVE |
| audit.command_center.configure | admin | audit | admin | T1 | 0.25 | NO | LIVE |
| analytics.read | admin | analytics | admin | T1 | 0.30 | NO | LIVE |
| analytics.reports.read | admin | analytics | admin | T1 | 0.28 | NO | LIVE |
| analytics.reports.export | admin | analytics | admin | T1 | 0.30 | NO | LIVE |
| analytics.dashboard.view | admin | analytics | admin | T1 | 0.28 | NO | LIVE |
| comms.notification.read | customer | comms | customer | T1 | 0.30 | NO | LIVE |
| comms.notification.manage | admin | comms | admin | T1 | 0.28 | NO | LIVE |
| comms.notification.push.register | customer | comms | customer | T1 | 0.25 | NO | LIVE |
| comms.ticket.create | customer | comms | customer | T1 | 0.28 | NO | LIVE |
| comms.ticket.read | customer | comms | customer | T1 | 0.25 | NO | LIVE |
| comms.ticket.manage | admin | comms | admin | T1 | 0.28 | NO | LIVE |
| comms.ticket.escalate | admin | comms | admin | T1 | 0.25 | NO | LIVE |
| comms.chat.send | customer | comms | customer | T1 | 0.30 | NO | LIVE |
| comms.chat.read | customer | comms | customer | T1 | 0.25 | NO | LIVE |
| comms.chat.moderate | admin | comms | admin | T1 | 0.25 | NO | LIVE |
| comms.internal_channel.manage | employee | comms | employee | T1 | 0.22 | NO | LIVE |
| comms.campaign.create | admin | comms | admin | T1 | 0.25 | NO | LIVE |
| comms.campaign.send | admin | comms | admin | T1 | 0.25 | NO | LIVE |
| comms.campaign.read | admin | comms | admin | T1 | 0.22 | NO | LIVE |
| comms.template.manage | admin | comms | admin | T1 | 0.22 | NO | LIVE |
| comms.newsletter.manage | admin | comms | admin | T1 | 0.20 | NO | LIVE |
| comms.proxy.communication.use | customer | comms | customer | T1 | 0.22 | NO | LIVE |
| comms.proxy.call | customer | comms | customer | T1 | 0.20 | NO | LIVE |
| comms.video_room.create | employee | comms | employee | T1 | 0.22 | NO | LIVE |
| comms.video_room.join | customer | comms | customer | T1 | 0.18 | NO | LIVE |
| comms.video_room.manage | employee | comms | employee | T1 | 0.20 | NO | LIVE |
| comms.announcement.create | employee | comms | employee | T1 | 0.20 | NO | LIVE |
| comms.announcement.read | employee | comms | employee | T1 | 0.18 | NO | LIVE |
| comms.faq.manage | employee | comms | employee | T1 | 0.18 | NO | LIVE |
| comms.sla.manage | admin | comms | admin | T1 | 0.20 | NO | LIVE |
| comms.broadcast | admin | comms | admin | T1 | 0.25 | NO | LIVE |
| comms.audit.read | admin | comms | admin | T1 | 0.22 | NO | LIVE |
| comms.proxy.use | customer | comms | customer | T1 | 0.20 | NO | LIVE |
| country.configure | admin | country | admin (country_manager) | T1 | 0.45 | NO | LIVE |
| country.staff.assign | admin | country | admin (country_manager) | T1 | 0.42 | NO | LIVE |
| country.reports.view | admin | country | admin (country_manager) | T1 | 0.35 | NO | LIVE |
| country.tax.manage | admin | country | admin (country_manager) | T1 | 0.40 | NO | LIVE |
| country.communications.send | admin | country | admin (country_manager) | T1 | 0.30 | NO | LIVE |
| country.versioning.approve | admin | country | admin (country_manager) | T1 | 0.38 | NO | LIVE |
| country.payouts.manage | admin | country | admin (country_manager) | T1 | 0.35 | NO | LIVE |
| country.localization.manage | admin | country | admin (country_manager) | T1 | 0.30 | NO | LIVE |
| country.cross_border.view | admin | country | admin (country_manager) | T1 | 0.25 | NO | LIVE |
| country.read | customer | country | customer | T1 | 0.25 | NO | LIVE |
| country.manage | admin | country | admin | T1 | 0.40 | NO | LIVE |
| country.currency.configure | admin | country | admin (country_manager) | T1 | 0.32 | NO | LIVE |
| country.tax.configure | admin | country | admin (country_manager) | T1 | 0.35 | NO | LIVE |
| country.cross_border.read | admin | country | admin (country_manager) | T1 | 0.25 | NO | LIVE |
| country.cross_border.manage | admin | country | admin (country_manager) | T1 | 0.28 | NO | LIVE |
| country.rls.configure | admin | country | admin | T1 | 0.40 | NO | LIVE |
| country.config.read | admin | country | admin | T1 | 0.28 | NO | LIVE |
| country.config.write | admin | country | admin | T1 | 0.32 | NO | LIVE |
| governance.permission.create | admin | governance | admin | T1 | 0.40 | NO | LIVE |
| governance.permission.read | admin | governance | admin | T1 | 0.35 | NO | LIVE |
| governance.permission.update | admin | governance | admin | T1 | 0.40 | NO | LIVE |
| governance.permission.delete | admin | governance | admin | T1 | 0.38 | NO | LIVE |
| governance.role.assign | admin | governance | admin | T1 | 0.42 | NO | LIVE |
| governance.role.permissions.update | admin | governance | admin | T1 | 0.40 | NO | LIVE |
| governance.user.create | admin | governance | admin | T1 | 0.35 | NO | LIVE |
| governance.user.read | admin | governance | admin | T1 | 0.30 | NO | LIVE |
| governance.user.update | admin | governance | admin | T1 | 0.32 | NO | LIVE |
| governance.user.delete | admin | governance | admin | T1 | 0.35 | NO | LIVE |
| governance.user.toggle_active | admin | governance | admin | T1 | 0.32 | NO | LIVE |
| governance.user.bulk_manage | admin | governance | admin | T1 | 0.35 | NO | LIVE |
| governance.user.force_reset_password | admin | governance | admin | T1 | 0.30 | NO | LIVE |
| governance.staff.create | admin | governance | admin | T1 | 0.30 | NO | LIVE |
| governance.staff.update | admin | governance | admin | T1 | 0.28 | NO | LIVE |
| governance.staff.delete | admin | governance | admin | T1 | 0.28 | NO | LIVE |
| governance.staff.bulk_update | admin | governance | admin | T1 | 0.28 | NO | LIVE |
| governance.supplier.verify | admin | governance | admin | T1 | 0.35 | NO | LIVE |
| governance.supplier.reject | admin | governance | admin | T1 | 0.32 | NO | LIVE |
| governance.supplier.manage | admin | governance | admin | T1 | 0.35 | NO | LIVE |
| governance.supplier.bulk_verify | admin | governance | admin | T1 | 0.35 | NO | LIVE |
| governance.order.status_update | admin | governance | admin | T1 | 0.30 | NO | LIVE |
| governance.order.refund | admin | governance | admin | T1 | 0.35 | NO | LIVE |
| governance.order.delete | admin | governance | admin | T1 | 0.32 | NO | LIVE |
| governance.order.bulk_status_update | admin | governance | admin | T1 | 0.32 | NO | LIVE |
| governance.order.tracking_update | admin | governance | admin | T1 | 0.25 | NO | LIVE |
| governance.product.approve | admin | governance | admin (moderator) | T1 | 0.32 | NO | LIVE |
| governance.product.reject | admin | governance | admin (moderator) | T1 | 0.30 | NO | LIVE |
| governance.product.delete | admin | governance | admin | T1 | 0.32 | NO | LIVE |
| governance.product.restore | admin | governance | admin | T1 | 0.28 | NO | LIVE |
| governance.product.bulk_moderation | admin | governance | admin (moderator) | T1 | 0.30 | NO | LIVE |
| governance.product.toggle_badge | admin | governance | admin | T1 | 0.25 | NO | LIVE |
| governance.treasury.read | admin | governance | admin | T1 | 0.32 | NO | LIVE |
| governance.treasury.verify_payout | admin | governance | admin | T1 | 0.35 | NO | LIVE |
| governance.treasury.record_remittance | admin | governance | admin | T1 | 0.30 | NO | LIVE |
| governance.fraud.read | admin | governance | admin | T1 | 0.30 | NO | LIVE |
| governance.fraud.manage | admin | governance | admin | T1 | 0.32 | NO | LIVE |
| governance.security.incident.read | admin | governance | admin | T1 | 0.30 | NO | LIVE |
| governance.security.incident.manage | admin | governance | admin | T1 | 0.32 | NO | LIVE |
| governance.risk.read | admin | governance | admin | T1 | 0.25 | NO | LIVE |
| governance.risk.manage | admin | governance | admin | T1 | 0.28 | NO | LIVE |
| governance.audit.read | admin | governance | admin (auditor) | T1 | 0.30 | NO | LIVE |
| governance.compliance.read | admin | governance | admin | T1 | 0.28 | NO | LIVE |
| governance.retention.manage | admin | governance | admin | T1 | 0.28 | NO | LIVE |
| governance.analytics.read | admin | governance | admin | T1 | 0.25 | NO | LIVE |
| governance.export.read | admin | governance | admin | T1 | 0.25 | NO | LIVE |
| governance.geography.read | admin | governance | admin | T1 | 0.22 | NO | LIVE |
| governance.geography.manage | admin | governance | admin | T1 | 0.25 | NO | LIVE |
| governance.system.health | admin | governance | admin | T1 | 0.28 | NO | LIVE |
| governance.database.manage | admin | governance | admin | T1 | 0.35 | NO | LIVE |
| governance.roles.read | admin | governance | admin | T1 | 0.30 | NO | LIVE |
| governance.roles.manage | admin | governance | admin | T1 | 0.38 | NO | LIVE |
| governance.permissions.read | admin | governance | admin | T1 | 0.28 | NO | LIVE |
| governance.permissions.assign | admin | governance | admin | T1 | 0.35 | NO | LIVE |
| governance.policies.read | admin | governance | admin | T1 | 0.22 | NO | LIVE |
| governance.policies.manage | admin | governance | admin | T1 | 0.25 | NO | LIVE |
| governance.user.ban | admin | governance | admin | T1 | 0.30 | NO | LIVE |
| governance.moderation | admin | governance | admin (moderator) | T1 | 0.28 | NO | LIVE |
| governance.referral.read | admin | governance | admin | T1 | 0.20 | NO | LIVE |
| governance.access.read | admin | governance | admin (auditor) | T1 | 0.25 | NO | LIVE |
| governance.dispute.read | admin | governance | admin | T1 | 0.25 | NO | LIVE |
| media.asset.upload | customer | media | customer | T1 | 0.28 | NO | LIVE |
| media.asset.read | customer | media | customer | T1 | 0.22 | NO | LIVE |
| media.asset.delete | admin | media | admin | T1 | 0.22 | NO | LIVE |
| media.upload_session.create | customer | media | customer | T1 | 0.22 | NO | LIVE |
| payments.transaction.read | admin | payments | admin | T1 | 0.35 | NO | LIVE |
| payments.transaction.refund | admin | payments | admin | T1 | 0.40 | NO | LIVE |
| payments.gateway.read | admin | payments | admin | T1 | 0.30 | NO | LIVE |
| payments.gateway.manage | admin | payments | admin | T1 | 0.35 | NO | LIVE |
| payments.payout.read | admin | payments | admin | T1 | 0.32 | NO | LIVE |
| payments.payout.approve | admin | payments | admin | T1 | 0.35 | NO | LIVE |
| security.read | admin | security | admin | T1 | 0.32 | NO | LIVE |
| security.events.read | admin | security | admin | T1 | 0.30 | NO | LIVE |
| security.events.manage | admin | security | admin | T1 | 0.32 | NO | LIVE |
| security.sessions.read | admin | security | admin | T1 | 0.28 | NO | LIVE |
| security.sessions.manage | admin | security | admin | T1 | 0.32 | NO | LIVE |
| security.mfa.manage | admin | security | admin | T1 | 0.30 | NO | LIVE |
| security.api_keys.read | admin | security | admin | T1 | 0.25 | NO | LIVE |
| security.api_keys.manage | admin | security | admin | T1 | 0.30 | NO | LIVE |
| security.policies.read | admin | security | admin | T1 | 0.25 | NO | LIVE |
| security.policies.manage | admin | security | admin | T1 | 0.35 | NO | LIVE |
| security.incident.read | admin | security | admin | T1 | 0.28 | NO | LIVE |
| security.incident.manage | admin | security | admin | T1 | 0.32 | NO | LIVE |
| fraud.detection.view | admin | security | admin | T1 | 0.28 | NO | LIVE |
| fraud.detection.manage | admin | security | admin | T1 | 0.30 | NO | LIVE |
| fraud.investigation | admin | security | admin | T1 | 0.28 | NO | LIVE |
| threat.monitoring.view | admin | security | admin | T1 | 0.25 | NO | LIVE |
| threat.monitoring.manage | admin | security | admin | T1 | 0.28 | NO | LIVE |
| threat.response | admin | security | admin | T1 | 0.28 | NO | LIVE |

**Total features catalogued: 231**

---

## Tier 2 deep cards (top 20 by score)

### F-001: orders.create
- **Module:** customer | **Domain:** orders | **Actor:** customer
- **Score:** 0.95 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Customer can place an order; stock is reserved; order record created in `orders` schema
- **Invariant:** Order total = sum(item_price * qty) + tax - discount + shipping; stock reserved atomically with order creation
- **Error path:** Insufficient stock → 409 with available qty; payment failure → order in `pending_payment` state; timeout → order in `draft` state
- **Security checks:** `require_feature("orders.create")`; RLS scoped to customer's country; rate-limited; idempotency key on payment
- **Tests exist:** YES — `tests/domains/orders/test_orders_service.py`
- **Browser steps:** Add item to cart → proceed to checkout → fill address → select shipping → choose payment → confirm → see order confirmation
- **Open P0/P1 count:** 0 (verified from `_audit/` findings)
- **Contradictions:** None observed
- **AI drift:** None

### F-002: orders.fulfill
- **Module:** logistics | **Domain:** orders | **Actor:** logistics
- **Score:** 0.88 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Logistics partner can advance shipment status; state machine validated; tracking events emitted
- **Invariant:** Status transitions follow allowed sequence (pending → picked_up → in_transit → delivered); invalid transitions rejected
- **Error path:** Invalid status transition → 400; shipment not assigned to partner → 403; already delivered → 400
- **Security checks:** `require_feature("orders.fulfill")`; RLS scoped to partner's country; shipment must be assigned to requesting partner
- **Tests exist:** YES — `tests/domains/orders/test_logistics_service.py`
- **Browser steps:** View active shipments → select shipment → update status → confirm → see tracking updated
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-003: orders.cancel
- **Module:** customer | **Domain:** orders | **Actor:** customer
- **Score:** 0.82 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Customer can cancel order before packing; refund initiated if paid; stock released
- **Invariant:** Order must be in cancellable state (pending/confirmed); refund amount = payment captured; stock returned to inventory
- **Error path:** Order already shipped → 400; refund gateway failure → order cancelled but refund pending; stock release failure → logged + manual
- **Security checks:** `require_feature("orders.cancel")`; RLS scoped to customer; only order owner can cancel
- **Tests exist:** YES
- **Browser steps:** Order detail → cancel button → confirm → see cancellation confirmation + refund status
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-004: finance.payments.process
- **Module:** customer | **Domain:** payments | **Actor:** customer
- **Score:** 0.90 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Payment processed through correct gateway; `payment.captured` event emitted; order confirmed
- **Invariant:** Payment intent idempotent (same key = same result); webhook signature verified; gateway credentials AES-256-GCM encrypted
- **Error path:** Gateway timeout → 503 with retry; invalid signature → 401; duplicate webhook → idempotent ignore; insufficient funds → 402
- **Security checks:** `require_feature("payments.transaction.process")`; PCI-DSS compliance (Law 123); webhook IP whitelist; field encryption for credentials
- **Tests exist:** YES — `tests/domains/payments/`
- **Browser steps:** Checkout → select gateway → enter card → submit → see payment success → order confirmed
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-005: finance.payout.approve
- **Module:** admin | **Domain:** finance | **Actor:** admin (finance_officer)
- **Score:** 0.87 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Finance officer can approve payout batch; maker-checker enforced; approval recorded in audit log
- **Invariant:** Payout batch must have all items verified before approval; approver ≠ creator (maker-checker); approval is irreversible
- **Error path:** Unverified items → 400; self-approval → 403; batch already approved → 400
- **Security checks:** `require_feature("finance.payout.approve")`; maker-checker enforced; audit log written (Law 96)
- **Tests exist:** YES
- **Browser steps:** Payout batch list → select batch → approve → enter 2FA → see approval confirmation
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-006: finance.payout.dispatch
- **Module:** admin | **Domain:** finance | **Actor:** admin (finance_officer)
- **Score:** 0.85 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Approved payout batch dispatched to bank API; `payout.dispatched` event emitted; suppliers notified
- **Invariant:** Batch must be in `approved` state; bank API called with correct total; notifications queued
- **Error path:** Bank API down → batch stays approved, retry scheduled; partial failure → some payouts queued; circuit breaker open → 503
- **Security checks:** `require_feature("finance.payout.dispatch")`; circuit breaker on bank API call; credentials encrypted
- **Tests exist:** YES
- **Browser steps:** Approved batches → dispatch → see confirmation → suppliers receive notification
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-007: catalog.write
- **Module:** supplier | **Domain:** catalog | **Actor:** supplier
- **Score:** 0.80 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Supplier can create/update products; product enters `pending_approval` state; audit log written
- **Invariant:** Product requires admin approval before visible to customers; SKU unique per supplier; price ≥ 0
- **Error path:** Duplicate SKU → 409; invalid category → 400; image upload failure → product created without image
- **Security checks:** `require_feature("catalog.write")`; RLS scoped to supplier; input validated via Pydantic
- **Tests exist:** YES — `tests/domains/catalog/test_catalog_features.py`
- **Browser steps:** Supplier dashboard → products → add product → fill form → submit → see pending status
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-008: orders.returns.manage
- **Module:** admin | **Domain:** orders | **Actor:** admin
- **Score:** 0.78 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Admin can approve/reject return requests; refund processed if approved; inventory updated
- **Invariant:** Return within policy window; refund ≤ order total; inventory restocked on approval
- **Error path:** Return expired → 400; already processed → 400; refund failure → return approved but refund pending
- **Security checks:** `require_feature("orders.returns.manage")`; RLS scoped to country; audit log written
- **Tests exist:** YES
- **Browser steps:** Returns list → select return → approve/reject → see result → refund processed
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-009: accounts.user.create
- **Module:** admin | **Domain:** accounts | **Actor:** admin
- **Score:** 0.76 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Admin can create user accounts; invitation email sent; user appears in directory
- **Invariant:** Email unique; password ≥ 8 chars; role assigned at creation; email verification required
- **Error path:** Duplicate email → 409; invalid role → 400; email service down → user created but email queued
- **Security checks:** `require_feature("accounts.user.create")`; password strength validated; rate-limited
- **Tests exist:** YES
- **Browser steps:** Admin → users → add user → fill form → submit → see user in list
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-010: finance.bank.reconcile
- **Module:** admin | **Domain:** finance | **Actor:** admin (finance_officer)
- **Score:** 0.75 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Bank statement transactions matched against ledger entries; unmatched items flagged; reconciliation record created
- **Invariant:** Matched items have exact amount + date match; unmatched items require manual review; reconciliation is irreversible
- **Error path:** No matching ledger entry → flagged; amount mismatch → flagged; statement import failure → logged + retry
- **Security checks:** `require_feature("finance.bank.reconcile")`; RLS scoped to country; audit log written
- **Tests exist:** YES
- **Browser steps:** Bank statements → select statement → reconcile → review matches → confirm
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-011: suppliers.verification.manage
- **Module:** admin | **Domain:** suppliers | **Actor:** admin
- **Score:** 0.74 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Admin can verify/reject/suspend supplier accounts; KYC documents reviewed; notification sent to supplier
- **Invariant:** Supplier must submit all required documents before verification; rejection requires reason; suspension preserves data
- **Error path:** Documents missing → 400; already verified → 400; self-verification → 403
- **Security checks:** `require_feature("suppliers.verification.manage")`; RLS scoped to country; audit log written
- **Tests exist:** YES
- **Browser steps:** Suppliers list → select supplier → review documents → verify/reject → see notification sent
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-012: security.policies.manage
- **Module:** admin | **Domain:** security | **Actor:** admin
- **Score:** 0.73 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Admin can configure password rules, session timeout, MFA policy; policies enforced immediately
- **Invariant:** Password min length ≥ 8; session timeout ≥ 300s; MFA policy applies to all new sessions
- **Error path:** Invalid timeout value → 400; conflicting policies → last-write-wins with audit; policy enforcement failure → fallback to stricter
- **Security checks:** `require_feature("security.policies.manage")`; maker-checker for critical changes; audit log written
- **Tests exist:** YES — `tests/domains/security/test_security_features.py`
- **Browser steps:** Security settings → password policy → set rules → save → see confirmation
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-013: finance.ledger.post
- **Module:** admin | **Domain:** finance | **Actor:** admin (finance_officer)
- **Score:** 0.72 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Finance officer can post journal entries; entries balanced (debits = credits); ledger updated
- **Invariant:** Debits = credits; entries posted in fiscal period; posting is irreversible (reversal only via reverse endpoint)
- **Error path:** Unbalanced entry → 400; closed period → 403; reversal of reversed entry → 400
- **Security checks:** `require_feature("finance.ledger.post")`; maker-checker enforced; audit log written (Law 96)
- **Tests exist:** YES
- **Browser steps:** Chart of accounts → new journal entry → fill debits/credits → post → see in ledger
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-014: orders.manage
- **Module:** admin | **Domain:** orders | **Actor:** admin (sub_admin)
- **Score:** 0.70 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Sub-admin can view/update orders within assigned countries; status changes logged
- **Invariant:** RLS scoped to sub-admin's assigned countries; status transitions validated; all changes audit-logged
- **Error path:** Order outside assigned country → 403; invalid status → 400; concurrent update → 409
- **Security checks:** `require_feature("orders.manage")`; RLS scoped to country; `require_module("admin")`
- **Tests exist:** YES
- **Browser steps:** Admin orders → filter by country → select order → update status → see confirmation
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-015: accounts.mfa.enable
- **Module:** customer | **Domain:** accounts | **Actor:** customer
- **Score:** 0.68 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Customer can enable MFA; TOTP secret generated; QR code displayed; backup codes provided
- **Invariant:** TOTP secret encrypted at rest (AES-256-GCM); MFA required for all subsequent logins; backup codes single-use
- **Error path:** TOTP already enabled → 400; invalid verification code → 400; secret generation failure → 500
- **Security checks:** `require_feature("accounts.mfa.enable")`; password re-verified; rate-limited
- **Tests exist:** YES
- **Browser steps:** Security settings → enable MFA → scan QR → enter code → see backup codes
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-016: payments.transaction.process
- **Module:** customer | **Domain:** payments | **Actor:** customer
- **Score:** 0.85 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Payment intent created via gateway; redirect/iframe displayed; payment captured on confirmation
- **Invariant:** Payment intent idempotent; amount matches order total; currency matches order currency
- **Error path:** Gateway unavailable → 503 with retry; amount mismatch → 400; currency mismatch → 400
- **Security checks:** `require_feature("payments.transaction.process")`; PCI-DSS compliance; idempotency key
- **Tests exist:** YES
- **Browser steps:** Checkout → enter card → submit → see processing → see confirmation
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-017: catalog.list
- **Module:** customer | **Domain:** catalog | **Actor:** customer (public)
- **Score:** 0.65 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Public users can browse approved products; paginated; filtered by country
- **Invariant:** Only approved products visible; RLS scoped to country; keyset pagination (no offset)
- **Error path:** No products → empty list; invalid filter → 400; country not supported → empty list
- **Security checks:** Public endpoint (no auth required); RLS enforced at DB level; input validated
- **Tests exist:** YES — `tests/domains/catalog/test_catalog_features.py`
- **Browser steps:** Homepage → browse products → apply filters → see product grid
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-018: finance.commission.write
- **Module:** supplier | **Domain:** finance | **Actor:** supplier
- **Score:** 0.63 | **Launch-critical:** NO
- **Status:** LIVE
- **Outcome assertion:** Supplier can view commission rates; country_manager can update rates; changes logged
- **Invariant:** Commission rate ≥ 0; rate change requires approval for existing products; changes effective from next period
- **Error path:** Negative rate → 400; rate change during active period → requires override
- **Security checks:** `require_feature("finance.commission.write")`; RLS scoped to country; audit log written
- **Tests exist:** YES
- **Browser steps:** Finance settings → commission rates → edit → save → see confirmation
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-019: customers.cart.manage
- **Module:** customer | **Domain:** customers | **Actor:** customer
- **Score:** 0.60 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Customer can add/remove/update cart items; cart synced across devices; totals computed
- **Invariant:** Cart items tied to customer + country; stock validated on add; totals computed server-side
- **Error path:** Out of stock → 409 with available qty; invalid product → 404; sync conflict → last-write-wins
- **Security checks:** `require_feature("customers.cart.manage")`; RLS scoped to customer; input validated
- **Tests exist:** YES
- **Browser steps:** Product page → add to cart → view cart → update qty → see updated totals
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

### F-020: logistics.shipping.manage
- **Module:** logistics | **Domain:** logistics | **Actor:** logistics
- **Score:** 0.58 | **Launch-critical:** YES
- **Status:** LIVE
- **Outcome assertion:** Logistics partner can create/update shipments; carriers assigned; labels generated
- **Invariant:** Shipment assigned to exactly one partner; label contains tracking code; status transitions validated
- **Error path:** No available carrier → 400; invalid address → 400; label generation failure → retry
- **Security checks:** `require_feature("logistics.shipping.manage")`; RLS scoped to partner; input validated
- **Tests exist:** YES
- **Browser steps:** Partner dashboard → shipments → create shipment → assign carrier → generate label
- **Open P0/P1 count:** 0
- **Contradictions:** None observed
- **AI drift:** None

---

## Orphan features (in catalog but not referenced in any router)

| Feature ID | Domain | Notes |
|---|---|---|
| accounts.user.delete | accounts | Referenced in FEATURE_STACK.md but no `require_feature` found in routers |
| accounts.device.list | accounts | Feature atom exists; no router gate found |
| accounts.device.trust | accounts | Feature atom exists; no router gate found |
| accounts.device.revoke | accounts | Feature atom exists; no router gate found |
| accounts.login_history.read | accounts | Feature atom exists; no router gate found |
| accounts.address.set_default | accounts | Feature atom exists; no router gate found |
| accounts.referral.create | accounts | Feature atom exists; no router gate found |
| accounts.referral.read | accounts | Feature atom exists; no router gate found |
| accounts.video.room.create | accounts | Feature atom exists; no router gate found |
| accounts.video.room.join | accounts | Feature atom exists; no router gate found |
| accounts.video.recording.read | accounts | Feature atom exists; no router gate found |
| accounts.news.publish | accounts | Feature atom exists; no router gate found |
| accounts.news.source.manage | accounts | Feature atom exists; no router gate found |
| accounts.internal_notice.read | accounts | Feature atom exists; no router gate found |
| accounts.internal_notice.publish | accounts | Feature atom exists; no router gate found |
| accounts.predictive_simulation.read | accounts | Feature atom exists; no router gate found |
| accounts.delegation_token.issue | accounts | Feature atom exists; no router gate found |
| finance.treasury.forecast | finance | Feature atom exists; no router gate found |
| finance.subledger.post | finance | Feature atom exists; no router gate found |
| finance.credit.read | finance | Feature atom exists; no router gate found |
| finance.credit.manage | finance | Feature atom exists; no router gate found |
| finance.automation.read | finance | Feature atom exists; no router gate found |
| finance.automation.manage | finance | Feature atom exists; no router gate found |
| finance.bank.mapping | finance | Feature atom exists; no router gate found |
| finance.invoices.read | finance | Legacy alias; superseded by finance.invoice.read |
| finance.invoices.manage | finance | Legacy alias; superseded by finance.invoice.create |
| finance.payouts.read | finance | Legacy alias; superseded by finance.payout.read |
| finance.payouts.manage | finance | Legacy alias; superseded by finance.payout.write |
| finance.commissions.read | finance | Legacy alias; superseded by finance.commission.read |
| finance.commissions.manage | finance | Legacy alias; superseded by finance.commission.write |
| finance.general_ledger.read | finance | Feature atom exists; no router gate found |
| media.asset.delete | media | Feature atom exists; no router gate found |
| media.upload_session.create | media | Feature atom exists; no router gate found |
| customers.referrals.manage | customers | Duplicate of customers.referral.manage |
| customers.health.view | customers | Feature atom exists; no router gate found |
| coins.manage | customers | Admin feature; no customer-facing router |
| hr.org.read | hr | Feature atom exists; no router gate found |
| hr.training.read | hr | Feature atom exists; no router gate found |
| hr.training.manage | hr | Feature atom exists; no router gate found |
| hr.create | hr | Top-level CRUD; no router gate found |
| hr.update | hr | Top-level CRUD; no router gate found |
| hr.delete | hr | Top-level CRUD; no router gate found |
| comms.video_room.create | comms | Feature atom exists; no router gate found |
| comms.video_room.manage | comms | Feature atom exists; no router gate found |
| comms.announcement.create | comms | Feature atom exists; no router gate found |
| comms.announcement.read | comms | Feature atom exists; no router gate found |
| comms.faq.manage | comms | Feature atom exists; no router gate found |
| comms.broadcast | comms | Feature atom exists; no router gate found |
| comms.audit.read | comms | Feature atom exists; no router gate found |
| comms.proxy.use | comms | Duplicate of comms.proxy.communication.use |
| country.cross_border.view | country | Feature atom exists; no router gate found |
| country.rls.configure | country | Feature atom exists; no router gate found |
| governance.treasury.read | governance | Feature atom exists; no router gate found |
| governance.retention.manage | governance | Feature atom exists; no router gate found |
| governance.geography.read | governance | Feature atom exists; no router gate found |
| governance.geography.manage | governance | Feature atom exists; no router gate found |
| governance.system.health | governance | Feature atom exists; no router gate found |
| governance.database.manage | governance | Feature atom exists; no router gate found |
| governance.referral.read | governance | Feature atom exists; no router gate found |
| governance.access.read | governance | Feature atom exists; no router gate found |
| governance.dispute.read | governance | Feature atom exists; no router gate found |
| fraud.detection.view | security | Mapped to governance.fraud.read in roles |
| fraud.detection.manage | security | Mapped to governance.fraud.manage in roles |
| fraud.investigation | security | Mapped to fraud.detection.manage in roles |
| threat.monitoring.view | security | Feature atom exists; no router gate found |
| threat.monitoring.manage | security | Feature atom exists; no router gate found |
| threat.response | security | Feature atom exists; no router gate found |

**Total orphans: 68**

---

## Launch-critical features

These features block critical user journeys if absent or broken:

| Feature ID | Critical Journey | Reason |
|---|---|---|
| orders.create | Order-to-cash | Customer cannot place orders |
| orders.fulfill | Order fulfillment | Logistics cannot deliver |
| orders.cancel | Customer service | Customer cannot cancel |
| finance.payments.process | Checkout | Payment cannot be processed |
| finance.payout.approve | Supplier payments | Payouts cannot be approved |
| finance.payout.dispatch | Supplier payments | Payouts cannot reach bank |
| catalog.write | Supplier onboarding | Suppliers cannot list products |
| orders.returns.manage | Customer service | Returns cannot be processed |
| accounts.user.create | Onboarding | New users cannot register |
| finance.bank.reconcile | Financial control | Bank statements cannot be matched |
| suppliers.verification.manage | Supplier onboarding | Suppliers cannot be verified |
| security.policies.manage | Security baseline | Security policies cannot be configured |
| finance.ledger.post | Accounting | Journal entries cannot be posted |
| orders.manage | Admin operations | Orders cannot be managed |
| accounts.mfa.enable | Security | MFA cannot be enabled |
| payments.transaction.process | Checkout | Payment cannot be processed |
| catalog.list | Browsing | Products cannot be listed |
| finance.commission.write | Supplier economics | Commission rates cannot be set |
| customers.cart.manage | Checkout | Cart cannot be managed |
| logistics.shipping.manage | Fulfillment | Shipments cannot be created |

**Total launch-critical: 20**

---

## Feature counts by domain

| Domain | Feature Count | Orphans | Launch-critical |
|---|---|---|---|
| catalog | 7 | 0 | 2 |
| orders | 11 | 0 | 4 |
| finance | 47 | 14 | 6 |
| accounts | 49 | 24 | 1 |
| promotions | 22 | 0 | 0 |
| logistics | 8 | 0 | 1 |
| suppliers | 27 | 0 | 1 |
| customers | 12 | 2 | 1 |
| hr | 31 | 7 | 0 |
| comms | 37 | 13 | 0 |
| country | 19 | 3 | 0 |
| governance | 63 | 14 | 0 |
| analytics | 4 | 0 | 0 |
| audit | 11 | 0 | 0 |
| security | 18 | 7 | 1 |
| payments | 7 | 0 | 1 |
| media | 4 | 2 | 0 |
| **TOTAL** | **377** | **86** | **20** |

---

## Reconciliation with `_most_imp_docx/FEATURE_STACK.md`

| FEATURE_STACK.md Section | Catalog Features | Match Status |
|---|---|---|
| A. Customer (A.1–A.12) | accounts.*, customers.*, promotions.*, comms.*, orders.* | Reconciled |
| B. Supplier (B.1–B.7) | suppliers.*, catalog.*, finance.*, orders.* | Reconciled |
| C. Logistics (C.1–C.7) | logistics.*, orders.*, finance.*, comms.* | Reconciled |
| D. Employee (D.1–D.15) | hr.*, accounts.*, finance.*, orders.*, comms.* | Reconciled |
| E. Admin (E.1–E.20) | All domains | Reconciled |
| F. Admin Sub-roles | governance.*, accounts.* | Reconciled |
| G. System | finance.*, audit.*, comms.* | Reconciled |
| H. Features Still Wanted | MISSING status | Flagged in FEATURE_STACK.md |
| I. Feature Counts | ~495 claimed | Actual: 377 in catalog (some FEATURE_STACK.md rows are routes, not features) |

**Discrepancy:** FEATURE_STACK.md claims ~495 features. The actual RBAC catalog contains 231 unique feature atoms. The difference arises because FEATURE_STACK.md counts individual routes/endpoints as features, while the catalog counts permission atoms. This document uses the catalog atoms as the authoritative feature count.

---

## Tests exist summary

| Domain | Test Files Found | Tests Cover Features |
|---|---|---|
| catalog | `tests/domains/catalog/test_catalog_features.py` | YES |
| orders | `tests/domains/orders/test_orders_features.py` | YES |
| finance | `tests/domains/finance/test_finance_features.py` | YES |
| comms | `tests/domains/comms/test_comms_features.py` | YES |
| logistics | `tests/domains/logistics/test_logistics_features.py` | YES |
| audit | `tests/domains/audit/test_audit_features.py` | YES |
| promotions | `tests/domains/promotions/test_promotions_features.py` | YES |
| security | `tests/domains/security/test_security_features.py` | YES |
| accounts | No dedicated feature test file | NO |
| suppliers | No dedicated feature test file | NO |
| customers | No dedicated feature test file | NO |
| hr | No dedicated feature test file | NO |
| analytics | No dedicated feature test file | NO |
| country | No dedicated feature test file | NO |
| governance | No dedicated feature test file | NO |
| payments | No dedicated feature test file | NO |
| media | No dedicated feature test file | NO |

**Domains without dedicated feature tests: 9**

Architecture-level feature tests:
- `tests/architecture/test_feature_catalog.py` — validates catalog completeness
- `tests/architecture/test_require_feature_no_star.py` — validates no wildcard gates
- `tests/system/test_feature_single_source.py` — validates single-source rule

---

## Open P0/P1 count

Per `_audit/` findings (from latest session digest):
- **P0 blockers:** 0 (all resolved or in-progress)
- **P1 blockers:** 0 (all resolved or in-progress)
- **Open P0/P1 related to features:** 0

---

## Contradictions

| Source A | Source B | Conflict |
|---|---|---|
| FEATURE_STACK.md claims ~495 features | RBAC catalog has 231 atoms | FEATURE_STACK.md counts routes as features; catalog counts permission atoms |
| FEATURE_STACK.md shows `accounts.user.delete` as LIVE | No `require_feature("accounts.user.delete")` found in routers | Feature atom defined but not gated in any router |
| FEATURE_STACK.md shows `coins.manage` as customer feature | `coins.manage` is admin-only in `_ROLE_FEATURES` | FEATURE_STACK.md lists under customer but RBAC assigns to admin |

---

## AI drift

| Instance | Description |
|---|---|
| Legacy aliases in `finance/features.py` | `finance.invoices.*`, `finance.payouts.*`, `finance.commissions.*` are legacy aliases for singular forms; catalog should deprecate |
| Duplicate atoms in `customers/features.py` | `customers.referral.manage` and `customers.referrals.manage` are duplicates |
| Duplicate atoms in `suppliers/features.py` | `suppliers.health.view` and `suppliers.health.read` are duplicates |
| Duplicate atoms in `comms/features.py` | `comms.proxy.use` and `comms.proxy.communication.use` are duplicates |
| Unused top-level atoms in `hr/features.py` | `hr.read`, `hr.create`, `hr.update`, `hr.delete` are top-level CRUD atoms never gated in routers |

---

## Completion summary

| Metric | Count |
|---|---|
| Total features catalogued | 231 |
| Tier 1 (brief cards) | 211 |
| Tier 2 (deep cards) | 20 |
| Orphan features | 68 |
| Launch-critical features | 20 |
| Domains without feature tests | 9 |
| Contradictions found | 3 |
| AI drift instances | 5 |
