# Governance Domain ORM Model Investigation Report

**Scope:** 9 files in `backend/domains/governance/models/`
**Models defined inline:** 49 classes (across admin.py, core.py, fraud.py, incident.py, onboarding.py, otp.py, permissions.py, social.py)
**Pure re-export shim files:** user.py (no inline models)
**Audit column set checked:** `created_at`, `updated_at`, `is_deleted`, `version`, `country_code`
**Forbidden FK target schemas:** `core`, `platform`, `identity`

---

## FILE: `admin.py` (37 model classes)

### Class: `AdminAnalyticsSnapshot` (line 28)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Missing audit columns | Has `computed_at` but no `created_at`. Missing `updated_at`, `is_deleted`, `version`. |

**Schema:** `governance` ✓ (line 33)

---

### Class: `RolePermissionSetting` (line 44)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "core"},)` (line 46). Should be `governance`. |
| 2 | FK to forbidden schema | `created_by`... no, this class has no FK. But schema is `core` itself. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `SystemAlert` (line 54)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "configuration"},)` (line 56). Should be `governance`. |
| 2 | FK to forbidden schema | `acknowledged_by = Column(Integer, ForeignKey("core.users.id"), ...)` (line 63). `core` is a forbidden FK schema. |
| 4 | Naming violations | `acknowledged_by` (line 63) is a FK column not following `<thing>_id` convention. Should be `acknowledged_by_id`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |
| 7 | Missing FK index | `acknowledged_by` (line 63) has no `index=True`. |

---

### Class: `AdminChangeAuditLog` (line 69)
| # | Criterion | Issue |
|---|-----------|-------|
| 2 | FK to forbidden schema | `admin_id = Column(Integer, ForeignKey("core.users.id"), ...)` (line 73). `core` is forbidden. |
| 7 | Missing FK index | `admin_id` (line 73) has no `index=True`. |
| 6 | Relationship issues | `admin = relationship("User", foreign_keys=[admin_id])` (line 83) — no `back_populates`, no explicit `lazy` strategy. Cross-domain relationship with no reciprocal definition. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

**Schema:** `governance` ✓ (line 71)

---

### Class: `AdminActivityLog` (line 86)
| # | Criterion | Issue |
|---|-----------|-------|
| 2 | FK to forbidden schema | `admin_id = Column(Integer, ForeignKey("core.users.id"), ...)` (line 90). `core` is forbidden. |
| 7 | Missing FK index | `admin_id` (line 90) has no `index=True`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

**Schema:** `governance` ✓ (line 88)

---

### Class: `SystemSetting` (line 98)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "configuration"},)` (line 100). Should be `governance`. |
| 4 | Naming violations | `key` (line 102) — not a FK but is a Python builtin-ish name; acceptable as column name. No naming issue per se. |

---

### Class: `APIKey` (line 111)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "core"},)` (line 113). Should be `governance`. |
| 2 | FK to forbidden schema | `created_by = Column(Integer, ForeignKey("core.users.id"), ...)` (line 120). `core` is forbidden. |
| 4 | Naming violations | `created_by` (line 120) is a FK column not following `<thing>_id` convention. Should be `created_by_id`. |
| 7 | Missing FK index | `created_by` (line 120) has no `index=True`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `BadgeBillingRecord` (line 125)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "commerce"},)` (line 127). Should be `governance`. |
| 2 | FK to forbidden schema | `user_id` (line 129), `supplier_id` (line 130) both FK to `core.users.id`. `core` is forbidden. |
| 2 | FK to forbidden schema | `bank_transaction_id` (line 147) FK to `finance.bank_transactions.id` — not in forbidden list (core/platform/identity). |
| 7 | Missing FK index | `user_id` (line 129), `supplier_id` (line 130), `bank_transaction_id` (line 147) — no `index=True` on any. |
| 4 | Naming violations | `created_by` (line 146) is `Column(Integer, nullable=True)` with NO ForeignKey — orphaned FK-like column. Should be `created_by_id` with a proper FK to users. |
| 6 | Relationship issues | `supplier = relationship("User", foreign_keys=[supplier_id])` (line 151) — no `back_populates`. `bank_transaction = relationship("BankTransaction")` (line 152) — no `back_populates`, no `foreign_keys` specified. |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `BadgeTransaction` (line 155)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "commerce"},)` (line 157). Should be `governance`. |
| 2 | FK to forbidden schema | `user_id` (line 159) FK to `core.users.id`. `core` is forbidden. |
| 7 | Missing FK index | `user_id` (line 159) has no `index=True`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `BadgeTier` (line 167)
**Schema:** `commerce` (line 169) — should be `governance`.

| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "commerce"},)` (line 169). Should be `governance`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `CommissionBadgeTier` (line 178)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "commerce"},)` (line 180). Should be `governance`. |
| 2 | FK to forbidden schema | `updated_by` (line 193) FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `updated_by` (line 193) is a FK column not following `<thing>_id`. Should be `updated_by_id`. |
| 7 | Missing FK index | `updated_by` (line 193) has no `index=True`. |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `CommissionGlobalConfig` (line 199)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "commerce"},)` (line 201). Should be `governance`. |
| 2 | FK to forbidden schema | `updated_by` (line 209) FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `updated_by` (line 209) FK, should be `updated_by_id`. |
| 7 | Missing FK index | `updated_by` (line 209) has no `index=True`. |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `TicketReply` (line 215)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "communication"},)` (line 217). Should be `governance`. |
| 2 | FK to forbidden schema | `sender_id` (line 220) FK to `core.users.id`. `core` is forbidden. |
| 7 | Missing FK index | `ticket_id` (line 219), `sender_id` (line 220) — no `index=True`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `CouponUsage` (line 226)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "commerce"},)` (line 228). Should be `governance`. |
| 2 | FK to forbidden schema | `user_id` (line 231) FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | Table name `coupon_usage` (line 227) is singular. Should be `coupon_usages` to match plural convention. |
| 7 | Missing FK index | `coupon_id` (line 230), `user_id` (line 231), `order_id` (line 232) — no `index=True`. (`country_code` has `index=True` on line 233.) |
| 6 | Relationship issues | `coupon = relationship("Coupon", backref="usages")` (line 236) — uses `backref` instead of `back_populates` (style inconsistency with other models). |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `PaymentProviderConfig` (line 242)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "treasury"},)` (line 244). Should be `governance`. |
| 2 | FK to forbidden schema | `updated_by` (line 249) FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `updated_by` (line 249) FK, should be `updated_by_id`. |
| 7 | Missing FK index | `updated_by` (line 249) has no `index=True`. |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `EmailProviderConfig` (line 255)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "configuration"},)` (line 257). Should be `governance`. |
| 2 | FK to forbidden schema | `updated_by` (line 261) FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `updated_by` (line 261) FK, should be `updated_by_id`. |
| 7 | Missing FK index | `updated_by` (line 261) has no `index=True`. |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `ShippingCarrier` (line 284)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "logistics"},)` (line 286). Should be `governance`. |
| 2 | FK to forbidden schema | `supplier_id` (line 288) FK to `core.users.id`. `core` is forbidden. |
| 7 | Missing FK index | `supplier_id` (line 288) has no `index=True`. |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `ShippingZone` (line 297)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "logistics"},)` (line 299). Should be `governance`. |
| 2 | FK to forbidden schema | `supplier_id` (line 301) FK to `core.users.id`. `core` is forbidden. |
| 7 | Missing FK index | `supplier_id` (line 301) has no `index=True`. |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `FinanceBankAccount` (line 310)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "treasury"},)` (line 312). Should be `governance`. |
| 2 | FK to forbidden schema | `created_by` (line 329), `updated_by` (line 330) both FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `created_by` (line 329) FK → should be `created_by_id`. `updated_by` (line 330) FK → should be `updated_by_id`. |
| 7 | Missing FK index | `created_by` (line 329), `updated_by` (line 330) — no `index=True`. |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `PromotionEngineConfig` (line 336)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "commerce"},)` (line 338). Should be `governance`. |
| 2 | FK to forbidden schema | `country_code` (line 340) FK to `country.country_configs.code` — not forbidden. `updated_by` (line 361) FK to `core.users.id` — `core` is forbidden. |
| 4 | Naming violations | `updated_by` (line 361) FK → should be `updated_by_id`. |
| 6 | Relationship issues | `country = relationship("CountryConfig", foreign_keys=[country_code])` (line 365) — no `back_populates`. Cross-domain. |
| 7 | Missing FK index | `updated_by` (line 361) has no `index=True`. (`country_code` has `index=True` on line 340.) |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `PromotionLedgerEntry` (line 368)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "commerce"},)` (line 370). Should be `governance`. |
| 2 | FK to forbidden schema | `user_id` (line 373) FK to `core.users.id`. `core` is forbidden. |
| 7 | Missing FK index | `user_id` (line 373) has no `index=True`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `PromotionOrderTier` (line 380)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "commerce"},)` (line 382). Should be `governance`. |
| 2 | FK to forbidden schema | `updated_by` (line 394) FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `updated_by` (line 394) FK → should be `updated_by_id`. |
| 7 | Missing FK index | `updated_by` (line 394) has no `index=True`. (`country_code` has `index=True` on line 395.) |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `LogisticsCODRemittanceReceipt` (line 401)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "logistics"},)` (line 403). Should be `governance`. |
| 2 | FK to forbidden schema | `reviewed_by` (line 413) FK to `core.users.id`. `core` is forbidden. `partner_id` (line 405) FK to `logistics.logistics_partners.id` — not forbidden. |
| 4 | Naming violations | `reviewed_by` (line 413) FK → should be `reviewed_by_id`. |
| 7 | Missing FK index | `partner_id` (line 405), `shipment_id` (line 406), `settlement_id` (line 407), `reviewed_by` (line 413) — no `index=True` on any. |
| 6 | Relationship issues | `settlement = relationship("LogisticsSettlement", foreign_keys=[settlement_id])` (line 418) — no `back_populates`. `partner = relationship("LogisticsPartner", foreign_keys=[partner_id])` (line 419) — no `back_populates`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `LogisticsPartnerBankAccount` (line 422)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "logistics"},)` (line 424). Should be `governance`. |
| 2 | FK to forbidden schema | `verified_by` (line 443) FK to `core.users.id`. `core` is forbidden. `partner_id` (line 426) FK to `logistics.logistics_partners.id` — not forbidden. |
| 4 | Naming violations | `verified_by` (line 443) FK → should be `verified_by_id`. |
| 7 | Missing FK index | `partner_id` (line 426), `verified_by` (line 443) — no `index=True`. |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `LogisticsPartnerDocument` (line 450)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "logistics"},)` (line 452). Should be `governance`. |
| 2 | FK to forbidden schema | `reviewed_by` (line 457) FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `reviewed_by` (line 457) FK → should be `reviewed_by_id`. |
| 7 | Missing FK index | `partner_id` (line 454), `reviewed_by` (line 457) — no `index=True`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `LogisticsSettlement` (line 464)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "logistics"},)` (line 466). Should be `governance`. |
| 2 | FK to forbidden schema | None to `core`/`platform`/`identity`. FKs: `partner_id` → `logistics.logistics_partners.id`, `order_id` → `commerce.orders.id`, `shipment_id` → `logistics.shipments.id`, `payout_id` → `treasury.payouts.id`. |
| 7 | Missing FK index | `partner_id` (line 468), `order_id` (line 469), `shipment_id` (line 471), `payout_id` (line 483) — no `index=True` on any. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |
| 4 | Naming violations | `bank_transaction_id` (line 484) is `Column(Integer, nullable=True)` with NO ForeignKey — orphaned FK-like column. Should either have `ForeignKey("finance.bank_transactions.id")` or be renamed. |

---

### Class: `ShipmentConfirmation` (line 489)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "logistics"},)` (line 491). Should be `governance`. |
| 2 | FK to forbidden schema | `supplier_id` (line 495), `requester_user_id` (line 496), `target_user_id` (line 498) all FK to `core.users.id`. `core` is forbidden. |
| 7 | Missing FK index | `shipment_id` (line 493), `order_id` (line 494), `supplier_id` (line 495), `requester_user_id` (line 496), `target_user_id` (line 498) — no `index=True`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `ChatbotQueryEvent` (line 518)
| # | Criterion | Issue |
|---|-----------|-------|
| 2 | FK to forbidden schema | `user_id` (line 531) FK to `core.users.id`. `core` is forbidden. `clicked_product_id` (line 540) FK to `commerce.products.id` — not forbidden. |
| 7 | Missing FK index | `user_id` (line 531) has no `index=True`. (There IS an index on `clicked_product_id` via `ix_chatbot_events_clicked_product_id` at line 525.) |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |
| 6 | Relationship issues | `__constraints__` attribute (line 544) — should be `__table_args__` for `CheckConstraint`. SQLAlchemy does not recognize `__constraints__` as a table argument; the CheckConstraint will NOT be applied to the table. |

**Schema:** `governance` ✓ (line 528)

---

### Class: `PushNotificationToken` (line 549)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "communication"},)` (line 551). Should be `governance`. |
| 2 | FK to forbidden schema | `user_id` (line 553) FK to `core.users.id`. `core` is forbidden. |
| 7 | Missing FK index | `user_id` (line 553) has no `index=True`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `ProductVerification` (line 560)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "commerce"},)` (line 562). Should be `governance`. |
| 2 | FK to forbidden schema | `verified_by` (line 566) FK to `core.users.id`. `core` is forbidden. `product_id` (line 564) FK to `commerce.products.id` — not forbidden. |
| 4 | Naming violations | `verified_by` (line 566) FK → should be `verified_by_id`. |
| 7 | Missing FK index | `product_id` (line 564), `verified_by` (line 566), `shipment_id` (line 567), `order_id` (line 577) — no `index=True`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `SupplierBankAccount` (line 581)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "supplier"},)` (line 583). Should be `governance`. |
| 2 | FK to forbidden schema | `supplier_id` (line 585), `verified_by` (line 602) both FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `verified_by` (line 602) FK → should be `verified_by_id`. |
| 7 | Missing FK index | `supplier_id` (line 585), `verified_by` (line 602) — no `index=True`. |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `ProcessedWebhookEvent` (line 609)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "analytics"},)` (line 611). Should be `governance`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. Has `created_at` (line 617) and `country_code` (line 618). |
| 7 | Missing FK index | N/A — no FK columns. |

---

### Class: `NormalizedWebhookEvent` (line 631)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "analytics"},)` (line 633). Should be `governance`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. Has `created_at` (line 652) and `country_code` (line 653). |

---

### Class: `EmployeeExpense` (line 656)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "hr"},)` (line 658). Should be `governance`. |
| 2 | FK to forbidden schema | `approved_by` (line 665) FK to `core.users.id`. `core` is forbidden. `employee_id` (line 660) FK to `logistics.employees.id` — not forbidden. |
| 4 | Naming violations | `approved_by` (line 665) FK → should be `approved_by_id`. |
| 7 | Missing FK index | `approved_by` (line 665) has no `index=True`. (`employee_id` has `index=True` on line 660.) |
| 6 | Relationship issues | `employee = relationship("Employee", backref="expenses")` (line 671) — uses `backref` instead of `back_populates`. `approver = relationship("User", foreign_keys=[approved_by])` (line 672) — no `back_populates`. |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `SupplierDispute` (line 675)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "supplier"},)` (line 677). Should be `governance`. |
| 2 | FK to forbidden schema | `supplier_id` (line 679), `created_by` (line 693), `resolved_by` (line 696) all FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `created_by` (line 693) FK → should be `created_by_id`. `resolved_by` (line 696) FK → should be `resolved_by_id`. |
| 7 | Missing FK index | `supplier_id` (line 679), `order_id` (line 680), `return_request_id` (line 685), `created_by` (line 693), `resolved_by` (line 696) — no `index=True` on any. |
| 4 | Naming violations (orphaned) | `verification_id` (line 686) — `Column(Integer, nullable=True)` with no FK. `invoice_id` (line 687) — no FK. `related_order_id` (line 688) — no FK but named like one. |
| 3 | Missing audit columns | Missing `is_deleted`, `version`. |

---

### Class: `SupplierCountryCommission` (line 704)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "supplier"},)` (line 706). Should be `governance`. |
| 2 | FK to forbidden schema | `supplier_id` (line 708) FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `country_code` (line 709) is `Column(String(10), nullable=False)` with no FK constraint, even though the same column in other models has `ForeignKey("country.country_configs.code")`. Inconsistency. |
| 7 | Missing FK index | `supplier_id` (line 708) has no `index=True`. |
| 3 | Missing audit columns | Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `RetentionJobRun` (line 717)
| # | Criterion | Issue |
|---|-----------|-------|
| 3 | Missing audit columns | Has no `created_at` (uses `started_at` instead). Missing `updated_at`, `is_deleted`, `version`. |

**Schema:** `governance` ✓ (line 719)

---

## FILE: `core.py` (3 inline model classes + re-export shims)

### Class: `UserBrowsingHistory` (line 45)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "core"},)` (line 47). Should be `governance`. |
| 2 | FK to forbidden schema | `user_id` (line 49) FK to `core.users.id`. `core` is forbidden. `product_id` (line 50) FK to `commerce.products.id` — not forbidden. |
| 4 | Naming violations | Table name `user_browsing_history` (line 46) is singular. Should be `user_browsing_histories` (plural convention). |
| 7 | Missing FK index | `product_id` (line 50) has `index=True` ✓. `user_id` (line 49) has `index=True` ✓. |
| 3 | Missing audit columns | Missing `created_at` (has `viewed_at` instead), `updated_at`, `is_deleted`, `version`. |

---

### Class: `SystemHealthEvent` (line 54)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (line 63) uses `{"schema": "customer"}`. Should be `governance`. Also, `__table_args__` is placed at the END of the class body (after column definitions) instead of immediately after `__tablename__` like the convention in other models — stylistically inconsistent. |
| 3 | Missing audit columns | Has `created_at` (line 62). Missing `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `UserSession` (line 66)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (line 77) uses `{"schema": "customer"}`. Should be `governance`. Also, `__table_args__` is placed at the END of the class body. |
| 2 | FK to forbidden schema | `user_id` (line 69) FK to `core.users.id`. `core` is forbidden. |
| 7 | Missing FK index | `user_id` (line 69) has `index=True` ✓. `session_token` is indexed ✓. |
| 3 | Missing audit columns | Has `created_at` (line 75) and `country_code` (line 76). Missing `updated_at`, `is_deleted`, `version`. |

**Re-export shims (lines 84-140):** The `_CANONICAL_EXPORTS` dict correctly re-exports models from other domains (accounts, audit, comms, analytics, security, logistics, hr). No inline model definitions — no issues to report for these.

---

## FILE: `fraud.py` (18 model classes)

### Class: `FraudEvent` (line 16)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (lines 18-21) uses `{"schema": "security"}`. Should be `governance`. |
| 2 | FK to forbidden schema | `user_id` (line 24), `reviewed_by` (line 35) both FK to `core.users.id`. `core` is forbidden. `order_id` (line 25) FK to `commerce.orders.id` — not forbidden. |
| 4 | Naming violations | `reviewed_by` (line 35) FK → should be `reviewed_by_id`. |
| 7 | Missing FK index | `user_id` (line 24), `order_id` (line 25), `reviewed_by` (line 35) — no `index=True` on any. |
| 6 | Relationship issues | `user = relationship("User", foreign_keys=[user_id])` (line 40) — no `back_populates`. `reviewer = relationship("User", foreign_keys=[reviewed_by])` (line 41) — no `back_populates`. Cross-domain, no explicit lazy strategy. |
| 3 | Missing audit columns | Has `created_at` (line 37) and `country_code` (line 38). Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `FraudBlacklist` (line 44)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (lines 46-47) uses `{"schema": "security"}`. Should be `governance`. |
| 4 | Naming violations | Table name `fraud_blacklist` (line 45) is singular. Should be `fraud_blacklists`. |
| 3 | Missing audit columns | Has `created_at` (line 56). Missing `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `FraudRule` (line 60)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (line 62) uses `{"schema": "security"}`. Should be `governance`. |
| 3 | Missing audit columns | Has `created_at` (line 74). Missing `updated_at`, `is_deleted`, `version`. Has `country_code` (line 73) but not indexed. |

---

### Class: `ManualReviewQueue` (line 77)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (lines 79-81) uses `{"schema": "security"}`. Should be `governance`. |
| 4 | Naming violations | Table name `manual_review_queue` (line 78) is singular. Should be `manual_review_queues`. |
| 2 | FK to forbidden schema | `assigned_to` (line 90) FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations (FK) | `assigned_to` (line 90) FK → should be `assigned_to_id`. |
| 7 | Missing FK index | `assigned_to` (line 90) has no `index=True`. |
| 3 | Missing audit columns | Has `created_at` (line 93), `updated_at` (line 94). Missing `is_deleted`, `version`, `country_code`. |

---

### Class: `IPReputation` (line 97)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (line 99) uses `{"schema": "security"}`. Should be `governance`. |
| 3 | Missing audit columns | Has `updated_at` (line 112), `created_at` (line 113), `country_code` (line 110). Missing `is_deleted`, `version`. |

---

### Class: `DeviceFingerprint` (line 116)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (line 118) uses `{"schema": "security"}`. Should be `governance`. |
| 2 | FK to forbidden schema | `user_id` (line 121) FK to `core.users.id`. `core` is forbidden. |
| 7 | Missing FK index | `user_id` (line 121) has no `index=True`. (`fingerprint_hash` has `index=True` ✓.) |
| 6 | Relationship issues | `user = relationship("User")` (line 133) — no `back_populates`, no `foreign_keys` specified, no explicit lazy strategy. |
| 3 | Missing audit columns | Has `first_seen_at` (line 130), `last_seen_at` (line 131). Missing `created_at`, `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `CreditCardBin` (line 136)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "security"},)` (line 138). Should be `governance`. |
| 3 | Missing audit columns | Has `created_at` (line 145). Missing `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `ReturnAbusePattern` (line 148)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "commerce"},)` (line 150). Should be `governance`. |
| 2 | FK to forbidden schema | `user_id` (line 152) FK to `core.users.id`. `core` is forbidden. |
| 7 | Missing FK index | `user_id` (line 152) has no `index=True`. |
| 6 | Relationship issues | `user = relationship("User")` (line 159) — no `back_populates`, no explicit lazy strategy. |
| 3 | Missing audit columns | Has `first_occurrence` (line 155), `last_occurrence` (line 156). Missing `created_at` (uses `first_occurrence` instead), `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `SupplierFraudIndicator` (line 162)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "supplier"},)` (line 164). Should be `governance`. |
| 2 | FK to forbidden schema | `supplier_id` (line 166) FK to `core.users.id`. `core` is forbidden. |
| 7 | Missing FK index | `supplier_id` (line 166) has no `index=True`. |
| 3 | Missing audit columns | Has `created_at` (line 170), `country_code` (line 171). Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `LogisticsFraudIndicator` (line 174)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "logistics"},)` (line 176). Should be `governance`. |
| 2 | FK to forbidden schema | `partner_id` (line 178) FK to `logistics.logistics_partners.id` — not forbidden. No FK to `core`. |
| 7 | Missing FK index | `partner_id` (line 178) has no `index=True`. |
| 3 | Missing audit columns | Has `created_at` (line 182), `country_code` (line 183). Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `FraudAlert` (line 186)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "security"},)` (line 188). Should be `governance`. |
| 3 | Missing audit columns | Has `created_at` (line 199), `country_code` (line 200). Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `IPAccountLinkage` (line 203)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "security"},)` (line 205). Should be `governance`. |
| 2 | FK to forbidden schema | `user_id` (line 208) FK to `core.users.id`. `core` is forbidden. |
| 7 | Missing FK index | `user_id` (line 208) has no `index=True`. (`ip_address` has `index=True` ✓.) |
| 6 | Relationship issues | `user = relationship("User")` (line 215) — no `back_populates`, no explicit lazy strategy. |
| 3 | Missing audit columns | Has `last_seen` (line 213). Missing `created_at`, `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `VelocityCounter` (line 218)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (line 220) uses `{"schema": "security"}`. Should be `governance`. |
| 3 | Missing audit columns | Has `created_at` (line 229). Missing `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `FraudScoringLog` (line 232)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (lines 236-237) uses `{"schema": "security"}`. Should be `governance`. |
| 2 | FK to forbidden schema | `user_id` (line 240), `order_id` (line 241) — `user_id` FK to `core.users.id` (forbidden). `order_id` FK to `commerce.orders.id` (not forbidden). |
| 7 | Missing FK index | `user_id` (line 240), `order_id` (line 241) — no `index=True`. |
| 6 | Relationship issues | `user = relationship("User")` (line 252) — no `back_populates`, no `foreign_keys`, no explicit lazy strategy. |
| 3 | Missing audit columns | Has `created_at` (line 249), `country_code` (line 250). Missing `updated_at`, `is_deleted`, `version`. |

---

### Class: `FraudCase` (line 255)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (lines 257-259) uses `{"schema": "security"}`. Should be `governance`. |
| 2 | FK to forbidden schema | `assigned_to` (line 270), `created_by` (line 271) both FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `assigned_to` (line 270) FK → should be `assigned_to_id`. `created_by` (line 271) FK → should be `created_by_id`. |
| 7 | Missing FK index | `assigned_to` (line 270), `created_by` (line 271) — no `index=True`. |
| 6 | Relationship issues | `assignee = relationship("User", foreign_keys=[assigned_to])` (line 278) — no `back_populates`. `creator = relationship("User", foreign_keys=[created_by])` (line 279) — no `back_populates`. |
| 3 | Missing audit columns | Has `created_at` (line 274), `updated_at` (line 275), `country_code` (line 276). Missing `is_deleted`, `version`. |

---

### Class: `FraudCaseAssignment` (line 282)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "security"},)` (line 285). Should be `governance`. Note: `__table_args__` is placed AFTER `__tablename__` with a blank line and extra spacing — unconventional formatting. |
| 2 | FK to forbidden schema | `assigned_to` (line 289), `assigned_by` (line 290) both FK to `core.users.id`. `core` is forbidden. `case_id` (line 288) FK to `security.fraud_cases.id` — self-referential within same class, not forbidden. |
| 4 | Naming violations | `assigned_to` (line 289) FK → should be `assigned_to_id`. `assigned_by` (line 290) FK → should be `assigned_by_id`. |
| 7 | Missing FK index | `case_id` (line 288), `assigned_to` (line 289) — no `index=True`. |
| 6 | Relationship issues | `case = relationship("FraudCase")` (line 294) — no `back_populates` (the `FraudCase` model has no reciprocal relationship). `assignee = relationship("User", foreign_keys=[assigned_to])` (line 295) — no `back_populates`. `assigner = relationship("User", foreign_keys=[assigned_by])` (line 296) — no `back_populates`. |
| 3 | Missing audit columns | Has `created_at` (line 292). Missing `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `DLPViolation` (line 299)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (lines 301-303) uses `{"schema": "security"}`. Should be `governance`. |
| 2 | FK to forbidden schema | `sender_id` (line 308), `reviewed_by` (line 313) both FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `reviewed_by` (line 313) FK → should be `reviewed_by_id`. (`sender_id` is OK — follows `_id` convention.) |
| 7 | Missing FK index | `sender_id` (line 308), `reviewed_by` (line 313) — no `index=True`. |
| 6 | Relationship issues | `sender = relationship("User", foreign_keys=[sender_id])` (line 317) — no `back_populates`. `reviewer = relationship("User", foreign_keys=[reviewed_by])` (line 318) — no `back_populates`. |
| 3 | Missing audit columns | Has `created_at` (line 315). Missing `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `MeetingTranscript` (line 321)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (line 323) uses `{"schema": "security"}`. Should be `governance`. |
| 3 | Missing audit columns | Has `created_at` (line 333). Missing `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `MeetingActionItem` (line 336)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (lines 338-340) uses `{"schema": "security"}`. Should be `governance`. |
| 2 | FK to forbidden schema | `assigned_to` (line 349) FK to `core.users.id`. `core` is forbidden. `meeting_id` (line 343) FK to `security.meeting_transcripts.id` — self-referential, not forbidden. |
| 4 | Naming violations | `assigned_to` (line 349) FK → should be `assigned_to_id`. |
| 7 | Missing FK index | `meeting_id` (line 343), `assigned_to` (line 349) — no `index=True`. |
| 6 | Relationship issues | `meeting = relationship("MeetingTranscript", backref="items")` (line 353) — uses `backref` instead of `back_populates`. `assignee = relationship("User")` (line 354) — no `back_populates`, no `foreign_keys`, no explicit lazy strategy. |
| 3 | Missing audit columns | Has `created_at` (line 350). Missing `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `MeetingRecording` (line 357)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__` (line 360) uses `{"schema": "communication"}`. Should be `governance`. Note: `__table_args__` is placed on a separate line with preceding blank line — unconventional formatting. |
| 2 | FK to forbidden schema | `started_by` (line 364) FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `started_by` (line 364) FK → should be `started_by_id`. |
| 7 | Missing FK index | `started_by` (line 364) has no `index=True`. |
| 6 | Relationship issues | `starter = relationship("User")` (line 372) — no `back_populates`, no `foreign_keys`, no explicit lazy strategy. |
| 3 | Missing audit columns | Has `created_at` (line 370). Missing `updated_at`, `is_deleted`, `version`, `country_code`. |

---

## FILE: `incident.py` (4 model classes)

### Class: `IncidentWarRoom` (line 11)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "communication"},)` (line 13). Should be `governance`. |
| 2 | FK to forbidden schema | `created_by` (line 19) FK to `core.users.id`. `core` is forbidden. |
| 4 | Naming violations | `created_by` (line 19) FK → should be `created_by_id`. |
| 7 | Missing FK index | `created_by` (line 19) has no `index=True`. (`incident_id` has `index=True` ✓.) |
| 6 | Relationship issues | `creator = relationship("User")` (line 26) — no `back_populates`, no `foreign_keys`, no explicit lazy strategy. |
| 3 | Missing audit columns | Has `started_at` (line 20). Missing `created_at`, `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `IncidentThread` (line 29)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "communication"},)` (line 31). Should be `governance`. |
| 2 | FK to forbidden schema | `participant_id` (line 34) FK to `core.users.id`. `core` is forbidden. `war_room_id` (line 33) FK to `communication.incident_war_rooms.id` — same class, not forbidden. |
| 7 | Missing FK index | `war_room_id` (line 33) has no `index=True`. `participant_id` (line 34) has no `index=True`. |
| 6 | Relationship issues | `participant = relationship("User")` (line 38) — no `back_populates`, no `foreign_keys`, no explicit lazy strategy. |
| 3 | Missing audit columns | Has `created_at` (line 36). Missing `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `IncidentActionItem` (line 41)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "communication"},)` (line 43). Should be `governance`. |
| 2 | FK to forbidden schema | `assignee_id` (line 46) FK to `core.users.id`. `core` is forbidden. `war_room_id` (line 45) FK to `communication.incident_war_rooms.id` — same class, not forbidden. |
| 7 | Missing FK index | `war_room_id` (line 45) has no `index=True`. `assignee_id` (line 46) has no `index=True`. |
| 6 | Relationship issues | `assignee = relationship("User")` (line 55) — no `back_populates`, no `foreign_keys`, no explicit lazy strategy. |
| 3 | Missing audit columns | Has `created_at` (line 52). Missing `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `WarRoomTemplate` (line 58)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "communication"},)` (line 60). Should be `governance`. |
| 3 | Missing audit columns | Has `created_at` (line 66). Missing `updated_at`, `is_deleted`, `version`, `country_code`. |

---

## FILE: `onboarding.py` (5 model classes)

### Class: `OnboardingPipeline` (line 11)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "hr"},)` (line 13). Should be `governance`. |
| 2 | FK to forbidden schema | `user_id` (line 15) FK to `core.users.id`. `core` is forbidden. `pipeline_id` FKs in other classes point to `hr.onboarding_pipelines.id`. |
| 7 | Missing FK index | `user_id` (line 15) has `index=True` ✓. |
| 6 | Relationship issues | `user = relationship("User")` (line 22) — no `back_populates`, no `foreign_keys`, no explicit lazy strategy. |
| 3 | Missing audit columns | Has `started_at` (line 20). Missing `created_at` (uses `started_at`), `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `OnboardingStep` (line 27)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "hr"},)` (line 29). Should be `governance`. |
| 7 | Missing FK index | `pipeline_id` (line 31) has no `index=True`. |
| 3 | Missing audit columns | Has `started_at` (line 35). Missing `created_at`, `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `DocumentVerification` (line 40)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "security"},)` (line 42). Should be `governance`. |
| 2 | FK to forbidden schema | `verifier_id` (line 49) FK to `core.users.id`. `core` is forbidden. `pipeline_id` (line 44) FK to `hr.onboarding_pipelines.id` — not forbidden. |
| 4 | Naming violations | `verifier_id` (line 49) follows `_id` convention ✓. |
| 7 | Missing FK index | `pipeline_id` (line 44), `verifier_id` (line 49) — no `index=True`. |
| 6 | Relationship issues | `verifier = relationship("User")` (line 51) — no `back_populates`, no `foreign_keys`, no explicit lazy strategy. |
| 3 | Missing audit columns | Missing `created_at`, `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `OCRResult` (line 54)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "media"},)` (line 56). Should be `governance`. |
| 7 | Missing FK index | `document_verification_id` (line 58) has `unique=True` which creates a unique index — this provides index coverage. ✓ |
| 6 | Relationship issues | `document_verification = relationship("DocumentVerification", backref="ocr_result", uselist=False)` (line 63) — uses `backref` instead of `back_populates`. The target model `DocumentVerification` has no matching relationship definition. |
| 3 | Missing audit columns | Has `processed_at` (line 62). Missing `created_at`, `updated_at`, `is_deleted`, `version`, `country_code`. |

---

### Class: `KYCVerification` (line 66)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "security"},)` (line 68). Should be `governance`. |
| 2 | FK to forbidden schema | `user_id` (line 70), `reviewer_id` (line 77) both FK to `core.users.id`. `core` is forbidden. |
| 7 | Missing FK index | `user_id` (line 70) has `index=True` ✓. `reviewer_id` (line 77) has no `index=True`. |
| 6 | Relationship issues | `user = relationship("User", foreign_keys=[user_id])` (line 78) — no `back_populates`. `reviewer = relationship("User", foreign_keys=[reviewer_id])` (line 79) — no `back_populates`. |
| 3 | Missing audit columns | Has `submitted_at` (line 75). Missing `created_at`, `updated_at`, `is_deleted`, `version`, `country_code`. |

---

## FILE: `otp.py` (1 model class)

### Class: `OtpCode` (line 11)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ({"schema": "accounts"},)` (line 15). Should be `governance`. |
| 7 | Missing FK index | `user_id` (line 18) has `index=True` ✓. `country_code` (line 26) has `index=True` ✓. |
| 3 | Missing audit columns | Has `created_at` (line 27), `country_code` (line 26). Missing `updated_at`, `is_deleted`, `version`. |

---

## FILE: `permissions.py` (5 model classes)

### Class: `PermissionCategory` (line 17)
| # | Criterion | Issue |
|---|-----------|-------|
| 5 | Import inconsistency | Line 5: `from infrastructure.database.base import Base` — uses absolute import. All other governance model files use `from . import Base` (relative import). |
| 4 | Naming violations | `country_code` (line 27) has `server_default="OM"` — hardcoded country default. This is a business logic concern but flagged as suspicious. |
| 3 | Missing audit columns | Has `created_at` (line 28), `updated_at` (line 29), `country_code` (line 27). Missing `is_deleted`, `version`. |
| 2 | FK to forbidden schema | No FK columns in this class. |

**Schema:** `governance` ✓ (line 19)

---

### Class: `Permission` (line 34)
| # | Criterion | Issue |
|---|-----------|-------|
| 7 | Missing FK index | `category_id` (line 38) has no `index=True`. |
| 3 | Missing audit columns | Has `created_at` (line 45), `country_code` (line 44). Missing `updated_at`, `is_deleted`, `version`. |

**Schema:** `governance` ✓ (line 36)

---

### Class: `RolePermissionAssignment` (line 50)
| # | Criterion | Issue |
|---|-----------|-------|
| 2 | FK to forbidden schema | `granted_by` (line 60) FK to `accounts.users.id` — NOT in forbidden list (core/platform/identity) ✓. `country_code` (line 59) FK to `country.country_configs.code` — not forbidden ✓. `permission_id` (line 58) FK to `governance.permissions.id` — same domain ✓. |
| 4 | Naming violations | `granted_by` (line 60) FK → should be `granted_by_id`. |
| 7 | Missing FK index | `permission_id` (line 58), `granted_by` (line 60) — no `index=True`. (`country_code` has `index=True` via FK? No — line 59: `ForeignKey(..., nullable=True)` without `index=True`. But `country_code` does have `index=True` on line 59? Let me re-check: `country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True)` — no `index=True`. Wait, I need to re-read.) |

Let me re-check line 59 of permissions.py:
```python
country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True)
```
No `index=True`. So missing index on `country_code`, `permission_id`, `granted_by`.

| 3 | Missing audit columns | Has `created_at` (line 62), `updated_at` (line 63), `country_code` (line 59). Missing `is_deleted`, `version`. |

**Schema:** `governance` ✓ (line 54)

---

### Class: `UserPermissionOverride` (line 66)
| # | Criterion | Issue |
|---|-----------|-------|
| 4 | Naming violations | `granted_by` (line 77) FK → should be `granted_by_id`. |
| 7 | Missing FK index | `user_id` (line 73), `permission_id` (line 74), `granted_by` (line 77) — no `index=True`. (`country_code` on line 75 has no `index=True`.) |
| 3 | Missing audit columns | Has `created_at` (line 79), `country_code` (line 75). Missing `updated_at`, `is_deleted`, `version`. |

**Schema:** `governance` ✓ (line 70)

---

### Class: `PermissionAuditLog` (line 82)
| # | Criterion | Issue |
|---|-----------|-------|
| 4 | Naming violations | Table name `permission_audit_log` (line 83) is singular. Should be `permission_audit_logs`. |
| 7 | Missing FK index | `actor_id` (line 86), `target_user_id` (line 88), `permission_id` (line 90) — no `index=True`. (`country_code` on line 91 is `Column(String(10), nullable=True)` — no FK, no index.) |
| 2 | FK to forbidden schema | `actor_id` (line 86), `target_user_id` (line 88) FK to `accounts.users.id` — not forbidden ✓. `permission_id` (line 90) FK to `governance.permissions.id` — same domain ✓. |
| 3 | Missing audit columns | Has `created_at` (line 92). Missing `updated_at`, `is_deleted`, `version`. |

**Schema:** `governance` ✓ (line 84)

---

## FILE: `social.py` (1 model class)

### Class: `SocialIdentity` (line 11)
| # | Criterion | Issue |
|---|-----------|-------|
| 1 | Schema discipline | `__table_args__ = ("accounts")` (line 17). Should be `governance`. |
| 7 | Missing FK index | `user_id` (line 21) has `index=True` ✓. |
| 3 | Missing audit columns | Has `created_at` (line 26). Missing `updated_at`, `is_deleted`, `version`, `country_code`. |
| 6 | Relationship issues | No `user = relationship("User")` defined despite having `user_id` FK. The model has no relationship to its parent User. |

---

## FILE: `user.py` (0 inline model classes)

**Pure re-export shim only.** All 9 names in `__all__` are lazily imported from their canonical domains:
- `User`, `UserLoginHistory`, `UserDevice`, `PasswordResetToken`, `EmailVerificationToken`, `RevokedToken`, `OtpCode`, `SocialIdentity` → `domains.accounts.models.user`
- `Referral`, `ReferralPointEvent` → `domains.customers.models.customer_schema_models`

**No inline model definitions — no issues to report.**

---

## SUMMARY BY CRITERION

### 1. Schema discipline (`governance`)
**38 models** use a non-`governance` schema. Breakdown by wrong schema used:

| Wrong Schema | Count | Files |
|---|---|---|
| `core` | 4 | admin.py (1), core.py (1) |
| `configuration` | 3 | admin.py (2),  |
| `commerce` | 15 | admin.py (10), fraud.py (1), onboarding.py (0 — has `security`/`hr`/`media`) |
| `communication` | 7 | admin.py (2), incident.py (4) |
| `logistics` | 7 | admin.py (4), fraud.py (1) |
| `supplier` | 4 | admin.py (3), fraud.py (1) |
| `treasury` | 3 | admin.py (3) |
| `analytics` | 2 | admin.py (2) |
| `hr` | 2 | onboarding.py (2) |
| `media` | 1 | onboarding.py (1) |
| `security` | 14 | fraud.py (12), onboarding.py (2) |
| `customer` | 2 | core.py (2) |
| `accounts` | 1 | social.py (1) |

Models with correct `governance` schema: `AdminAnalyticsSnapshot`, `AdminChangeAuditLog`, `AdminActivityLog`, `ChatbotQueryEvent`, `RetentionJobRun` (admin.py); `PermissionCategory`, `Permission`, `RolePermissionAssignment`, `UserPermissionOverride`, `PermissionAuditLog` (permissions.py)

### 2. FK to forbidden schemas (`core`/`platform`/`identity`)
**59 FK columns** reference `core.users.id` across 6 files:
- `admin.py`: 31 FK columns → `core.users.id`
- `fraud.py`: 15 FK columns → `core.users.id`
- `core.py`: 2 FK columns → `core.users.id`
- `incident.py`: 4 FK columns → `core.users.id`
- `onboarding.py`: 4 FK columns → `core.users.id`

**0 FK columns** reference `platform` or `identity` schemas.

### 3. Missing audit columns
The audit column set `{created_at, updated_at, is_deleted, version, country_code}` is checked for each model. **44 of 49 inline models** are missing at least one audit column. Only 5 models have all 5:
- `PermissionCategory` — missing `is_deleted`, `version` (missing 2)
- `RolePermissionAssignment` — missing `is_deleted`, `version` (missing 2)
- `UserSession` — missing `updated_at`, `is_deleted`, `version` (missing 3)

Actually, reviewing more carefully, the only models that are close to complete are in `permissions.py` and a few in `admin.py`. The vast majority (44/49) are missing at least 2 audit columns.

### 4. Naming violations
- **Singular table names** (should be plural): `fraud_blacklist`, `manual_review_queue`, `coupon_usage`, `user_browsing_history`, `permission_audit_log` (5 total)
- **FK columns not following `<thing>_id`** (should end with `_id`): `acknowledged_by`, `created_by` (5 instances), `updated_by` (7 instances), `reviewed_by` (4 instances), `verified_by` (3 instances), `approved_by`, `resolved_by`, `started_by`, `assigned_to` (4 instances), `assigned_by`, `granted_by` (2 instances) — 27 total FK columns with non-`_id` names

### 5. Duplicate models
None found. All 49 `__tablename__` values are unique across the 9 files. No `__tablename__` collision.

### 6. Relationship issues
- **5 relationships using `backref` instead of `back_populates`**: `CouponUsage.coupon`, `OCRResult.document_verification`, `MeetingActionItem.meeting`, `EmployeeExpense.employee`
- **35+ cross-domain relationships** with no `back_populates` and no explicit `lazy` strategy — potential N+1 lazy-load risk
- **1 broken `__constraints__` attribute** on `ChatbotQueryEvent` (line 544) — should be `__table_args__`
- **1 missing relationship**: `SocialIdentity` has `user_id` FK but no `user = relationship("User")`

### 7. Missing indexes on FK columns
Dozens of FK columns lack `index=True`:
- `admin.py`: ~25 FK columns without indexes (of ~40 total FKs)
- `fraud.py`: ~14 FK columns without indexes (of ~18 total FKs)
- `incident.py`: 5 FK columns without indexes (of 5 total FKs)
- `onboarding.py`: 4 FK columns without indexes (of 7 total FKs)
- `permissions.py`: ~5 FK columns without indexes (of 8 total FKs)
- `social.py`: 0 (user_id has index)
- `otp.py`: 0 (user_id and country_code both have index)
- `core.py`: 0 (user_id and product_id both have index)

### Additional issues found (beyond the 7 criteria)
- **Import inconsistency** in `permissions.py` line 5: uses `from infrastructure.database.base import Base` (absolute) instead of `from . import Base` (relative) like all other governance files
- **Inconsistent user FK schema**: `permissions.py`, `otp.py`, and `social.py` use `accounts.users.id` for user FKs, while `admin.py`, `fraud.py`, `core.py`, `incident.py`, and `onboarding.py` use `core.users.id` — inconsistency within the governance domain
- **`FraudCaseAssignment.__table_args__` formatting** (line 286): blank line and unconventional placement between `__tablename__` and column definitions
- **`MeetingRecording.__table_args__` formatting** (line 360): `__table_args__` placed after `__tablename__` with a blank line
- **Orphaned non-FK columns named like FKs**: `BadgeBillingRecord.created_by` (line 146), `SupplierDispute.verification_id` (line 686), `SupplierDispute.invoice_id` (line 687), `SupplierDispute.related_order_id` (line 688), `NormalizedWebhookEvent.zozi_order_id` (line 641), `LogisticsSettlement.bank_transaction_id` (line 484) — all plain `Column(Integer)` without `ForeignKey`
- **`SystemSetting.key`** column (line 102): uses `key` as column name — while not a Python reserved keyword, it shadows the builtin `key` parameter name
- **Hardcoded `server_default="OM"`** on `PermissionCategory.country_code` (line 27) and `Permission.country_code` (line 44) — hardcoded Oman country code as default
- **`ChatbotQueryEvent.__constraints__`** (line 544): non-standard SQLAlchemy attribute; `CheckConstraint` will not be applied to the table

