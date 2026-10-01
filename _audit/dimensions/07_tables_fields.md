# Forensic Audit: Tables & Fields

## Laws: 6, 9, 19-24, 45-57


## Table of Contents

- [SupplierBankAccount (supplier_bank_accounts)](#supplierbankaccount-supplier_bank_accounts)
- [LogisticsPartnerBankAccount (logistics_partner_bank_accounts)](#logisticspartnerbankaccount-logistics_partner_bank_accounts)
- [Address (addresses)](#address-addresses)
- [Cart (carts)](#cart-carts)
- [CartItem (cart_items)](#cartitem-cart_items)
- [MfaFactor (mfa_factors)](#mfafactor-mfa_factors)
- [OnboardingPipeline (onboarding_pipelines)](#onboardingpipeline-onboarding_pipelines)
- [OnboardingStep (onboarding_steps)](#onboardingstep-onboarding_steps)
- [OCRResult (ocr_results)](#ocrresult-ocr_results)
- [OtpCode (otp_codes)](#otpcode-otp_codes)
- [PasswordHistory (password_histories)](#passwordhistory-password_histories)
- [RefreshTokenFamily (refresh_token_families)](#refreshtokenfamily-refresh_token_families)
- [SocialIdentity (social_identities)](#socialidentity-social_identities)
- [User (users)](#user-users)
- [UserSession (user_sessions)](#usersession-user_sessions)
- [UserLoginHistory (user_login_histories)](#userloginhistory-user_login_histories)
- [UserDevice (user_devices)](#userdevice-user_devices)
- [PasswordResetToken (password_reset_tokens)](#passwordresettoken-password_reset_tokens)
- [EmailVerificationToken (email_verification_tokens)](#emailverificationtoken-email_verification_tokens)
- [RevokedToken (revoked_tokens)](#revokedtoken-revoked_tokens)
- [UserConsent (user_consents)](#userconsent-user_consents)
- [UserPreference (user_preferences)](#userpreference-user_preferences)
- [ExecutiveNews (executive_news)](#executivenews-executive_news)
- [PredictiveSimulation (predictive_simulations)](#predictivesimulation-predictive_simulations)
- [AuditLog (audit_logs)](#auditlog-audit_logs)
- [CommandCenterView (command_center_views)](#commandcenterview-command_center_views)
- [AIUploadJob (ai_upload_jobs)](#aiuploadjob-ai_upload_jobs)
- [AIStagingProduct (ai_staging_products)](#aistagingproduct-ai_staging_products)
- [AIStagingVariant (ai_staging_variants)](#aistagingvariant-ai_staging_variants)
- [AIGenerationLog (ai_generation_logs)](#aigenerationlog-ai_generation_logs)
- [ChartOfCategory (chart_of_categories)](#chartofcategory-chart_of_categories)
- [ProductType (product_types)](#producttype-product_types)
- [CategoryAttribute (category_attributes)](#categoryattribute-category_attributes)
- [CategoryAttributeValue (category_attribute_values)](#categoryattributevalue-category_attribute_values)
- [CommissionGroup (commission_groups)](#commissiongroup-commission_groups)
- [CommissionProfile (commission_profiles)](#commissionprofile-commission_profiles)
- [CommissionRule (commission_rules)](#commissionrule-commission_rules)
- [CommissionTransaction (commission_transactions)](#commissiontransaction-commission_transactions)
- [Category (categories)](#category-categories)
- [Product (products)](#product-products)
- [Review (reviews)](#review-reviews)
- [WishlistItem (wishlist_items)](#wishlistitem-wishlist_items)
- [Wishlist (wishlists)](#wishlist-wishlists)
- [ProductVariant (product_variants)](#productvariant-product_variants)
- [ProductVideo (product_videos)](#productvideo-product_videos)
- [VideoAnalytics (video_analytics)](#videoanalytics-video_analytics)
- [ProductFilterMetadata (product_filter_metadatas)](#productfiltermetadata-product_filter_metadatas)
- [ProductFilterOption (product_filter_options)](#productfilteroption-product_filter_options)
- [UploadJob (upload_jobs)](#uploadjob-upload_jobs)
- [EntityChatThread (entity_chat_threads)](#entitychatthread-entity_chat_threads)
- [VideoRoom (video_rooms)](#videoroom-video_rooms)
- [VideoRoomParticipant (video_room_participants)](#videoroomparticipant-video_room_participants)
- [DirectChatRoom (direct_chat_rooms)](#directchatroom-direct_chat_rooms)
- [GroupChatMember (group_chat_members)](#groupchatmember-group_chat_members)
- [EscalationSLALog (escalation_sla_logs)](#escalationslalog-escalation_sla_logs)
- [EntityChatMessage (entity_chat_messages)](#entitychatmessage-entity_chat_messages)
- [VideoRoomRecording (video_room_recordings)](#videoroomrecording-video_room_recordings)
- [DirectChatMessage (direct_chat_messages)](#directchatmessage-direct_chat_messages)
- [GroupChatRoom (group_chat_rooms)](#groupchatroom-group_chat_rooms)
- [GroupChatMessage (group_chat_messages)](#groupchatmessage-group_chat_messages)
- [Announcement (announcements)](#announcement-announcements)
- [HelpCategory (help_categories)](#helpcategory-help_categories)
- [ProxyChannel (proxy_channels)](#proxychannel-proxy_channels)
- [ProxySession (proxy_sessions)](#proxysession-proxy_sessions)
- [ProxyMessage (proxy_messages)](#proxymessage-proxy_messages)
- [ProxyCallLog (proxy_call_logs)](#proxycalllog-proxy_call_logs)
- [ExternalContactMasking (external_contact_maskings)](#externalcontactmasking-external_contact_maskings)
- [CommunicationAuditTrail (communication_audit_trails)](#communicationaudittrail-communication_audit_trails)
- [InternalChannelMember (internal_channel_members)](#internalchannelmember-internal_channel_members)
- [InternalMessage (internal_messages)](#internalmessage-internal_messages)
- [ChatReadReceipt (chat_read_receipts)](#chatreadreceipt-chat_read_receipts)
- [ChatAttachment (chat_attachments)](#chatattachment-chat_attachments)
- [EmailFolder (email_folders)](#emailfolder-email_folders)
- [SupportTicket (support_tickets)](#supportticket-support_tickets)
- [SupportTicketReply (support_ticket_replies)](#supportticketreply-support_ticket_replies)
- [TicketAttachment (ticket_attachments)](#ticketattachment-ticket_attachments)
- [NewsSource (news_sources)](#newssource-news_sources)
- [InternalNotice (internal_notices)](#internalnotice-internal_notices)
- [EscalationSLARule (escalation_sla_rules)](#escalationslarule-escalation_sla_rules)
- [MeetingRecording (meeting_recordings)](#meetingrecording-meeting_recordings)
- [IncidentWarRoom (incident_war_rooms)](#incidentwarroom-incident_war_rooms)
- [IncidentThread (incident_threads)](#incidentthread-incident_threads)
- [IncidentActionItem (incident_action_items)](#incidentactionitem-incident_action_items)
- [WarRoomTemplate (war_room_templates)](#warroomtemplate-war_room_templates)
- [EmailTemplate (email_templates)](#emailtemplate-email_templates)
- [NewsletterSubscriber (newsletter_subscribers)](#newslettersubscriber-newsletter_subscribers)
- [EmailCampaignLog (email_campaign_logs)](#emailcampaignlog-email_campaign_logs)
- [CampaignRecipient (campaign_recipients)](#campaignrecipient-campaign_recipients)
- [EmailDeliveryEvent (email_delivery_events)](#emaildeliveryevent-email_delivery_events)
- [EmailSuppression (email_suppressions)](#emailsuppression-email_suppressions)
- [EmailRuntimeConfig (email_runtime_configs)](#emailruntimeconfig-email_runtime_configs)
- [Message (messages)](#message-messages)
- [NewsArticle (news_articles)](#newsarticle-news_articles)
- [CountryConfig (country_configs)](#countryconfig-country_configs)
- [CountryCommunication (country_communications)](#countrycommunication-country_communications)
- [CountryGatewayCredentials (country_gateway_credentials)](#countrygatewaycredentials-country_gateway_credentials)
- [CountryBasics (country_basics)](#countrybasics-country_basics)
- [ShiftHandoverLog (shift_handover_logs)](#shifthandoverlog-shift_handover_logs)
- [PaymentOrchestratorSync (payment_orchestrator_syncs)](#paymentorchestratorsync-payment_orchestrator_syncs)
- [SupplierOnboardingSync (supplier_onboarding_syncs)](#supplieronboardingsync-supplier_onboarding_syncs)
- [DataResidencyRecord (data_residency_records)](#dataresidencyrecord-data_residency_records)
- [CountryMapConfig (country_map_configs)](#countrymapconfig-country_map_configs)
- [ShopWarehouseLocation (shop_warehouse_locations)](#shopwarehouselocation-shop_warehouse_locations)
- [LogisticsPartnerLocation (logistics_partner_locations)](#logisticspartnerlocation-logistics_partner_locations)
- [ParcelLocationTracker (parcel_location_trackers)](#parcellocationtracker-parcel_location_trackers)
- [CountryEconomics (country_economics)](#countryeconomics-country_economics)
- [CountryFeatureFlag (country_feature_flags)](#countryfeatureflag-country_feature_flags)
- [CountryStaffAssignment (country_staff_assignments)](#countrystaffassignment-country_staff_assignments)
- [OmanDeliveryZone (oman_delivery_zones)](#omandeliveryzone-oman_delivery_zones)
- [CountryConfigVersion (country_config_versions)](#countryconfigversion-country_config_versions)
- [SupplierKYCRequirement (supplier_kyc_requirements)](#supplierkycrequirement-supplier_kyc_requirements)
- [LogisticsPartnerKYCRequirement (logistics_partner_kyc_requirements)](#logisticspartnerkycrequirement-logistics_partner_kyc_requirements)
- [CountryCommissionRate (country_commission_rates)](#countrycommissionrate-country_commission_rates)
- [CountryLocalization (country_localizations)](#countrylocalization-country_localizations)
- [CountryPaymentAlias (country_payment_aliases)](#countrypaymentalias-country_payment_aliases)
- [CountryLegalContract (country_legal_contracts)](#countrylegalcontract-country_legal_contracts)
- [CountryCategoryTaxRate (country_category_tax_rates)](#countrycategorytaxrate-country_category_tax_rates)
- [CountryCity (country_cities)](#countrycity-country_cities)
- [CountryHolidayCalendar (country_holiday_calendars)](#countryholidaycalendar-country_holiday_calendars)
- [CountryGatewayConfig (country_gateway_configs)](#countrygatewayconfig-country_gateway_configs)
- [CountryCommunicationThread (country_communication_threads)](#countrycommunicationthread-country_communication_threads)
- [CountryCommissionRateHistory (country_commission_rate_histories)](#countrycommissionratehistory-country_commission_rate_histories)
- [CountryLogisticsZone (country_logistics_zones)](#countrylogisticszone-country_logistics_zones)
- [CountryPayoutRule (country_payout_rules)](#countrypayoutrule-country_payout_rules)
- [CountryLegal (country_legals)](#countrylegal-country_legals)
- [CountryTax (country_taxes)](#countrytax-country_taxes)
- [CrossCountryCustomerSession (cross_country_customer_sessions)](#crosscountrycustomersession-cross_country_customer_sessions)
- [Referral (referrals)](#referral-referrals)
- [ReferralPointEvent (referral_point_events)](#referralpointevent-referral_point_events)
- [CommissionAgreement (commission_agreements)](#commissionagreement-commission_agreements)
- [ProductCommissionOverride (product_commission_overrides)](#productcommissionoverride-product_commission_overrides)
- [CommissionLedgerEntry (commission_ledger_entries)](#commissionledgerentry-commission_ledger_entries)
- [CommissionCategoryRate (commission_category_rates)](#commissioncategoryrate-commission_category_rates)
- [FiscalPeriod (fiscal_periods)](#fiscalperiod-fiscal_periods)
- [TransactionLedger (transaction_ledgers)](#transactionledger-transaction_ledgers)
- [SupplierSettlement (supplier_settlements)](#suppliersettlement-supplier_settlements)
- [JournalEntry (journal_entries)](#journalentry-journal_entries)
- [JournalEntryLine (journal_entry_lines)](#journalentryline-journal_entry_lines)
- [Account (accounts)](#account-accounts)
- [AccountGroup (account_groups)](#accountgroup-account_groups)
- [AccountBalance (account_balances)](#accountbalance-account_balances)
- [ARLedgerEntry (ar_ledger_entries)](#arledgerentry-ar_ledger_entries)
- [APLedger (ap_ledger_entries)](#apledger-ap_ledger_entries)
- [FinancialReport (financial_reports)](#financialreport-financial_reports)
- [Invoice (invoices)](#invoice-invoices)
- [InvoiceItem (invoice_items)](#invoiceitem-invoice_items)
- [RefundLedger (refund_ledgers)](#refundledger-refund_ledgers)
- [BankTransaction (bank_transactions)](#banktransaction-bank_transactions)
- [VATRemittance (vat_remittances)](#vatremittance-vat_remittances)
- [CashAccount (cash_accounts)](#cashaccount-cash_accounts)
- [CashTransaction (cash_transactions)](#cashtransaction-cash_transactions)
- [TreasuryAccount (treasury_accounts)](#treasuryaccount-treasury_accounts)
- [TreasuryTransaction (treasury_transactions)](#treasurytransaction-treasury_transactions)
- [CashFlowForecast (cash_flow_forecasts)](#cashflowforecast-cash_flow_forecasts)
- [CashPositionSnapshot (cash_position_snapshots)](#cashpositionsnapshot-cash_position_snapshots)
- [GatewaySettlementSchedule (gateway_settlement_schedules)](#gatewaysettlementschedule-gateway_settlement_schedules)
- [PendingJournalEntry (pending_journal_entries)](#pendingjournalentry-pending_journal_entries)
- [PayoutBatch (payout_batches)](#payoutbatch-payout_batches)
- [PayoutBatchItem (payout_batch_items)](#payoutbatchitem-payout_batch_items)
- [BankMappingRule (bank_mapping_rules)](#bankmappingrule-bank_mapping_rules)
- [BankStatementImport (bank_statement_imports)](#bankstatementimport-bank_statement_imports)
- [BankStatementLine (bank_statement_lines)](#bankstatementline-bank_statement_lines)
- [FixedAsset (fixed_assets)](#fixedasset-fixed_assets)
- [Accrual (accruals)](#accrual-accruals)
- [ScannedExpense (scanned_expenses)](#scannedexpense-scanned_expenses)
- [AutomationRule (automation_rules)](#automationrule-automation_rules)
- [AutomationLog (automation_logs)](#automationlog-automation_logs)
- [Vendor (vendors)](#vendor-vendors)
- [Customer (customers)](#customer-customers)
- [CostCenter (cost_centers)](#costcenter-cost_centers)
- [APBill (ap_bills)](#apbill-ap_bills)
- [ARInvoice (ar_invoices)](#arinvoice-ar_invoices)
- [BankAccount (bank_accounts)](#bankaccount-bank_accounts)
- [Budget (budgets)](#budget-budgets)
- [BankReconciliation (bank_reconciliations)](#bankreconciliation-bank_reconciliations)
- [RecurringTemplate (recurring_templates)](#recurringtemplate-recurring_templates)
- [FinanceAuditLog (finance_audit_logs)](#financeauditlog-finance_audit_logs)
- [FinanceAutomationLog (finance_automation_logs)](#financeautomationlog-finance_automation_logs)
- [Payment (payments)](#payment-payments)
- [PaymentReconciliationRun (payment_reconciliation_runs)](#paymentreconciliationrun-payment_reconciliation_runs)
- [PaymentGatewayConnection (payment_gateway_connections)](#paymentgatewayconnection-payment_gateway_connections)
- [Payout (payouts)](#payout-payouts)
- [LogisticsPartnerPayout (logistics_partner_payouts)](#logisticspartnerpayout-logistics_partner_payouts)
- [PayoutRule (payout_rules)](#payoutrule-payout_rules)
- [TaxRule (tax_rules)](#taxrule-tax_rules)
- [PayoutRuleCategory (payout_rule_categories)](#payoutrulecategory-payout_rule_categories)
- [PayoutRuleProduct (payout_rule_products)](#payoutruleproduct-payout_rule_products)
- [AdminAnalyticsSnapshot (admin_analytics_snapshots)](#adminanalyticssnapshot-admin_analytics_snapshots)
- [RolePermissionSetting (role_permission_settings)](#rolepermissionsetting-role_permission_settings)
- [SystemAlert (system_alerts)](#systemalert-system_alerts)
- [AdminChangeAuditLog (admin_change_audit_logs)](#adminchangeauditlog-admin_change_audit_logs)
- [AdminActivityLog (admin_activity_logs)](#adminactivitylog-admin_activity_logs)
- [SystemSetting (system_settings)](#systemsetting-system_settings)
- [APIKey (api_keys)](#apikey-api_keys)
- [BadgeBillingRecord (badge_billing_records)](#badgebillingrecord-badge_billing_records)
- [BadgeTransaction (badge_transactions)](#badgetransaction-badge_transactions)
- [BadgeTier (badge_tiers)](#badgetier-badge_tiers)
- [CommissionBadgeTier (commission_badge_tiers)](#commissionbadgetier-commission_badge_tiers)
- [CommissionGlobalConfig (commission_global_configs)](#commissionglobalconfig-commission_global_configs)
- [TicketReply (ticket_replies)](#ticketreply-ticket_replies)
- [PaymentProviderConfig (payment_provider_configs)](#paymentproviderconfig-payment_provider_configs)
- [EmailProviderConfig (email_provider_configs)](#emailproviderconfig-email_provider_configs)
- [ShippingCarrier (shipping_carriers)](#shippingcarrier-shipping_carriers)
- [ShippingZone (shipping_zones)](#shippingzone-shipping_zones)
- [FinanceBankAccount (finance_bank_accounts)](#financebankaccount-finance_bank_accounts)
- [PromotionOrderTier (promotion_order_tiers)](#promotionordertier-promotion_order_tiers)
- [LogisticsCODRemittanceReceipt (logistics_cod_remittance_receipts)](#logisticscodremittancereceipt-logistics_cod_remittance_receipts)
- [LogisticsPartnerDocument (logistics_partner_documents)](#logisticspartnerdocument-logistics_partner_documents)
- [LogisticsSettlement (logistics_settlements)](#logisticssettlement-logistics_settlements)
- [ShipmentConfirmation (shipment_confirmations)](#shipmentconfirmation-shipment_confirmations)
- [ChatbotQueryEvent (chatbot_query_events)](#chatbotqueryevent-chatbot_query_events)
- [PushNotificationToken (push_notification_tokens)](#pushnotificationtoken-push_notification_tokens)
- [ProductVerification (product_verifications)](#productverification-product_verifications)
- [ProcessedWebhookEvent (processed_webhook_events)](#processedwebhookevent-processed_webhook_events)
- [NormalizedWebhookEvent (normalized_webhook_events)](#normalizedwebhookevent-normalized_webhook_events)
- [EmployeeExpense (employee_expenses)](#employeeexpense-employee_expenses)
- [SupplierCountryCommission (supplier_country_commissions)](#suppliercountrycommission-supplier_country_commissions)
- [RetentionJobRun (retention_job_runs)](#retentionjobrun-retention_job_runs)
- [UserBrowsingHistory (user_browsing_histories)](#userbrowsinghistory-user_browsing_histories)
- [SystemHealthEvent (system_health_events)](#systemhealthevent-system_health_events)
- [LegalContractTemplate (legal_contract_templates)](#legalcontracttemplate-legal_contract_templates)
- [Office (offices)](#office-offices)
- [PhysicalIDCard (physical_id_cards)](#physicalidcard-physical_id_cards)
- [DynamicQRSession (dynamic_qr_sessions)](#dynamicqrsession-dynamic_qr_sessions)
- [EmployeeBiometric (employee_biometrics)](#employeebiometric-employee_biometrics)
- [GeoFenceLog (geo_fence_logs)](#geofencelog-geo_fence_logs)
- [EmployeeRole (employee_roles)](#employeerole-employee_roles)
- [OrgUnit (org_units)](#orgunit-org_units)
- [Employee (employees)](#employee-employees)
- [EmployeeAttendance (employee_attendances)](#employeeattendance-employee_attendances)
- [EmployeeWorkLog (employee_work_logs)](#employeeworklog-employee_work_logs)
- [EmployeeLeaveRequest (employee_leave_requests)](#employeeleaverequest-employee_leave_requests)
- [EmployeeLeaveLedger (employee_leave_ledgers)](#employeeleaveledger-employee_leave_ledgers)
- [EmployeeShiftRoster (employee_shift_rosters)](#employeeshiftroster-employee_shift_rosters)
- [EmployeeAsset (employee_assets)](#employeeasset-employee_assets)
- [EmployeeCertification (employee_certifications)](#employeecertification-employee_certifications)
- [EmployeeDocument (employee_documents)](#employeedocument-employee_documents)
- [EmployeeDependent (employee_dependents)](#employeedependent-employee_dependents)
- [EmployeeRelation (employee_relations)](#employeerelation-employee_relations)
- [EmployeeAddress (employee_addresses)](#employeeaddress-employee_addresses)
- [COIReport (coi_reports)](#coireport-coi_reports)
- [TravelRequest (employee_travel_requests)](#travelrequest-employee_travel_requests)
- [AlumniNetwork (alumni_networks)](#alumninetwork-alumni_networks)
- [DisciplinaryCase (disciplinary_cases)](#disciplinarycase-disciplinary_cases)
- [OffboardingCase (offboarding_cases)](#offboardingcase-offboarding_cases)
- [EmployeeRiskScore (employee_risk_scores)](#employeeriskscore-employee_risk_scores)
- [PayrollRecord (payroll_records)](#payrollrecord-payroll_records)
- [TrainingModule (training_modules)](#trainingmodule-training_modules)
- [EmployeeTraining (employee_trainings)](#employeetraining-employee_trainings)
- [EmployeeActivityLog (employee_activity_logs)](#employeeactivitylog-employee_activity_logs)
- [ShiftHandoverSession (shift_handover_sessions)](#shifthandoversession-shift_handover_sessions)
- [ShiftHandoverTask (shift_handover_tasks)](#shifthandovertask-shift_handover_tasks)
- [Warehouse (warehouses)](#warehouse-warehouses)
- [PurchaseOrder (purchase_orders)](#purchaseorder-purchase_orders)
- [PurchaseOrderLine (purchase_order_lines)](#purchaseorderline-purchase_order_lines)
- [GoodsReceiptNote (goods_receipt_notes)](#goodsreceiptnote-goods_receipt_notes)
- [GoodsReceiptLine (goods_receipt_lines)](#goodsreceiptline-goods_receipt_lines)
- [SalesOrder (sales_orders)](#salesorder-sales_orders)
- [SalesOrderLine (sales_order_lines)](#salesorderline-sales_order_lines)
- [StockMovement (stock_movements)](#stockmovement-stock_movements)
- [ImportShipment (import_shipments)](#importshipment-import_shipments)
- [ImportShipmentLine (import_shipment_lines)](#importshipmentline-import_shipment_lines)
- [LandedCostAllocation (landed_cost_allocations)](#landedcostallocation-landed_cost_allocations)
- [CustomsEntry (customs_entries)](#customsentry-customs_entries)
- [ImportCostTemplate (import_cost_templates)](#importcosttemplate-import_cost_templates)
- [LogisticsPartner (logistics_partners)](#logisticspartner-logistics_partners)
- [LogisticsPartnerProfile (logistics_partner_profiles)](#logisticspartnerprofile-logistics_partner_profiles)
- [LogisticsPartnerServiceArea (logistics_partner_service_areas)](#logisticspartnerservicearea-logistics_partner_service_areas)
- [LogisticsPricingProfile (logistics_pricing_profiles)](#logisticspricingprofile-logistics_pricing_profiles)
- [LogisticsVehicleRule (logistics_vehicle_rules)](#logisticsvehiclerule-logistics_vehicle_rules)
- [LogisticsCategoryPricingRule (logistics_category_pricing_rules)](#logisticscategorypricingrule-logistics_category_pricing_rules)
- [Shipment (shipments)](#shipment-shipments)
- [ShipmentEvent (shipment_events)](#shipmentevent-shipment_events)
- [CityDistanceMatrix (city_distance_matrices)](#citydistancematrix-city_distance_matrices)
- [ShippingRule (shipping_rules)](#shippingrule-shipping_rules)
- [Order (orders)](#order-orders)
- [OrderItem (order_items)](#orderitem-order_items)
- [OrderLogisticsAllocation (order_logistics_allocations)](#orderlogisticsallocation-order_logistics_allocations)
- [ReturnRequest (return_requests)](#returnrequest-return_requests)
- [OrderNotification (order_notifications)](#ordernotification-order_notifications)
- [PaymentMethod (payment_methods)](#paymentmethod-payment_methods)
- [PaymentAttempt (payment_attempts)](#paymentattempt-payment_attempts)
- [Refund (refunds)](#refund-refunds)
- [PaymentIntent (payment_intents)](#paymentintent-payment_intents)
- [CouponUsage (coupon_usages)](#couponusage-coupon_usages)
- [UserPoints (user_points)](#userpoints-user_points)
- [PointsTransaction (points_transactions)](#pointstransaction-points_transactions)
- [PromotionEngineConfig (promotion_engine_configs)](#promotionengineconfig-promotion_engine_configs)
- [PromotionLedgerEntry (promotion_ledger_entries)](#promotionledgerentry-promotion_ledger_entries)
- [Coupon (coupons)](#coupon-coupons)
- [Banner (banners)](#banner-banners)
- [BOGOPromotion (bogo_promotions)](#bogopromotion-bogo_promotions)
- [FlashSale (flash_sales)](#flashsale-flash_sales)
- [FraudEvent (fraud_events)](#fraudevent-fraud_events)
- [FraudBlacklist (fraud_blacklists)](#fraudblacklist-fraud_blacklists)
- [FraudRule (fraud_rules)](#fraudrule-fraud_rules)
- [ManualReviewQueue (manual_review_queues)](#manualreviewqueue-manual_review_queues)
- [IPReputation (ip_reputations)](#ipreputation-ip_reputations)
- [DeviceFingerprint (device_fingerprints)](#devicefingerprint-device_fingerprints)
- [CreditCardBin (credit_card_bins)](#creditcardbin-credit_card_bins)
- [ReturnAbusePattern (return_abuse_patterns)](#returnabusepattern-return_abuse_patterns)
- [LogisticsFraudIndicator (logistics_fraud_indicators)](#logisticsfraudindicator-logistics_fraud_indicators)
- [FraudAlert (fraud_alerts)](#fraudalert-fraud_alerts)
- [IPAccountLinkage (ip_account_linkages)](#ipaccountlinkage-ip_account_linkages)
- [VelocityCounter (fraud_velocity_counters)](#velocitycounter-fraud_velocity_counters)
- [FraudScoringLog (fraud_scoring_logs)](#fraudscoringlog-fraud_scoring_logs)
- [FraudCase (fraud_cases)](#fraudcase-fraud_cases)
- [FraudCaseAssignment (fraud_case_assignments)](#fraudcaseassignment-fraud_case_assignments)
- [DLPViolation (dlp_violations)](#dlpviolation-dlp_violations)
- [MeetingTranscript (meeting_transcripts)](#meetingtranscript-meeting_transcripts)
- [MeetingActionItem (meeting_action_items)](#meetingactionitem-meeting_action_items)
- [AlertEscalationRule (alert_escalation_rules)](#alertescalationrule-alert_escalation_rules)
- [DocumentVerification (document_verifications)](#documentverification-document_verifications)
- [KYCVerification (kyc_verifications)](#kycverification-kyc_verifications)
- [SupplierFraudIndicator (supplier_fraud_indicators)](#supplierfraudindicator-supplier_fraud_indicators)
- [SupplierBadgeCatalog (supplier_badge_catalogs)](#supplierbadgecatalog-supplier_badge_catalogs)
- [SupplierBadge (supplier_badges)](#supplierbadge-supplier_badges)
- [SupplierBadgeBillingHistory (supplier_badge_billing_histories)](#supplierbadgebillinghistory-supplier_badge_billing_histories)
- [SupplierDispute (supplier_disputes)](#supplierdispute-supplier_disputes)

### SupplierBankAccount (supplier_bank_accounts)

- **File**: `backend/domains\accounts\models\banking.py`
- **Schema**: accounts
- **Tablename**: `supplier_bank_accounts`
- **Columns**: id, supplier_id, account_number, bank_name, beneficiary_name, branch_name, iban, swift_code, routing_number, currency, bank_country, verification_status, verification_note, provider, provider_recipient_id, provider_status, provider_last_synced_at, verified_at, verified_by_id, is_active, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | supplier_bank_accounts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LogisticsPartnerBankAccount (logistics_partner_bank_accounts)

- **File**: `backend/domains\accounts\models\banking.py`
- **Schema**: accounts
- **Tablename**: `logistics_partner_bank_accounts`
- **Columns**: id, partner_id, account_number, bank_name, beneficiary_name, branch_name, iban, swift_code, routing_number, currency, bank_country, verification_status, verification_note, provider, provider_recipient_id, provider_status, provider_last_synced_at, verified_at, verified_by_id, is_active, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | logistics_partner_bank_accounts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Address (addresses)

- **File**: `backend/domains\accounts\models\core.py`
- **Schema**: accounts
- **Tablename**: `addresses`
- **Columns**: id, user_id, label, full_name, phone, address_line1, address_line2, city, state, postal_code, country, is_default, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | addresses |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Cart (carts)

- **File**: `backend/domains\accounts\models\core.py`
- **Schema**: accounts
- **Tablename**: `carts`
- **Columns**: id, user_id, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | carts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CartItem (cart_items)

- **File**: `backend/domains\accounts\models\core.py`
- **Schema**: accounts
- **Tablename**: `cart_items`
- **Columns**: id, user_id, product_id, quantity, selected_size, selected_color, variant_id, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | cart_items |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### MfaFactor (mfa_factors)

- **File**: `backend/domains\accounts\models\mfa_factor.py`
- **Schema**: accounts
- **Tablename**: `mfa_factors`
- **Columns**: id, user_id, factor_type, secret, enabled, created_at, last_used_at, backup_codes, country_code, updated_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | mfa_factors |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### OnboardingPipeline (onboarding_pipelines)

- **File**: `backend/domains\accounts\models\onboarding.py`
- **Schema**: accounts
- **Tablename**: `onboarding_pipelines`
- **Columns**: id, user_id, pipeline_type, pipeline_status, current_step, steps_data, started_at, completed_at, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | onboarding_pipelines |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### OnboardingStep (onboarding_steps)

- **File**: `backend/domains\accounts\models\onboarding.py`
- **Schema**: accounts
- **Tablename**: `onboarding_steps`
- **Columns**: id, pipeline_id, step_name, step_status, data, started_at, completed_at, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | onboarding_steps |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### OCRResult (ocr_results)

- **File**: `backend/domains\accounts\models\onboarding.py`
- **Schema**: accounts
- **Tablename**: `ocr_results`
- **Columns**: id, document_verification_id, extracted_text, confidence_score, fields, processed_at, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | ocr_results |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### OtpCode (otp_codes)

- **File**: `backend/domains\accounts\models\otp.py`
- **Schema**: accounts
- **Tablename**: `otp_codes`
- **Columns**: id, user_id, purpose, channel, destination, code_hash, expires_at, attempts, verified, country_code, created_at, updated_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | otp_codes |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PasswordHistory (password_histories)

- **File**: `backend/domains\accounts\models\password_history.py`
- **Schema**: accounts
- **Tablename**: `password_histories`
- **Columns**: id, user_id, password_hash, created_at, country_code, updated_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | password_histories |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### RefreshTokenFamily (refresh_token_families)

- **File**: `backend/domains\accounts\models\refresh_token_family.py`
- **Schema**: accounts
- **Tablename**: `refresh_token_families`
- **Columns**: id, user_id, family_id, created_at, updated_at, revoked_at, reused_at, ip_address, user_agent, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | refresh_token_families |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SocialIdentity (social_identities)

- **File**: `backend/domains\accounts\models\social.py`
- **Schema**: accounts
- **Tablename**: `social_identities`
- **Columns**: id, user_id, provider, provider_user_id, email, full_name, raw_data, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | social_identities |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### User (users)

- **File**: `backend/domains\accounts\models\user.py`
- **Schema**: accounts
- **Tablename**: `users`
- **Columns**: id, email, hashed_password, full_name, role, country_code, is_active, email_verified, staff_country_codes, referred_by_user_id, created_at, updated_at, is_deleted, profile_image
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | users |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### UserSession (user_sessions)

- **File**: `backend/domains\accounts\models\user.py`
- **Schema**: accounts
- **Tablename**: `user_sessions`
- **Columns**: id, user_id, token_jti, refresh_token_jti, ip_address, user_agent, device_fingerprint, is_active, expires_at, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | user_sessions |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### UserLoginHistory (user_login_histories)

- **File**: `backend/domains\accounts\models\user.py`
- **Schema**: accounts
- **Tablename**: `user_login_histories`
- **Columns**: id, user_id, ip_address, user_agent, success, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | user_login_histories |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### UserDevice (user_devices)

- **File**: `backend/domains\accounts\models\user.py`
- **Schema**: accounts
- **Tablename**: `user_devices`
- **Columns**: id, user_id, device_fingerprint, fingerprint_hash, device_id, is_active, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | user_devices |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PasswordResetToken (password_reset_tokens)

- **File**: `backend/domains\accounts\models\user.py`
- **Schema**: accounts
- **Tablename**: `password_reset_tokens`
- **Columns**: id, user_id, token, expires_at, is_used, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | password_reset_tokens |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmailVerificationToken (email_verification_tokens)

- **File**: `backend/domains\accounts\models\user.py`
- **Schema**: accounts
- **Tablename**: `email_verification_tokens`
- **Columns**: id, user_id, token, expires_at, is_used, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | email_verification_tokens |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### RevokedToken (revoked_tokens)

- **File**: `backend/domains\accounts\models\user.py`
- **Schema**: accounts
- **Tablename**: `revoked_tokens`
- **Columns**: id, user_id, token, expires_at, revoked_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 19: Missing required column: created_at

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | revoked_tokens |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | FAIL | MISSING |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### UserConsent (user_consents)

- **File**: `backend/domains\accounts\models\user_consent.py`
- **Schema**: accounts
- **Tablename**: `user_consents`
- **Columns**: id, user_id, consent_type, granted, granted_at, revoked_at, ip_address, user_agent, consent_version, country_code, created_at, updated_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | user_consents |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### UserPreference (user_preferences)

- **File**: `backend/domains\accounts\models\user_preference.py`
- **Schema**: accounts
- **Tablename**: `user_preferences`
- **Columns**: id, user_id, key, value, updated_at, country_code, created_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | accounts |
| Law 9: Naming (snake_case, plural) | PASS | user_preferences |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ExecutiveNews (executive_news)

- **File**: `backend/domains\analytics\models\analytics_schema_models.py`
- **Schema**: analytics
- **Tablename**: `executive_news`
- **Columns**: id, title, summary, content, url, category, priority, is_published, ai_sentiment, published_at, is_deleted, country_code, created_at, updated_at, uuid, version, created_by_id, updated_by_id, deleted_at, deleted_by_id
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | analytics |
| Law 9: Naming (snake_case, plural) | PASS | executive_news |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PredictiveSimulation (predictive_simulations)

- **File**: `backend/domains\analytics\models\analytics_schema_models.py`
- **Schema**: analytics
- **Tablename**: `predictive_simulations`
- **Columns**: id, simulation_type, parameters_json, result_json, is_deleted, country_code, created_at, updated_at, uuid, version, created_by_id, updated_by_id, deleted_at, deleted_by_id
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | analytics |
| Law 9: Naming (snake_case, plural) | PASS | predictive_simulations |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### AuditLog (audit_logs)

- **File**: `backend/domains\audit\models\audit_schema_models.py`
- **Schema**: audit
- **Tablename**: `audit_logs`
- **Columns**: id, action, entity_type, entity_id, user_id, username, user_role, details, ip_address, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 22: FK column country_code missing ondelete

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | audit |
| Law 9: Naming (snake_case, plural) | PASS | audit_logs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | FAIL | Missing ondelete on FK |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CommandCenterView (command_center_views)

- **File**: `backend/domains\audit\models\audit_schema_models.py`
- **Schema**: audit
- **Tablename**: `command_center_views`
- **Columns**: id, user_id, view_name, config, is_default, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 22: FK column country_code missing ondelete

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | audit |
| Law 9: Naming (snake_case, plural) | PASS | command_center_views |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | FAIL | Missing ondelete on FK |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### AIUploadJob (ai_upload_jobs)

- **File**: `backend/domains\catalog\models\ai_upload.py`
- **Schema**: catalog
- **Tablename**: `ai_upload_jobs`
- **Columns**: id, supplier_id, status, model_used, prompt_hash, tokens_used, source_media_json, created_product_id, error_log, country_code, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | ai_upload_jobs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### AIStagingProduct (ai_staging_products)

- **File**: `backend/domains\catalog\models\ai_upload.py`
- **Schema**: catalog
- **Tablename**: `ai_staging_products`
- **Columns**: id, job_id, product_id, name, description, price, stock, category, subcategory, color, brand, tags, sizes, materials, image_url, additional_media, ai_description, variant_axes, attributes, confidence_score, requires_human_review, country_code, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | ai_staging_products |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### AIStagingVariant (ai_staging_variants)

- **File**: `backend/domains\catalog\models\ai_upload.py`
- **Schema**: catalog
- **Tablename**: `ai_staging_variants`
- **Columns**: id, job_id, staging_product_id, variant_key, size, color, material, pattern, gender, sku, barcode, product_code, price, stock, media_url, attributes_json, is_active, confidence_score, requires_human_review, country_code, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | ai_staging_variants |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### AIGenerationLog (ai_generation_logs)

- **File**: `backend/domains\catalog\models\ai_upload.py`
- **Schema**: catalog
- **Tablename**: `ai_generation_logs`
- **Columns**: id, job_id, field, model_used, prompt_hash, tokens_used, cost, confidence, country_code, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | ai_generation_logs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ChartOfCategory (chart_of_categories)

- **File**: `backend/domains\catalog\models\chart_of_categories.py`
- **Schema**: catalog
- **Tablename**: `chart_of_categories`
- **Columns**: id, parent_id, name, slug, level, description, icon, sort_order, is_active, is_deleted, country_code, commission_group_id, path, depth, created_at, updated_at, version
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | chart_of_categories |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ProductType (product_types)

- **File**: `backend/domains\catalog\models\chart_of_categories.py`
- **Schema**: catalog
- **Tablename**: `product_types`
- **Columns**: id, coc_category_id, name, slug, description, icon, sort_order, is_active, country_code, is_deleted, attribute_schema, created_at, updated_at, version
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | product_types |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CategoryAttribute (category_attributes)

- **File**: `backend/domains\catalog\models\chart_of_categories.py`
- **Schema**: catalog
- **Tablename**: `category_attributes`
- **Columns**: id, product_type_id, name, key, layer, value_type, options, is_required, is_filterable, is_active, sort_order, country_code, is_deleted, created_at, updated_at, version
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | category_attributes |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CategoryAttributeValue (category_attribute_values)

- **File**: `backend/domains\catalog\models\chart_of_categories.py`
- **Schema**: catalog
- **Tablename**: `category_attribute_values`
- **Columns**: id, attribute_id, value, label, sort_order, is_active, country_code, is_deleted, created_at, updated_at, version
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | category_attribute_values |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CommissionGroup (commission_groups)

- **File**: `backend/domains\catalog\models\commission.py`
- **Schema**: catalog
- **Tablename**: `commission_groups`
- **Columns**: id, name, slug, description, base_rate, max_commission_amount, is_active, country_code, is_deleted, created_at, updated_at, version
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | commission_groups |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CommissionProfile (commission_profiles)

- **File**: `backend/domains\catalog\models\commission.py`
- **Schema**: catalog
- **Tablename**: `commission_profiles`
- **Columns**: id, supplier_id, name, slug, description, is_default, is_active, country_code, is_deleted, created_at, updated_at, version
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | commission_profiles |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CommissionRule (commission_rules)

- **File**: `backend/domains\catalog\models\commission.py`
- **Schema**: catalog
- **Tablename**: `commission_rules`
- **Columns**: id, profile_id, commission_group_id, name, coc_node_id, product_type_id, brand, attribute_key, attribute_value, rate, max_commission_amount, priority, effective_from, effective_to, is_active, country_code, is_deleted, created_at, updated_at, version
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | commission_rules |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CommissionTransaction (commission_transactions)

- **File**: `backend/domains\catalog\models\commission.py`
- **Schema**: catalog
- **Tablename**: `commission_transactions`
- **Columns**: id, order_id, supplier_id, product_id, gross_amount, commission_rate, commission_amount, net_amount, rule_id, rule_name, coc_path, country_code, is_deleted, created_at, updated_at, calculated_at, version
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | commission_transactions |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Category (categories)

- **File**: `backend/domains\catalog\models\products.py`
- **Schema**: catalog
- **Tablename**: `categories`
- **Columns**: id, name, slug, description, parent_id, icon, image_url, is_active, is_featured, sort_order, commission_rate, meta_title, meta_description, created_at, updated_at, country_code, is_deleted, path, depth
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | categories |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Product (products)

- **File**: `backend/domains\catalog\models\products.py`
- **Schema**: catalog
- **Tablename**: `products`
- **Columns**: id, name, slug, description, short_description, ai_description, sku, barcode, price, compare_price, cost_price, stock, low_stock_threshold, weight, dimensions, materials, image_url, images, category, category_id, tags, attributes, supplier_id, country_code, is_active, is_featured, is_digital, is_verified, moderation_status, brand, color, sizes, rating, sales_count, meta_title, meta_description, is_approved, is_deleted, discount_starts_at, discount_ends_at, created_at, updated_at, filter_attributes, search_vector, video_count, variant_axes, bg_preset, visibility_regions, slug_hash, subcategory, return_window_days, is_new
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | products |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Review (reviews)

- **File**: `backend/domains\catalog\models\products.py`
- **Schema**: catalog
- **Tablename**: `reviews`
- **Columns**: id, product_id, user_id, rating, title, comment, image_url, is_approved, is_deleted, is_verified_purchase, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | reviews |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### WishlistItem (wishlist_items)

- **File**: `backend/domains\catalog\models\products.py`
- **Schema**: catalog
- **Tablename**: `wishlist_items`
- **Columns**: id, user_id, product_id, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | wishlist_items |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Wishlist (wishlists)

- **File**: `backend/domains\catalog\models\products.py`
- **Schema**: catalog
- **Tablename**: `wishlists`
- **Columns**: id, user_id, product_id, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | wishlists |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ProductVariant (product_variants)

- **File**: `backend/domains\catalog\models\products.py`
- **Schema**: catalog
- **Tablename**: `product_variants`
- **Columns**: id, product_id, sku, title, size, color, material, pattern, gender, barcode, product_code, price, stock, media_url, attributes_json, is_active, sort_order, is_deleted, created_at, updated_at, country_code, variant_key
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | product_variants |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ProductVideo (product_videos)

- **File**: `backend/domains\catalog\models\products.py`
- **Schema**: catalog
- **Tablename**: `product_videos`
- **Columns**: id, product_id, video_url, thumbnail_url, duration_seconds, video_type, title, description, views_count, is_featured, upload_status, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | product_videos |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### VideoAnalytics (video_analytics)

- **File**: `backend/domains\catalog\models\products.py`
- **Schema**: catalog
- **Tablename**: `video_analytics`
- **Columns**: id, video_id, user_id, event_type, watch_duration_seconds, device_type, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | video_analytics |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ProductFilterMetadata (product_filter_metadatas)

- **File**: `backend/domains\catalog\models\products.py`
- **Schema**: catalog
- **Tablename**: `product_filter_metadatas`
- **Columns**: id, category_id, filter_name, filter_type, display_order, is_active, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | product_filter_metadatas |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ProductFilterOption (product_filter_options)

- **File**: `backend/domains\catalog\models\products.py`
- **Schema**: catalog
- **Tablename**: `product_filter_options`
- **Columns**: id, filter_metadata_id, option_value, option_display_name, product_count, sort_order, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | product_filter_options |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### UploadJob (upload_jobs)

- **File**: `backend/domains\catalog\models\upload_job.py`
- **Schema**: catalog
- **Tablename**: `upload_jobs`
- **Columns**: uuid, version, is_deleted, deleted_at, id, filename, stored_path, content_type, file_size, status, progress, error_log, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | catalog |
| Law 9: Naming (snake_case, plural) | PASS | upload_jobs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EntityChatThread (entity_chat_threads)

- **File**: `backend/domains\comms\models\chat.py`
- **Schema**: comms
- **Tablename**: `entity_chat_threads`
- **Columns**: id, entity_type, entity_id, title, is_active, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | entity_chat_threads |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### VideoRoom (video_rooms)

- **File**: `backend/domains\comms\models\chat.py`
- **Schema**: comms
- **Tablename**: `video_rooms`
- **Columns**: id, room_id, room_uuid, name, country_code, created_by_id, is_boardroom, status, max_participants, recording_enabled, watermark_enabled, transcription_enabled, started_at, ended_at, created_at, updated_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | video_rooms |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### VideoRoomParticipant (video_room_participants)

- **File**: `backend/domains\comms\models\chat.py`
- **Schema**: comms
- **Tablename**: `video_room_participants`
- **Columns**: id, room_id, user_id, role, joined_at, left_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 19: Missing required column: created_at; Law 20: Missing required column: updated_at; Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | video_room_participants |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | FAIL | MISSING |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### DirectChatRoom (direct_chat_rooms)

- **File**: `backend/domains\comms\models\chat.py`
- **Schema**: comms
- **Tablename**: `direct_chat_rooms`
- **Columns**: id, chat_id, participant_one_id, participant_two_id, country_code, is_masked, is_active, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | direct_chat_rooms |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### GroupChatMember (group_chat_members)

- **File**: `backend/domains\comms\models\chat.py`
- **Schema**: comms
- **Tablename**: `group_chat_members`
- **Columns**: id, room_id, user_id, role, joined_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 19: Missing required column: created_at; Law 20: Missing required column: updated_at; Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | group_chat_members |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | FAIL | MISSING |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### EscalationSLALog (escalation_sla_logs)

- **File**: `backend/domains\comms\models\chat.py`
- **Schema**: comms
- **Tablename**: `escalation_sla_logs`
- **Columns**: id, message_id, message_type, original_recipient_id, escalated_to_user_id, escalated_to_role, priority, elapsed_minutes, status, escalated_at, acknowledged_at, is_deleted, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 20: Missing required column: updated_at; Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | escalation_sla_logs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### EntityChatMessage (entity_chat_messages)

- **File**: `backend/domains\comms\models\chat.py`
- **Schema**: comms
- **Tablename**: `entity_chat_messages`
- **Columns**: id, thread_id, sender_id, message, message_type, read_at, is_deleted, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 20: Missing required column: updated_at; Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | entity_chat_messages |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### VideoRoomRecording (video_room_recordings)

- **File**: `backend/domains\comms\models\chat.py`
- **Schema**: comms
- **Tablename**: `video_room_recordings`
- **Columns**: id, room_id, started_by_id, recording_url, duration_seconds, status, started_at, ended_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 19: Missing required column: created_at; Law 20: Missing required column: updated_at; Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | video_room_recordings |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | FAIL | MISSING |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### DirectChatMessage (direct_chat_messages)

- **File**: `backend/domains\comms\models\chat.py`
- **Schema**: comms
- **Tablename**: `direct_chat_messages`
- **Columns**: id, room_id, sender_id, message, message_type, read_at, is_deleted, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 20: Missing required column: updated_at; Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | direct_chat_messages |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### GroupChatRoom (group_chat_rooms)

- **File**: `backend/domains\comms\models\chat.py`
- **Schema**: comms
- **Tablename**: `group_chat_rooms`
- **Columns**: id, chat_id, name, country_code, is_encrypted, is_active, created_by_id, created_at, updated_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | group_chat_rooms |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### GroupChatMessage (group_chat_messages)

- **File**: `backend/domains\comms\models\chat.py`
- **Schema**: comms
- **Tablename**: `group_chat_messages`
- **Columns**: id, room_id, sender_id, message, message_type, read_at, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | group_chat_messages |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### Announcement (announcements)

- **File**: `backend/domains\comms\models\communication.py`
- **Schema**: comms
- **Tablename**: `announcements`
- **Columns**: uuid, version, is_deleted, deleted_at, id, title, content, is_active, starts_at, ends_at, created_at, updated_at, uuid, version, updated_at, is_deleted, deleted_at, id, question, answer, category, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now(); Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | announcements |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### HelpCategory (help_categories)

- **File**: `backend/domains\comms\models\communication.py`
- **Schema**: comms
- **Tablename**: `help_categories`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, name, description, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | help_categories |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### ProxyChannel (proxy_channels)

- **File**: `backend/domains\comms\models\communication.py`
- **Schema**: comms
- **Tablename**: `proxy_channels`
- **Columns**: uuid, version, created_at, is_deleted, deleted_at, id, entity_type, entity_id, proxy_phone, proxy_email, participants, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | proxy_channels |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### ProxySession (proxy_sessions)

- **File**: `backend/domains\comms\models\communication.py`
- **Schema**: comms
- **Tablename**: `proxy_sessions`
- **Columns**: uuid, version, created_at, updated_at, is_deleted, deleted_at, id, channel_id, participant_one_id, participant_two_id, started_at, ended_at, is_encrypted, session_metadata
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | proxy_sessions |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### ProxyMessage (proxy_messages)

- **File**: `backend/domains\comms\models\communication.py`
- **Schema**: comms
- **Tablename**: `proxy_messages`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, session_id, sender_id, recipient_id, message_type, content, is_masked, read_at, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | proxy_messages |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### ProxyCallLog (proxy_call_logs)

- **File**: `backend/domains\comms\models\communication.py`
- **Schema**: comms
- **Tablename**: `proxy_call_logs`
- **Columns**: uuid, version, created_at, updated_at, is_deleted, deleted_at, id, channel_id, caller_id, callee_id, direction, duration_seconds, call_recording_url, is_recorded, started_at, ended_at, uuid, version, updated_at, is_deleted, deleted_at, id, entity_id, entity_type, participants, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | proxy_call_logs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ExternalContactMasking (external_contact_maskings)

- **File**: `backend/domains\comms\models\communication.py`
- **Schema**: comms
- **Tablename**: `external_contact_maskings`
- **Columns**: uuid, version, created_at, updated_at, is_deleted, deleted_at, id, user_id, external_contact_type, external_contact_id, masked_phone, masked_email
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | external_contact_maskings |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### CommunicationAuditTrail (communication_audit_trails)

- **File**: `backend/domains\comms\models\communication.py`
- **Schema**: comms
- **Tablename**: `communication_audit_trails`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, entity_type, entity_id, user_id, action, channel, content_preview, metadata_json, created_at, uuid, version, created_at, updated_at, is_deleted, deleted_at, id, entity_type, entity_id, name, channel_id, description, is_public, country_code, allowed_roles
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | communication_audit_trails |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### InternalChannelMember (internal_channel_members)

- **File**: `backend/domains\comms\models\communication.py`
- **Schema**: comms
- **Tablename**: `internal_channel_members`
- **Columns**: uuid, version, created_at, updated_at, is_deleted, deleted_at, id, channel_id, user_id, role, joined_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | internal_channel_members |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### InternalMessage (internal_messages)

- **File**: `backend/domains\comms\models\communication.py`
- **Schema**: comms
- **Tablename**: `internal_messages`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, channel_id, user_id, message, message_type, is_masked, read_at, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | internal_messages |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### ChatReadReceipt (chat_read_receipts)

- **File**: `backend/domains\comms\models\communication.py`
- **Schema**: comms
- **Tablename**: `chat_read_receipts`
- **Columns**: uuid, version, created_at, updated_at, is_deleted, deleted_at, id, message_id, message_type, employee_id, read_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | chat_read_receipts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### ChatAttachment (chat_attachments)

- **File**: `backend/domains\comms\models\communication.py`
- **Schema**: comms
- **Tablename**: `chat_attachments`
- **Columns**: uuid, version, created_at, updated_at, is_deleted, deleted_at, id, message_id, message_type, attachment_type, file_url, file_name, file_size_bytes, mime_type, thumbnail_url, duration_seconds, waveform_json, is_processed, uuid, version, is_deleted, deleted_at, id, sender_id, subject, body_html, body_text, recipients, thread_id, is_external, external_message_id, in_reply_to_id, folder_id, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | chat_attachments |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### EmailFolder (email_folders)

- **File**: `backend/domains\comms\models\communication.py`
- **Schema**: comms
- **Tablename**: `email_folders`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, employee_id, name, folder_type, sort_order, is_system, created_at, uuid, version, updated_at, is_deleted, deleted_at, id, sender_id, recipient_ref, message_hash, content, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | email_folders |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### SupportTicket (support_tickets)

- **File**: `backend/domains\comms\models\communication_schema_models.py`
- **Schema**: comms
- **Tablename**: `support_tickets`
- **Columns**: id, is_deleted, user_id, subject, priority, status, created_at, updated_at, country_code
- **Status**: RESOLVED
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | support_tickets |
| Law 19: Timestamps server_default | PASS | server_default present |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SupportTicketReply (support_ticket_replies)

- **File**: `backend/domains\comms\models\communication_schema_models.py`
- **Schema**: comms
- **Tablename**: `support_ticket_replies`
- **Columns**: id, ticket_id, sender_id, message, created_at, updated_at, is_deleted, country_code
- **Status**: RESOLVED
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | support_ticket_replies |
| Law 19: Timestamps server_default | PASS | server_default present |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### TicketAttachment (ticket_attachments)

- **File**: `backend/domains\comms\models\communication_schema_models.py`
- **Schema**: comms
- **Tablename**: `ticket_attachments`
- **Columns**: id, ticket_reply_id, ticket_id, file_url, created_at, updated_at, country_code, is_deleted
- **Status**: RESOLVED
- **Project Completion Blocker**: no
- **Issues**: Law 22: Missing required column: is_deleted; Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | ticket_attachments |
| Law 19: Timestamps server_default | PASS | server_default present |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### NewsSource (news_sources)

- **File**: `backend/domains\comms\models\communication_schema_models.py`
- **Schema**: comms
- **Tablename**: `news_sources`
- **Columns**: id, name, url, source_type, api_key_required, category, is_active, created_at, updated_at, is_deleted, country_code
- **Status**: RESOLVED
- **Project Completion Blocker**: no
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | news_sources |
| Law 19: Timestamps server_default | PASS | server_default present |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### InternalNotice (internal_notices)

- **File**: `backend/domains\comms\models\communication_schema_models.py`
- **Schema**: comms
- **Tablename**: `internal_notices`
- **Columns**: id, title, content, priority, is_active, valid_from, valid_to, created_at, updated_at, is_deleted, country_code
- **Status**: RESOLVED
- **Project Completion Blocker**: no
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | internal_notices |
| Law 19: Timestamps server_default | PASS | server_default present |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EscalationSLARule (escalation_sla_rules)

- **File**: `backend/domains\comms\models\communication_schema_models.py`
- **Schema**: comms
- **Tablename**: `escalation_sla_rules`
- **Columns**: id, country_code, priority, escalate_after_minutes, escalate_to_role, notify_via, is_active, created_at, updated_at, is_deleted
- **Status**: RESOLVED
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | escalation_sla_rules |
| Law 19: Timestamps server_default | PASS | server_default present |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### MeetingRecording (meeting_recordings)

- **File**: `backend/domains\comms\models\fraud.py`
- **Schema**: comms
- **Tablename**: `meeting_recordings`
- **Columns**: id, is_deleted, room_id, started_by_id, recording_url, duration_seconds, status_code, started_at, ended_at, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | meeting_recordings |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### IncidentWarRoom (incident_war_rooms)

- **File**: `backend/domains\comms\models\incident.py`
- **Schema**: comms
- **Tablename**: `incident_war_rooms`
- **Columns**: id, incident_id, title, severity, status, created_by_id, started_at, resolved_at, closed_at, context_data, is_deleted, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 19: Missing required column: created_at; Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | incident_war_rooms |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | FAIL | MISSING |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### IncidentThread (incident_threads)

- **File**: `backend/domains\comms\models\incident.py`
- **Schema**: comms
- **Tablename**: `incident_threads`
- **Columns**: id, war_room_id, participant_id, message, created_at, updated_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | incident_threads |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### IncidentActionItem (incident_action_items)

- **File**: `backend/domains\comms\models\incident.py`
- **Schema**: comms
- **Tablename**: `incident_action_items`
- **Columns**: id, war_room_id, assignee_id, title, description, status, priority, due_date, created_at, completed_at, updated_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | incident_action_items |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### WarRoomTemplate (war_room_templates)

- **File**: `backend/domains\comms\models\incident.py`
- **Schema**: comms
- **Tablename**: `war_room_templates`
- **Columns**: id, name, severity, auto_assign, template_data, is_deleted, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 20: Missing required column: updated_at; Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | war_room_templates |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### EmailTemplate (email_templates)

- **File**: `backend/domains\comms\models\marketing.py`
- **Schema**: comms
- **Tablename**: `email_templates`
- **Columns**: uuid, version, is_deleted, deleted_at, id, name, subject, content, template_type, is_active, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | email_templates |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### NewsletterSubscriber (newsletter_subscribers)

- **File**: `backend/domains\comms\models\marketing.py`
- **Schema**: comms
- **Tablename**: `newsletter_subscribers`
- **Columns**: uuid, version, is_deleted, deleted_at, id, email, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | newsletter_subscribers |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### EmailCampaignLog (email_campaign_logs)

- **File**: `backend/domains\comms\models\marketing.py`
- **Schema**: comms
- **Tablename**: `email_campaign_logs`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, campaign_id, recipient_email, status_code, sent_at, delivered_at, opened_at, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | email_campaign_logs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### CampaignRecipient (campaign_recipients)

- **File**: `backend/domains\comms\models\marketing.py`
- **Schema**: comms
- **Tablename**: `campaign_recipients`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, campaign_id, user_id, email, status_code, sent_at, delivered_at, opened_at, clicked_at, bounced_at, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | campaign_recipients |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### EmailDeliveryEvent (email_delivery_events)

- **File**: `backend/domains\comms\models\marketing.py`
- **Schema**: comms
- **Tablename**: `email_delivery_events`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, event_type, recipient_email, subject, status_code, details, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | email_delivery_events |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### EmailSuppression (email_suppressions)

- **File**: `backend/domains\comms\models\marketing.py`
- **Schema**: comms
- **Tablename**: `email_suppressions`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, email, reason, source, provider, status_code, notes, suppressed_at, last_event_at, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | email_suppressions |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### EmailRuntimeConfig (email_runtime_configs)

- **File**: `backend/domains\comms\models\marketing.py`
- **Schema**: comms
- **Tablename**: `email_runtime_configs`
- **Columns**: uuid, version, created_at, is_deleted, deleted_at, id, provider, resend_api_key, resend_webhook_secret, smtp_host, smtp_port, smtp_username, smtp_password, is_smtp_use_tls, is_smtp_use_ssl, smtp_timeout_seconds, email_from_default, email_from_promotional, email_from_transactional, email_from_notification, email_from_alert, email_from_verification, email_from_login_verification, email_from_password_reset, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | email_runtime_configs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### Message (messages)

- **File**: `backend/domains\comms\models\message.py`
- **Schema**: comms
- **Tablename**: `messages`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, from_user_id, to_user_id, subject, body, entity_type, entity_id, priority, category, status, read_at, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | messages |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### NewsArticle (news_articles)

- **File**: `backend/domains\comms\models\news.py`
- **Schema**: comms
- **Tablename**: `news_articles`
- **Columns**: id, is_deleted, source_id, external_id, content_hash, title, summary, content, url, image_url, published_at, country_code, ai_sentiment, ai_tags, is_published, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | comms |
| Law 9: Naming (snake_case, plural) | PASS | news_articles |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryConfig (country_configs)

- **File**: `backend/domains\country\models\countries.py`
- **Schema**: country
- **Tablename**: `country_configs`
- **Columns**: uuid, version, deleted_at, id, basics_id, code, name, currency, currency_symbol, phone_code, language, timezone, date_format, status, is_active, is_deleted, is_default, created_at, updated_at, official_name, alpha3, flag_url, currency_name, exchange_rate_to_usd, capital, region, subregion, population, internet_penetration_pct, gdp_per_capita_usd, urbanization_pct, mobile_subs_per_100, public_holidays_json, macro_indicators_json, tax_type, tax_rate, tax_name, tax_inclusive, tax_exempt_categories_json, tax_reduced_rates_json, logistics_model, default_vehicle_type, base_rate, per_km_rate, minimum_charge, weight_surcharge_rate, weight_surcharge_threshold_kg, payment_methods_json, payment_gateways_json, logistics_providers_json, legal_rules_json, product_restrictions_json, address_format_json, regions_json, supplier_requirements_json, payout_settings_json, commission_tiers_json, suggested_gateway_rankings_json, suggested_commission_ranges_json, consumer_behavior_profile_json, economic_tier, fraud_risk_tier, suggested_logistics_model, data_residency_tier, data_residency_encrypted, confidence_score, audit_trail_json, cod_enabled, cod_max_amount, cod_verification_required, cod_remittance_days, settlement_hold_days, minimum_payout_amount, payout_currency, supplier_kyc_tier, supplier_onboarding_fee, supplier_monthly_fee, supplier_rating_threshold, legal_entity_required, consumer_protection_days, data_privacy_framework, max_package_weight_kg, max_package_dimensions_cm, signature_required_threshold, measurement_system, working_days_json, supported_languages_json, payout_methods_json, logistics_zones_json, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_configs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryCommunication (country_communications)

- **File**: `backend/domains\country\models\countries.py`
- **Schema**: country
- **Tablename**: `country_communications`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, from_user_id, to_user_id, subject, body, priority, category, status, related_entity_type, related_entity_id, read_at, attachments_json, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_communications |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryGatewayCredentials (country_gateway_credentials)

- **File**: `backend/domains\country\models\countries.py`
- **Schema**: country
- **Tablename**: `country_gateway_credentials`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, gateway_name, environment, credentials, is_active, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_gateway_credentials |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryBasics (country_basics)

- **File**: `backend/domains\country\models\country_basics.py`
- **Schema**: country
- **Tablename**: `country_basics`
- **Columns**: uuid, version, deleted_at, id, code, name, currency, currency_symbol, phone_code, language, timezone, date_format, status, is_active, is_deleted, is_default, created_at, updated_at, country_code, official_name, alpha3, flag_url, currency_name, exchange_rate_to_usd, capital, region, subregion, population, internet_penetration_pct, gdp_per_capita_usd, urbanization_pct, mobile_subs_per_100, public_holidays_json, macro_indicators_json
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now(); Law 22: FK column country_code missing ondelete

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_basics |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | FAIL | Missing ondelete on FK |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ShiftHandoverLog (shift_handover_logs)

- **File**: `backend/domains\country\models\country_control.py`
- **Schema**: country
- **Tablename**: `shift_handover_logs`
- **Columns**: id, user_id, country_code, shift_start, shift_end, notes, handover_to_user_id, handover_notes, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | shift_handover_logs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PaymentOrchestratorSync (payment_orchestrator_syncs)

- **File**: `backend/domains\country\models\country_control.py`
- **Schema**: country
- **Tablename**: `payment_orchestrator_syncs`
- **Columns**: id, country_code, gateway_id, gateway_name, environment, is_active, fee_percent, fee_fixed, supported_payment_methods, last_sync_at, status, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | payment_orchestrator_syncs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SupplierOnboardingSync (supplier_onboarding_syncs)

- **File**: `backend/domains\country\models\country_control.py`
- **Schema**: country
- **Tablename**: `supplier_onboarding_syncs`
- **Columns**: id, country_code, supplier_id, kyc_status, kyc_documents, onboarding_fee_paid, monthly_fee_status, status, notes, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | supplier_onboarding_syncs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### DataResidencyRecord (data_residency_records)

- **File**: `backend/domains\country\models\country_control.py`
- **Schema**: country
- **Tablename**: `data_residency_records`
- **Columns**: id, country_code, data_type, storage_location, cross_border_allowed, compliance_status, last_audit_at, next_audit_at, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | data_residency_records |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryMapConfig (country_map_configs)

- **File**: `backend/domains\country\models\country_control.py`
- **Schema**: country
- **Tablename**: `country_map_configs`
- **Columns**: id, country_code, map_provider, api_key_ref, default_zoom, show_regions, show_cities, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_map_configs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ShopWarehouseLocation (shop_warehouse_locations)

- **File**: `backend/domains\country\models\country_control.py`
- **Schema**: country
- **Tablename**: `shop_warehouse_locations`
- **Columns**: id, country_code, name, warehouse_code, latitude, longitude, address, is_active, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | shop_warehouse_locations |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LogisticsPartnerLocation (logistics_partner_locations)

- **File**: `backend/domains\country\models\country_control.py`
- **Schema**: country
- **Tablename**: `logistics_partner_locations`
- **Columns**: id, partner_id, country_code, location_type, latitude, longitude, address, is_active, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | logistics_partner_locations |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ParcelLocationTracker (parcel_location_trackers)

- **File**: `backend/domains\country\models\country_control.py`
- **Schema**: country
- **Tablename**: `parcel_location_trackers`
- **Columns**: id, parcel_id, country_code, latitude, longitude, location_name, timestamp, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | parcel_location_trackers |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryEconomics (country_economics)

- **File**: `backend/domains\country\models\country_economics.py`
- **Schema**: country
- **Tablename**: `country_economics`
- **Columns**: deleted_at, id, uuid, version, country_code, is_active, is_deleted, created_at, updated_at, economic_tier, fraud_risk_tier, suggested_logistics_model, data_residency_tier, data_residency_encrypted, confidence_score, audit_trail_json, cod_enabled, cod_max_amount, cod_verification_required, cod_remittance_days, settlement_hold_days, minimum_payout_amount, payout_currency, supplier_kyc_tier, supplier_onboarding_fee, supplier_monthly_fee, supplier_rating_threshold, legal_entity_required, consumer_protection_days, data_privacy_framework, max_package_weight_kg, max_package_dimensions_cm, signature_required_threshold, measurement_system, working_days_json, supported_languages_json, payout_methods_json, logistics_zones_json
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_economics |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryFeatureFlag (country_feature_flags)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_feature_flags`
- **Columns**: uuid, version, is_deleted, deleted_at, id, country_code, feature_key, feature_name, is_enabled, config, rollout_audience, rollout_percentage, notes, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_feature_flags |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryStaffAssignment (country_staff_assignments)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_staff_assignments`
- **Columns**: uuid, version, is_deleted, deleted_at, id, user_id, country_code, role_in_country, is_active, assigned_by, notes, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_staff_assignments |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### OmanDeliveryZone (oman_delivery_zones)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `oman_delivery_zones`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, zone_code, zone_name, description, car_rate, van_rate, truck_rate, weight_surcharge_rate, weight_surcharge_threshold_kg, cities_json, sort_order, is_active, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | oman_delivery_zones |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### CountryConfigVersion (country_config_versions)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_config_versions`
- **Columns**: uuid, is_deleted, deleted_at, id, country_code, config_type, version, payload_json, status, draft_by, approved_by, published_at, effective_from, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_config_versions |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SupplierKYCRequirement (supplier_kyc_requirements)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `supplier_kyc_requirements`
- **Columns**: uuid, version, is_deleted, deleted_at, id, country_code, kyc_tier_required, document_types_required, verification_wait_days, auto_approve_threshold, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | supplier_kyc_requirements |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LogisticsPartnerKYCRequirement (logistics_partner_kyc_requirements)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `logistics_partner_kyc_requirements`
- **Columns**: uuid, version, is_deleted, deleted_at, id, country_code, min_experience_months, required_documents, insurance_required, insurance_min_coverage, vehicle_requirements, background_check_required, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | logistics_partner_kyc_requirements |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryCommissionRate (country_commission_rates)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_commission_rates`
- **Columns**: uuid, version, created_at, updated_at, is_deleted, deleted_at, id, country_code, supplier_tier, name, rate_percent, fixed_fee, effective_from, effective_to
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_commission_rates |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryLocalization (country_localizations)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_localizations`
- **Columns**: uuid, version, is_deleted, deleted_at, id, country_code, default_numeral_system, hijri_calendar_enabled, rtl_layout_enabled, address_format, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_localizations |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryPaymentAlias (country_payment_aliases)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_payment_aliases`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, alias_type, alias_value, is_active, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_payment_aliases |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryLegalContract (country_legal_contracts)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_legal_contracts`
- **Columns**: uuid, is_deleted, deleted_at, id, country_code, contract_type, version, content_html, is_active, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_legal_contracts |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryCategoryTaxRate (country_category_tax_rates)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_category_tax_rates`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, category_id, tax_rate, tax_name, category_slug, rate, is_exempt, is_reduced, notes, source, is_active, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_category_tax_rates |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryCity (country_cities)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_cities`
- **Columns**: uuid, version, is_deleted, deleted_at, id, country_code, name, name_local, population, is_capital, latitude, longitude, postal_code_prefix, status, is_active, region, sort_order, source, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_cities |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryHolidayCalendar (country_holiday_calendars)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_holiday_calendars`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, holiday_date, name, local_name, is_observed, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_holiday_calendars |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryGatewayConfig (country_gateway_configs)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_gateway_configs`
- **Columns**: uuid, version, is_deleted, deleted_at, id, country_code, gateway_id, gateway_name, is_enabled, priority, credentials, environment, settings, last_tested_at, last_test_result, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_gateway_configs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryCommunicationThread (country_communication_threads)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_communication_threads`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, entity_type, entity_id, participants, is_active, last_message_at, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_communication_threads |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryCommissionRateHistory (country_commission_rate_histories)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_commission_rate_histories`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, category_id, supplier_tier, rate_percent, effective_from, effective_to, changed_by, change_reason, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_commission_rate_histories |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryLogisticsZone (country_logistics_zones)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_logistics_zones`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, zone_code, zone_name, zone_type, cities, pricing_config, is_active, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_logistics_zones |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryPayoutRule (country_payout_rules)

- **File**: `backend/domains\country\models\country_enhancements.py`
- **Schema**: country
- **Tablename**: `country_payout_rules`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, supplier_tier, min_amount, max_amount, fixed_fee, percent_fee, settlement_days, is_active, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_payout_rules |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryLegal (country_legals)

- **File**: `backend/domains\country\models\country_legal.py`
- **Schema**: country
- **Tablename**: `country_legals`
- **Columns**: deleted_at, id, uuid, version, country_code, is_active, is_deleted, created_at, updated_at, legal_entity_required, consumer_protection_days, data_privacy_framework, gdpr_compliant, local_data_residency, compliance_score, legal_risk_tier, contract_templates_json, regulatory_bodies_json
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_legals |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CountryTax (country_taxes)

- **File**: `backend/domains\country\models\country_tax.py`
- **Schema**: country
- **Tablename**: `country_taxes`
- **Columns**: deleted_at, id, uuid, country_code, is_active, is_deleted, version, created_at, updated_at, tax_type, tax_rate, tax_name, tax_inclusive, tax_exempt_categories_json, tax_reduced_rates_json
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | country |
| Law 9: Naming (snake_case, plural) | PASS | country_taxes |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CrossCountryCustomerSession (cross_country_customer_sessions)

- **File**: `backend/domains\customers\models\cross_country_session.py`
- **Schema**: customers
- **Tablename**: `cross_country_customer_sessions`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, user_id, source_country_code, target_country_code, session_data, conversion, order_id, ip_address, user_agent, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | customers |
| Law 9: Naming (snake_case, plural) | PASS | cross_country_customer_sessions |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### Referral (referrals)

- **File**: `backend/domains\customers\models\customer_schema_models.py`
- **Schema**: customers
- **Tablename**: `referrals`
- **Columns**: id, referrer_id, referred_id, referral_code, status, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | customers |
| Law 9: Naming (snake_case, plural) | PASS | referrals |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ReferralPointEvent (referral_point_events)

- **File**: `backend/domains\customers\models\customer_schema_models.py`
- **Schema**: customers
- **Tablename**: `referral_point_events`
- **Columns**: id, user_id, event_type, points, referred_user_id, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | customers |
| Law 9: Naming (snake_case, plural) | PASS | referral_point_events |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CommissionAgreement (commission_agreements)

- **File**: `backend/domains\finance\models\commission.py`
- **Schema**: finance
- **Tablename**: `commission_agreements`
- **Columns**: uuid, version, is_deleted, deleted_at, id, supplier_id, country_code, tier, rate, set_by_admin_id, is_active, effective_from, effective_to, note, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | commission_agreements |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ProductCommissionOverride (product_commission_overrides)

- **File**: `backend/domains\finance\models\commission.py`
- **Schema**: finance
- **Tablename**: `product_commission_overrides`
- **Columns**: uuid, version, is_deleted, deleted_at, id, product_id, supplier_id, rate_percent, set_by_admin_id, is_active, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | product_commission_overrides |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CommissionLedgerEntry (commission_ledger_entries)

- **File**: `backend/domains\finance\models\commission.py`
- **Schema**: finance
- **Tablename**: `commission_ledger_entries`
- **Columns**: uuid, version, is_deleted, deleted_at, id, supplier_id, order_id, order_item_id, product_id, category_slug, badge_level, global_default_rate, category_rate, badge_rate, override_rate, applied_rate, calculation_method, order_value, commission_pct, cap_applied, commission_amount, low_value_threshold_used, fixed_cap_used, override_flag, is_adjusted, currency, amount, adjusted_by_id, status, credited_at, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | commission_ledger_entries |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CommissionCategoryRate (commission_category_rates)

- **File**: `backend/domains\finance\models\commission.py`
- **Schema**: finance
- **Tablename**: `commission_category_rates`
- **Columns**: uuid, version, is_deleted, deleted_at, id, category_id, category_slug, category_display_name, country_code, rate_percent, is_active, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | commission_category_rates |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### FiscalPeriod (fiscal_periods)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `fiscal_periods`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, country_code, period_year, period_month, period_start, period_end, status, is_locked, closed_at, closed_by_id, notes, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | fiscal_periods |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### TransactionLedger (transaction_ledgers)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `transaction_ledgers`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, created_by_id, id, user_id, supplier_id, logistics_partner_id, order_id, order_item_id, shipment_id, payment_method, product_subtotal, discount_amount, delivery_pickup_charge, delivery_dropoff_charge, delivery_total, vat_amount, zozi_commission_rate, zozi_commission, net_supplier_amount, net_logistics_amount, net_zozi_amount, cod_collected_amount, cod_remittance_due, settlement_status, currency, transaction_type, reference_id, balance_after, notes, amount, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | transaction_ledgers |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SupplierSettlement (supplier_settlements)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `supplier_settlements`
- **Columns**: uuid, version, created_by_id, id, supplier_id, order_id, ledger_id, payout_id, shipment_id, gross_amount, commission_amount, commission_deducted, commission_rate, vat_on_commission, net_amount, status, settled_at, eligible_at, bank_transaction_id, currency, created_at, updated_at, country_code, is_deleted, deleted_at, deleted_by_id
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | supplier_settlements |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### JournalEntry (journal_entries)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `journal_entries`
- **Columns**: uuid, version, updated_at, id, entry_date, reference_number, description, source, country_code, currency, is_reconciled, created_by_id, reference_type, reference_id, period_id, reversal_of_id, is_deleted, deleted_at, deleted_by_id, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | journal_entries |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### JournalEntryLine (journal_entry_lines)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `journal_entry_lines`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, entry_id, account_id, cost_center_id, amount, side, description, entity_type, entity_id, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | journal_entry_lines |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Account (accounts)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `accounts`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, group_id, code, name, normal_side, currency, is_active, display_order, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | accounts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### AccountGroup (account_groups)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `account_groups`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, code, name, description, account_type, normal_side, display_order, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | account_groups |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### AccountBalance (account_balances)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `account_balances`
- **Columns**: uuid, version, created_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, account_id, user_id, balance, currency, last_entry_id, last_entry_at, last_updated, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | account_balances |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ARLedgerEntry (ar_ledger_entries)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `ar_ledger_entries`
- **Columns**: uuid, version, updated_at, deleted_by_id, id, customer_id, order_id, invoice_id, reference_type, reference_id, entry_type, amount, balance_after, currency, status, due_date, settled_at, description, created_by_id, created_at, country_code, is_deleted, deleted_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | ar_ledger_entries |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### APLedger (ap_ledger_entries)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `ap_ledger_entries`
- **Columns**: uuid, version, updated_at, deleted_by_id, id, supplier_id, order_id, invoice_id, settlement_id, reference_type, reference_id, entry_type, amount, balance_after, currency, status, due_date, paid_at, description, created_by_id, created_at, country_code, is_deleted, deleted_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | ap_ledger_entries |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### FinancialReport (financial_reports)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `financial_reports`
- **Columns**: uuid, version, created_at, updated_at, deleted_by_id, created_by_id, id, report_type, period_start, period_end, country_code, data, generated_at, is_deleted, deleted_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | financial_reports |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Invoice (invoices)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `invoices`
- **Columns**: uuid, version, created_by_id, id, order_id, shipment_id, supplier_id, invoice_number, invoice_type, subtotal, tax_amount, shipping_amount, discount_amount, total_amount, currency, status, issued_at, due_at, picked_at, dispatched_at, delivered_at, paid_at, notes, created_at, updated_at, country_code, is_deleted, deleted_at, deleted_by_id
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | invoices |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### InvoiceItem (invoice_items)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `invoice_items`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, invoice_id, product_id, description, quantity, unit_price, discount_amount, tax_rate, line_total, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | invoice_items |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### RefundLedger (refund_ledgers)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `refund_ledgers`
- **Columns**: uuid, version, updated_at, created_by_id, id, order_id, return_request_id, ledger_id, bank_transaction_id, reason, refund_reason, refund_method, customer_refund_amount, supplier_reversal, logistics_reversal, delivery_fee_reversal, commission_reversal, vat_adjustment, vat_reversal, performed_by_id, processed_at, currency, status, created_at, country_code, is_deleted, deleted_at, deleted_by_id
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | refund_ledgers |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### BankTransaction (bank_transactions)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `bank_transactions`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, transaction_ref, source, transaction_type, category, amount, currency, description, linked_order_id, linked_supplier_id, linked_logistics_id, linked_payout_id, linked_refund_id, reconciled, reconciled_by_id, reconciled_at, transaction_date, status, created_at, country_code, flagged, flag_reason
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | bank_transactions |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### VATRemittance (vat_remittances)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `vat_remittances`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, period_start, period_end, vat_collected_amount, vat_adjustment_amount, amount_due, amount, amount_remitted, currency, bank_transaction_id, remitted_by_id, remitted_at, notes, status, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | vat_remittances |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CashAccount (cash_accounts)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `cash_accounts`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, id, name, account_type, currency, balance, description, is_active, created_by_id, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | cash_accounts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CashTransaction (cash_transactions)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `cash_transactions`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, account_id, transaction_type, amount, balance_after, description, reference, category, performed_by_id, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | cash_transactions |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### TreasuryAccount (treasury_accounts)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `treasury_accounts`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, created_by_id, id, slug, name, account_type, currency, gl_account_code, description, employee_id, balance, is_active, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | treasury_accounts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### TreasuryTransaction (treasury_transactions)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `treasury_transactions`
- **Columns**: uuid, version, created_at, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, from_account_id, to_account_id, account_id, transaction_type, amount, currency, reference, description, posted_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | treasury_transactions |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CashFlowForecast (cash_flow_forecasts)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `cash_flow_forecasts`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, forecast_date, period_start, period_end, net_cash_flow, opening_balance, closing_balance, country_code, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | cash_flow_forecasts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CashPositionSnapshot (cash_position_snapshots)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `cash_position_snapshots`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, snapshot_time, account_id, balance, currency, country_code, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | cash_position_snapshots |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### GatewaySettlementSchedule (gateway_settlement_schedules)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `gateway_settlement_schedules`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, gateway_id, settlement_date, amount, currency, status, country_code, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | gateway_settlement_schedules |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PendingJournalEntry (pending_journal_entries)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `pending_journal_entries`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, id, lines_json, description, source, country_code, entry_date, amount_threshold_triggered, status, created_by_id, approved_by_id, rejected_by_id, rejection_reason, approved_at, journal_entry_id, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | pending_journal_entries |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PayoutBatch (payout_batches)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `payout_batches`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, id, batch_number, country_code, total_amount, item_count, status, created_by_id, approved_by_id, dispatched_at, settled_at, notes, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | payout_batches |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PayoutBatchItem (payout_batch_items)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `payout_batch_items`
- **Columns**: uuid, version, created_at, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, batch_id, entity_type, entity_id, amount, currency, reference, status, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | payout_batch_items |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### BankMappingRule (bank_mapping_rules)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `bank_mapping_rules`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, id, country_code, name, match_pattern, description_contains, account_code, normal_side, category, priority, is_active, created_by_id, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | bank_mapping_rules |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### BankStatementImport (bank_statement_imports)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `bank_statement_imports`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, bank_name, file_name, statement_period_start, statement_period_end, currency, total_lines, matched_lines, unmatched_lines, status, imported_by_id, country_code, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | bank_statement_imports |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### BankStatementLine (bank_statement_lines)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `bank_statement_lines`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, import_id, txn_date, description, reference, amount, mapped_account_code, mapped_side, mapping_rule_id, status, posted_journal_entry_id, reconciled_transaction_id, country_code, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | bank_statement_lines |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### FixedAsset (fixed_assets)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `fixed_assets`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, id, name, asset_code, category, purchase_date, purchase_cost, salvage_value, useful_life_months, accumulated_depreciation, last_depreciated_date, asset_account_code, depreciation_account_code, accumulated_depr_account_code, status, country_code, created_by_id, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | fixed_assets |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Accrual (accruals)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `accruals`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, id, accrual_type, description, amount, expense_account_code, accrual_account_code, accrual_date, reversal_date, status, journal_entry_id, reversal_entry_id, country_code, created_by_id, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | accruals |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ScannedExpense (scanned_expenses)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `scanned_expenses`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, created_by_id, id, employee_id, vendor_name, invoice_number, expense_date, amount, currency, tax_amount, category, description, expense_account_code, image_url, ocr_raw_text, ocr_confidence, status, posted_journal_entry_id, reviewed_by_id, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | scanned_expenses |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### AutomationRule (automation_rules)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `automation_rules`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, created_by_id, id, name, description, rule_type, trigger, action, config, is_active, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | automation_rules |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### AutomationLog (automation_logs)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `automation_logs`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, id, rule_id, status, message, records_affected, country_code, created_at, updated_at, created_by_id
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | automation_logs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Vendor (vendors)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `vendors`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, created_by_id, id, name, tax_id, contact_email, currency, payment_terms_days, country_code, is_active, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | vendors |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Customer (customers)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `customers`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, created_by_id, id, name, tax_id, contact_email, currency, payment_terms_days, credit_limit, country_code, is_active, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | customers |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CostCenter (cost_centers)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `cost_centers`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, created_by_id, id, code, name, country_code, is_active, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | cost_centers |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### APBill (ap_bills)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `ap_bills`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, id, vendor_id, bill_number, bill_date, due_date, account_code, amount, tax_amount, description, status, linked_journal_entry_id, paid_journal_entry_id, country_code, created_by_id, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | ap_bills |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ARInvoice (ar_invoices)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `ar_invoices`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, id, customer_id, invoice_number, invoice_date, due_date, account_code, amount, tax_amount, description, status, linked_journal_entry_id, paid_journal_entry_id, country_code, created_by_id, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | ar_invoices |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### BankAccount (bank_accounts)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `bank_accounts`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, created_by_id, id, bank_name, account_name, account_number, iban, swift_bic, currency, gl_account_code, country_code, is_active, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | bank_accounts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Budget (budgets)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `budgets`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, id, account_code, fiscal_period_id, amount, currency, country_code, notes, created_by_id, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | budgets |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### BankReconciliation (bank_reconciliations)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `bank_reconciliations`
- **Columns**: uuid, version, created_at, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, statement_line_id, journal_entry_id, matched_amount, status, note, matched_by_id, matched_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | bank_reconciliations |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### RecurringTemplate (recurring_templates)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `recurring_templates`
- **Columns**: uuid, version, is_deleted, deleted_at, deleted_by_id, id, name, frequency, next_run_date, description, lines, currency, country_code, is_active, created_by_id, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | recurring_templates |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### FinanceAuditLog (finance_audit_logs)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `finance_audit_logs`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, action, actor_id, actor_role, entity_type, entity_id, country_code, detail, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | finance_audit_logs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### FinanceAutomationLog (finance_automation_logs)

- **File**: `backend/domains\finance\models\general_ledger.py`
- **Schema**: finance
- **Tablename**: `finance_automation_logs`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, deleted_by_id, created_by_id, id, kind, records_processed, records_changed, detail, run_by_id, country_code, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | finance_automation_logs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Payment (payments)

- **File**: `backend/domains\finance\models\payments.py`
- **Schema**: finance
- **Tablename**: `payments`
- **Columns**: id, is_deleted, order_id, amount, payment_method, provider, status, intent_id, created_at, updated_at, country_code, layout_json
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | payments |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PaymentReconciliationRun (payment_reconciliation_runs)

- **File**: `backend/domains\finance\models\payments.py`
- **Schema**: finance
- **Tablename**: `payment_reconciliation_runs`
- **Columns**: id, is_deleted, run_date, total_amount, reconciled_count, unmatched_count, processed_count, stale_pending_orders, recent_webhook_count, result_json, started_at, completed_at, status, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | payment_reconciliation_runs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PaymentGatewayConnection (payment_gateway_connections)

- **File**: `backend/domains\finance\models\payments.py`
- **Schema**: finance
- **Tablename**: `payment_gateway_connections`
- **Columns**: id, is_deleted, provider_code, gateway_name, country_code, environment, is_active, credentials, fee_config, supported_methods, last_sync_at, provider_kind, display_name, is_enabled, supports_customer_checkout, supports_payouts, payment_mode, public_key, secret_key, webhook_secret, merchant_id, api_base_url, webhook_url, test_url, settlement_cycle, supported_currencies_json, extra_config_json, notes, fee_percent, fixed_fee_amount, payout_fee_percent, payout_fixed_fee_amount, pass_fee_to_customer, test_status, test_message, last_tested_at, updated_by_id, adapter_supported, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | payment_gateway_connections |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Payout (payouts)

- **File**: `backend/domains\finance\models\payments.py`
- **Schema**: finance
- **Tablename**: `payouts`
- **Columns**: id, is_deleted, batch_number, order_id, supplier_id, amount, currency, method, status, reference_id, reference, provider, provider_recipient_id, provider_transfer_id, provider_status, notes, processed_at, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | payouts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LogisticsPartnerPayout (logistics_partner_payouts)

- **File**: `backend/domains\finance\models\payments.py`
- **Schema**: finance
- **Tablename**: `logistics_partner_payouts`
- **Columns**: id, is_deleted, partner_id, amount, currency, period_start, period_end, status, reference_id, processed_at, country_code, created_at, updated_at, method, notes
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | logistics_partner_payouts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PayoutRule (payout_rules)

- **File**: `backend/domains\finance\models\tax_rules.py`
- **Schema**: finance
- **Tablename**: `payout_rules`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, min_amount, max_amount, fixed_fee, percent_fee, is_active, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | payout_rules |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### TaxRule (tax_rules)

- **File**: `backend/domains\finance\models\tax_rules.py`
- **Schema**: finance
- **Tablename**: `tax_rules`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, tax_name, tax_rate, is_active, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | tax_rules |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PayoutRuleCategory (payout_rule_categories)

- **File**: `backend/domains\finance\models\tax_rules.py`
- **Schema**: finance
- **Tablename**: `payout_rule_categories`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, category_slug, payout_rate, min_amount, max_amount, is_active, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | payout_rule_categories |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PayoutRuleProduct (payout_rule_products)

- **File**: `backend/domains\finance\models\tax_rules.py`
- **Schema**: finance
- **Tablename**: `payout_rule_products`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, product_id, payout_rate, min_amount, max_amount, is_active, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | finance |
| Law 9: Naming (snake_case, plural) | PASS | payout_rule_products |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### AdminAnalyticsSnapshot (admin_analytics_snapshots)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `admin_analytics_snapshots`
- **Columns**: id, snapshot_key, snapshot_group, period, payload_json, computed_at, expires_at, is_deleted, country_code
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 19: Missing required column: created_at; Law 20: Missing required column: updated_at

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | admin_analytics_snapshots |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | FAIL | MISSING |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### RolePermissionSetting (role_permission_settings)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `role_permission_settings`
- **Columns**: id, role, permissions_json, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | role_permission_settings |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SystemAlert (system_alerts)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `system_alerts`
- **Columns**: id, alert_type, severity, title, message, is_acknowledged, acknowledged_by_id, acknowledged_at, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | system_alerts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### AdminChangeAuditLog (admin_change_audit_logs)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `admin_change_audit_logs`
- **Columns**: id, admin_id, action, entity, entity_key, before_json, after_json, notes, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | admin_change_audit_logs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### AdminActivityLog (admin_activity_logs)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `admin_activity_logs`
- **Columns**: id, admin_id, action, details, ip_address, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | admin_activity_logs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SystemSetting (system_settings)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `system_settings`
- **Columns**: id, key, value, value_type, description, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | system_settings |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### APIKey (api_keys)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `api_keys`
- **Columns**: id, name, key_hash, permissions, is_active, expires_at, created_by_id, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | api_keys |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### BadgeBillingRecord (badge_billing_records)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `badge_billing_records`
- **Columns**: id, user_id, supplier_id, billing_reference, badge_level, charge_type, charge_source, amount, currency, status, reference_id, period_start, period_end, due_at, billed_at, paid_at, payment_method, notes, created_by_id, bank_transaction_id, created_at, updated_at, country_code, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | badge_billing_records |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### BadgeTransaction (badge_transactions)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `badge_transactions`
- **Columns**: id, user_id, amount, transaction_type, reference_id, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | badge_transactions |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### BadgeTier (badge_tiers)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `badge_tiers`
- **Columns**: id, name, min_points, benefits, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | badge_tiers |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CommissionBadgeTier (commission_badge_tiers)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `commission_badge_tiers`
- **Columns**: id, name, badge_level, commission_rate, setup_fee, recurring_fee, recurring_interval, benefits_json, min_fulfilled_orders, min_monthly_revenue, sort_order, is_active, is_deleted, updated_by_id, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | commission_badge_tiers |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CommissionGlobalConfig (commission_global_configs)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `commission_global_configs`
- **Columns**: id, default_rate, low_value_threshold, fixed_cap_amount, fixed_cap_enabled, margin_protection_enabled, margin_threshold, is_deleted, updated_by_id, updated_at, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | commission_global_configs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### TicketReply (ticket_replies)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `ticket_replies`
- **Columns**: id, ticket_id, sender_id, message, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | ticket_replies |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PaymentProviderConfig (payment_provider_configs)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `payment_provider_configs`
- **Columns**: id, provider_name, config, is_active, is_deleted, updated_by_id, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | payment_provider_configs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmailProviderConfig (email_provider_configs)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `email_provider_configs`
- **Columns**: id, provider, is_active, updated_by_id, created_at, updated_at, email_from_default, email_from_promotional, email_from_transactional, email_from_notification, email_from_alert, email_from_verification, email_from_login_verification, email_from_password_reset, resend_api_key, resend_webhook_secret, smtp_host, smtp_port, smtp_username, smtp_password, smtp_use_tls, smtp_use_ssl, smtp_timeout_seconds, is_deleted, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | email_provider_configs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ShippingCarrier (shipping_carriers)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `shipping_carriers`
- **Columns**: id, supplier_id, name, code, is_active, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | shipping_carriers |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ShippingZone (shipping_zones)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `shipping_zones`
- **Columns**: id, supplier_id, name, countries, is_active, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | shipping_zones |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### FinanceBankAccount (finance_bank_accounts)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `finance_bank_accounts`
- **Columns**: id, account_name, account_number, bank_name, account_label, branch_name, iban, swift_code, routing_number, currency, support_email, support_phone, remittance_reference_prefix, instructions, is_active, scope, created_by_id, updated_by_id, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | finance_bank_accounts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PromotionOrderTier (promotion_order_tiers)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `promotion_order_tiers`
- **Columns**: id, promotion_id, tier_name, min_order_amount, max_order_amount, discount_type, discount_amount, discount_value, stacking_allowed, is_active, sort_order, updated_by_id, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | promotion_order_tiers |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LogisticsCODRemittanceReceipt (logistics_cod_remittance_receipts)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `logistics_cod_remittance_receipts`
- **Columns**: id, partner_id, shipment_id, settlement_id, amount, bank_reference, receipt_file_url, notes, review_note, reviewed_by_id, status, currency, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | logistics_cod_remittance_receipts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LogisticsPartnerDocument (logistics_partner_documents)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `logistics_partner_documents`
- **Columns**: id, partner_id, doc_type, file_url, reviewed_by_id, is_verified, verified_at, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | logistics_partner_documents |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LogisticsSettlement (logistics_settlements)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `logistics_settlements`
- **Columns**: id, partner_id, order_id, ledger_id, shipment_id, amount, pickup_charge, dropoff_charge, total_delivery_fee, cod_collected, cod_remitted, cod_retained, cod_remittance_status, eligible_at, status, currency, is_deleted, payout_id, bank_transaction_id, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | logistics_settlements |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ShipmentConfirmation (shipment_confirmations)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `shipment_confirmations`
- **Columns**: id, shipment_id, order_id, supplier_id, requester_user_id, requester_role, target_user_id, target_role, confirmation_type, status, requested_status, requested_event_type, current_hub, notes, confirmation_code, confirmed_at, responded_at, tracking_number, delivery_signature_name, delivery_signature_data_url, delivery_signature_captured_at, response_notes, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | shipment_confirmations |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ChatbotQueryEvent (chatbot_query_events)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `chatbot_query_events`
- **Columns**: id, user_id, session_id, event_type, message, normalized_query, intent, filters_json, result_count, product_ids_json, clicked_product_id, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | chatbot_query_events |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PushNotificationToken (push_notification_tokens)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `push_notification_tokens`
- **Columns**: id, user_id, token, device_type, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | push_notification_tokens |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ProductVerification (product_verifications)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `product_verifications`
- **Columns**: id, product_id, status, verified_by_id, shipment_id, verification_type, result, expected_specs, actual_specs, discrepancies, scan_code, image_urls, notes, created_at, updated_at, order_id, is_deleted, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | product_verifications |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ProcessedWebhookEvent (processed_webhook_events)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `processed_webhook_events`
- **Columns**: id, processor, event_id, payload_hash, processed_at, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | processed_webhook_events |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### NormalizedWebhookEvent (normalized_webhook_events)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `normalized_webhook_events`
- **Columns**: id, provider_code, gateway_event_id, event_type, status, environment, processed_at, zozi_order_id, gateway_transaction_id, gateway_customer_id, gross_amount, currency, gateway_fee, net_settlement, fraud_score, three_ds_status, avs_result, raw_payload, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | normalized_webhook_events |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeExpense (employee_expenses)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `employee_expenses`
- **Columns**: id, employee_id, expense_type, amount, description, status, approved_by_id, approved_at, receipt_url, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | employee_expenses |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SupplierCountryCommission (supplier_country_commissions)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `supplier_country_commissions`
- **Columns**: id, supplier_id, country_code, commission_rate, category_slug, notes, is_active, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | supplier_country_commissions |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### RetentionJobRun (retention_job_runs)

- **File**: `backend/domains\governance\models\admin.py`
- **Schema**: governance
- **Tablename**: `retention_job_runs`
- **Columns**: id, job_type, target_table, target_name, cutoff_days, records_deleted, archived_count, deleted_count, artifact_path, result_json, started_at, completed_at, status, error_message, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | retention_job_runs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### UserBrowsingHistory (user_browsing_histories)

- **File**: `backend/domains\governance\models\core.py`
- **Schema**: governance
- **Tablename**: `user_browsing_histories`
- **Columns**: id, user_id, product_id, viewed_at, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 22: FK column country_code missing ondelete

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | user_browsing_histories |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | FAIL | Missing ondelete on FK |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SystemHealthEvent (system_health_events)

- **File**: `backend/domains\governance\models\core.py`
- **Schema**: governance
- **Tablename**: `system_health_events`
- **Columns**: id, service, metric_name, metric_value, severity, message, created_at, updated_at, is_deleted, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 22: FK column country_code missing ondelete

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | system_health_events |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | FAIL | Missing ondelete on FK |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LegalContractTemplate (legal_contract_templates)

- **File**: `backend/domains\governance\models\legal_contract_template.py`
- **Schema**: governance
- **Tablename**: `legal_contract_templates`
- **Columns**: id, country_code, template_type, version, content, is_active, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | governance |
| Law 9: Naming (snake_case, plural) | PASS | legal_contract_templates |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Office (offices)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `offices`
- **Columns**: id, name, city, latitude, longitude, geo_fence_radius_meters, address, phone, email, is_active, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | offices |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PhysicalIDCard (physical_id_cards)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `physical_id_cards`
- **Columns**: id, employee_id, card_number, issued_at, expires_at, is_revoked, revoked_at, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | physical_id_cards |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### DynamicQRSession (dynamic_qr_sessions)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `dynamic_qr_sessions`
- **Columns**: id, employee_id, qr_token, expires_at, used_at, ip_address, user_agent, device_fingerprint, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | dynamic_qr_sessions |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeBiometric (employee_biometrics)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_biometrics`
- **Columns**: id, employee_id, fingerprint_hash, face_encoding, biometric_type, enrolled_at, is_active, is_deleted, country_code
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 19: Missing required column: created_at; Law 20: Missing required column: updated_at

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_biometrics |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | FAIL | MISSING |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### GeoFenceLog (geo_fence_logs)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `geo_fence_logs`
- **Columns**: id, employee_id, latitude, longitude, accuracy_meters, scanned_at, is_within_fence, is_deleted, country_code
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 19: Missing required column: created_at; Law 20: Missing required column: updated_at

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | geo_fence_logs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | FAIL | MISSING |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeRole (employee_roles)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_roles`
- **Columns**: id, role_name, permissions, authority_level, can_approve_leave, can_approve_expense, can_manage_users, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_roles |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### OrgUnit (org_units)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `org_units`
- **Columns**: id, name, parent_id, country_code, level, is_active, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | org_units |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Employee (employees)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employees`
- **Columns**: id, user_id, employee_code, office_id, department, position, employment_type, employment_status, salary, currency, country_code, hire_date, termination_date, is_verified, gender, years_of_experience, performance_score, education_level, notes, reporting_manager_id, hiring_manager_id, authority_level, org_unit_id, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employees |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeAttendance (employee_attendances)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_attendances`
- **Columns**: id, employee_id, record_date, scan_in_time, scan_out_time, scan_type, location_lat, location_long, device_fingerprint, is_anomaly, status, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_attendances |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeWorkLog (employee_work_logs)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_work_logs`
- **Columns**: id, employee_id, record_date, hours_worked, task_description, location_lat, location_long, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_work_logs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeLeaveRequest (employee_leave_requests)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_leave_requests`
- **Columns**: id, employee_id, leave_type, start_date, end_date, days_requested, status, approved_by_id, approved_at, rejection_reason, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_leave_requests |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeLeaveLedger (employee_leave_ledgers)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_leave_ledgers`
- **Columns**: id, employee_id, leave_type, year, allocated_days, used_days, carried_forward, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_leave_ledgers |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeShiftRoster (employee_shift_rosters)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_shift_rosters`
- **Columns**: id, employee_id, shift_date, start_time, end_time, shift_type, status, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_shift_rosters |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeAsset (employee_assets)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_assets`
- **Columns**: id, employee_id, asset_type, asset_id, serial_no, assigned_at, returned_at, status, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_assets |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeCertification (employee_certifications)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_certifications`
- **Columns**: id, employee_id, cert_type, cert_name, issued_date, expiry_date, is_valid, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_certifications |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeDocument (employee_documents)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_documents`
- **Columns**: id, employee_id, doc_type, file_url, expiry_date, verified_by_id, verified_at, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_documents |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeDependent (employee_dependents)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_dependents`
- **Columns**: id, employee_id, name, relation, dob, is_insured, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_dependents |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeRelation (employee_relations)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_relations`
- **Columns**: id, employee_id, related_person_name, relation_type, is_internal_employee, internal_employee_id, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_relations |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeAddress (employee_addresses)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_addresses`
- **Columns**: id, employee_id, address_type, street, city, state, postal_code, country_code, is_primary, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_addresses |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### COIReport (coi_reports)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `coi_reports`
- **Columns**: id, employee_id, related_person_name, relation_type, is_internal, internal_employee_id, risk_level, is_approved, approved_by_id, approved_at, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | coi_reports |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### TravelRequest (employee_travel_requests)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_travel_requests`
- **Columns**: id, employee_id, destination_country, start_date, end_date, purpose, status, approved_by_id, approved_at, per_diem_json, total_cost, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_travel_requests |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### AlumniNetwork (alumni_networks)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `alumni_networks`
- **Columns**: id, employee_id, status, granted_at, eligibility_expires_at, notes, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | alumni_networks |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### DisciplinaryCase (disciplinary_cases)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `disciplinary_cases`
- **Columns**: id, employee_id, employee_name, stage, description, issued_at, status, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | disciplinary_cases |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### OffboardingCase (offboarding_cases)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `offboarding_cases`
- **Columns**: id, employee_id, employee_name, reason, status, initiated_at, completed_at, notes, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | offboarding_cases |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### EmployeeRiskScore (employee_risk_scores)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_risk_scores`
- **Columns**: id, employee_id, assessment_date, score, risk_level, factors, notes, country_code, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_risk_scores |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PayrollRecord (payroll_records)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `payroll_records`
- **Columns**: id, country_code, employee_id, net_pay, status, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | payroll_records |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### TrainingModule (training_modules)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `training_modules`
- **Columns**: module_id, title, description, required_for_role, duration_minutes, is_active, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | training_modules |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### EmployeeTraining (employee_trainings)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_trainings`
- **Columns**: id, employee_id, module_id, status, score, completed_at, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_trainings |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### EmployeeActivityLog (employee_activity_logs)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `employee_activity_logs`
- **Columns**: id, actor_employee_id, action, entity_type, entity_id, metadata_json, ip_address, device_fingerprint, country_code, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | employee_activity_logs |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ShiftHandoverSession (shift_handover_sessions)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `shift_handover_sessions`
- **Columns**: id, country_code, outgoing_employee_id, incoming_employee_id, shift_date, notes, status, acknowledged_at, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | shift_handover_sessions |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ShiftHandoverTask (shift_handover_tasks)

- **File**: `backend/domains\hr\models\employee_models.py`
- **Schema**: hr
- **Tablename**: `shift_handover_tasks`
- **Columns**: id, session_id, description, priority, status, assigned_to_id, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | hr |
| Law 9: Naming (snake_case, plural) | PASS | shift_handover_tasks |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### Warehouse (warehouses)

- **File**: `backend/domains\logistics\models\erp.py`
- **Schema**: logistics
- **Tablename**: `warehouses`
- **Columns**: uuid, is_deleted, deleted_at, version, created_by_id, id, name, code, address, city, country_code, is_active, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | warehouses |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PurchaseOrder (purchase_orders)

- **File**: `backend/domains\logistics\models\erp.py`
- **Schema**: logistics
- **Tablename**: `purchase_orders`
- **Columns**: uuid, is_deleted, deleted_at, version, id, po_number, supplier_id, supplier_name, order_date, expected_delivery_date, warehouse_id, currency, notes, terms, shipping_address, country_code, created_by_id, status, subtotal, discount_total, tax_total, grand_total, total_amount, delivery_date, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | purchase_orders |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PurchaseOrderLine (purchase_order_lines)

- **File**: `backend/domains\logistics\models\erp.py`
- **Schema**: logistics
- **Tablename**: `purchase_order_lines`
- **Columns**: uuid, is_deleted, deleted_at, version, created_by_id, id, po_id, product_id, product_name, sku, description, quantity_ordered, quantity_received, unit_price, discount_percent, discount_amount, tax_rate, tax_amount, line_total, weight, volume, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | purchase_order_lines |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### GoodsReceiptNote (goods_receipt_notes)

- **File**: `backend/domains\logistics\models\erp.py`
- **Schema**: logistics
- **Tablename**: `goods_receipt_notes`
- **Columns**: uuid, is_deleted, deleted_at, version, created_by_id, id, grn_number, po_id, supplier_id, receipt_date, warehouse_id, status, notes, received_by_id, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | goods_receipt_notes |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### GoodsReceiptLine (goods_receipt_lines)

- **File**: `backend/domains\logistics\models\erp.py`
- **Schema**: logistics
- **Tablename**: `goods_receipt_lines`
- **Columns**: uuid, is_deleted, deleted_at, version, created_by_id, id, grn_id, po_line_id, product_id, product_name, sku, quantity_received, quantity_accepted, quantity_rejected, rejection_reason, lot_number, expiry_date, unit_cost, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | goods_receipt_lines |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SalesOrder (sales_orders)

- **File**: `backend/domains\logistics\models\erp.py`
- **Schema**: logistics
- **Tablename**: `sales_orders`
- **Columns**: uuid, is_deleted, deleted_at, version, id, so_number, customer_id, customer_name, customer_po_number, order_date, expected_delivery_date, warehouse_id, currency, shipping_address, billing_address, notes, terms, country_code, created_by_id, status, subtotal, discount_total, tax_total, grand_total, delivery_date, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | sales_orders |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SalesOrderLine (sales_order_lines)

- **File**: `backend/domains\logistics\models\erp.py`
- **Schema**: logistics
- **Tablename**: `sales_order_lines`
- **Columns**: uuid, is_deleted, deleted_at, version, created_by_id, id, so_id, product_id, product_name, sku, description, quantity_ordered, quantity_dispatched, unit_price, discount_percent, discount_amount, tax_rate, tax_amount, line_total, weight, volume, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | sales_order_lines |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### StockMovement (stock_movements)

- **File**: `backend/domains\logistics\models\erp.py`
- **Schema**: logistics
- **Tablename**: `stock_movements`
- **Columns**: uuid, is_deleted, deleted_at, version, id, product_id, warehouse_id, movement_type, reference_type, reference_id, quantity_change, quantity_after, unit_cost, total_cost, country_code, created_by_id, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | stock_movements |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ImportShipment (import_shipments)

- **File**: `backend/domains\logistics\models\erp.py`
- **Schema**: logistics
- **Tablename**: `import_shipments`
- **Columns**: uuid, is_deleted, deleted_at, version, id, shipment_ref, po_id, supplier_id, supplier_name, origin_country, port_of_loading, port_of_discharge, vessel_name, bill_of_lading, container_number, shipment_date, estimated_arrival, actual_arrival, currency, exchange_rate, warehouse_id, country_code, notes, created_by_id, status, product_cost_total, freight_cost, insurance_cost, port_charges, inland_freight, bank_charges, other_costs, total_landed_cost, duty_cost, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | import_shipments |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ImportShipmentLine (import_shipment_lines)

- **File**: `backend/domains\logistics\models\erp.py`
- **Schema**: logistics
- **Tablename**: `import_shipment_lines`
- **Columns**: uuid, is_deleted, deleted_at, version, created_by_id, id, shipment_id, po_line_id, product_id, product_name, sku, hs_code, quantity, unit_cost_fx, unit_cost_local, line_total_fx, weight_kg, volume_cbm, allocated_freight, allocated_insurance, allocated_port, allocated_other, duty_amount, landed_unit_cost, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | import_shipment_lines |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LandedCostAllocation (landed_cost_allocations)

- **File**: `backend/domains\logistics\models\erp.py`
- **Schema**: logistics
- **Tablename**: `landed_cost_allocations`
- **Columns**: uuid, is_deleted, deleted_at, version, created_by_id, id, shipment_id, cost_type, description, total_amount, allocation_method, currency, exchange_rate, country_code, status, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | landed_cost_allocations |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CustomsEntry (customs_entries)

- **File**: `backend/domains\logistics\models\erp.py`
- **Schema**: logistics
- **Tablename**: `customs_entries`
- **Columns**: uuid, is_deleted, deleted_at, version, created_by_id, id, shipment_id, customs_declaration_number, customs_broker, entry_date, duty_rate_applied, duty_amount, vat_on_duty, penalties, total_customs_cost, status, notes, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | customs_entries |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ImportCostTemplate (import_cost_templates)

- **File**: `backend/domains\logistics\models\erp.py`
- **Schema**: logistics
- **Tablename**: `import_cost_templates`
- **Columns**: uuid, is_deleted, deleted_at, version, created_by_id, id, name, default_duty_rate, default_freight_percent, default_insurance_percent, default_port_charges_percent, default_bank_charges_percent, allocation_method, country_code, is_active, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | import_cost_templates |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LogisticsPartner (logistics_partners)

- **File**: `backend/domains\logistics\models\logistics_entities.py`
- **Schema**: logistics
- **Tablename**: `logistics_partners`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, user_id, name, code, contact_name, contact_email, contact_phone, website, coverage_regions, service_types, status_code, verification_status, verification_note, verified_by, verified_at, country_code, created_at, business_type, region, city, address, postal_code, tax_id, bio, about_us, logo_url, banner_url, latitude, longitude, social_links, notes, is_terms_accepted, terms_version, terms_accepted_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | logistics_partners |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LogisticsPartnerProfile (logistics_partner_profiles)

- **File**: `backend/domains\logistics\models\logistics_entities.py`
- **Schema**: logistics
- **Tablename**: `logistics_partner_profiles`
- **Columns**: uuid, version, is_deleted, deleted_at, id, partner_id, tax_id, registration_number, business_type, years_in_business, insurance_provider, insurance_policy_number, insurance_expiry, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | logistics_partner_profiles |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LogisticsPartnerServiceArea (logistics_partner_service_areas)

- **File**: `backend/domains\logistics\models\logistics_entities.py`
- **Schema**: logistics
- **Tablename**: `logistics_partner_service_areas`
- **Columns**: uuid, version, is_deleted, deleted_at, id, partner_id, country_code, country_name, origin_city, city_name, zone_label, charge_amount, minimum_charge, per_kg_rate, pickup_charge, dropoff_charge, per_km_rate, currency, delivery_days_min, delivery_days_max, is_active, approval_status, review_note, reviewed_by_id, reviewed_at, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | logistics_partner_service_areas |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LogisticsPricingProfile (logistics_pricing_profiles)

- **File**: `backend/domains\logistics\models\logistics_entities.py`
- **Schema**: logistics
- **Tablename**: `logistics_pricing_profiles`
- **Columns**: uuid, version, is_deleted, deleted_at, id, partner_id, service_area_id, profile_name, base_in_city_fee, per_kg_rate, minimum_charge, maximum_charge, fuel_multiplier, base_inter_city_fee, per_km_rate, bulk_discount_threshold_kg, bulk_discount_percent, currency, is_active, approval_status, review_note, reviewed_by_id, reviewed_at, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | logistics_pricing_profiles |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LogisticsVehicleRule (logistics_vehicle_rules)

- **File**: `backend/domains\logistics\models\logistics_entities.py`
- **Schema**: logistics
- **Tablename**: `logistics_vehicle_rules`
- **Columns**: uuid, version, is_deleted, deleted_at, id, partner_id, service_area_id, vehicle_type, max_weight_kg, cost_multiplier, priority_rank, route_scope, max_volume_cm3, is_active, approval_status, review_note, reviewed_by_id, reviewed_at, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | logistics_vehicle_rules |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### LogisticsCategoryPricingRule (logistics_category_pricing_rules)

- **File**: `backend/domains\logistics\models\logistics_entities.py`
- **Schema**: logistics
- **Tablename**: `logistics_category_pricing_rules`
- **Columns**: uuid, version, is_deleted, deleted_at, id, partner_id, service_area_id, category_name, flat_fee_override, special_handling_fee, currency, is_active, approval_status, review_note, reviewed_by_id, reviewed_at, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | logistics_category_pricing_rules |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Shipment (shipments)

- **File**: `backend/domains\logistics\models\logistics_entities.py`
- **Schema**: logistics
- **Tablename**: `shipments`
- **Columns**: uuid, version, is_deleted, deleted_at, id, order_id, supplier_id, assigned_partner_id, carrier_id, tracking_number, carrier_name, status_code, distribution_channel, current_hub, scan_code, package_count, package_weight_kg, package_dimensions, packaged_at, packaged_by_user_id, packaged_notes, packaging_notes, shipped_at, estimated_delivery, actual_delivery, delivery_signature_name, delivery_signature_data_url, delivery_signature_captured_at, notes, accepted_vehicle_type, accepted_vehicle_multiplier, accepted_vehicle_selected_at, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | shipments |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ShipmentEvent (shipment_events)

- **File**: `backend/domains\logistics\models\logistics_entities.py`
- **Schema**: logistics
- **Tablename**: `shipment_events`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, shipment_id, order_id, supplier_id, actor_user_id, actor_role, event_type, status_after, distribution_channel, location, latitude, longitude, scan_code, notes, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | shipment_events |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CityDistanceMatrix (city_distance_matrices)

- **File**: `backend/domains\logistics\models\logistics_schema_models.py`
- **Schema**: logistics
- **Tablename**: `city_distance_matrices`
- **Columns**: id, origin_country_code, origin_city_name, destination_country_code, destination_city_name, distance_km, notes, created_by_id, updated_by_id, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now(); Law 22: FK column country_code missing ondelete

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | city_distance_matrices |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | FAIL | Missing ondelete on FK |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ShippingRule (shipping_rules)

- **File**: `backend/domains\logistics\models\shipping_rules.py`
- **Schema**: logistics
- **Tablename**: `shipping_rules`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, country_code, method, base_rate, per_kg_rate, is_active, created_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | logistics |
| Law 9: Naming (snake_case, plural) | PASS | shipping_rules |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Order (orders)

- **File**: `backend/domains\orders\models\order_entities.py`
- **Schema**: orders
- **Tablename**: `orders`
- **Columns**: uuid, version, id, order_number, customer_id, user_id, status_code, status_label, payment_status, payment_method, payment_provider, payment_intent_id, subtotal, subtotal_amount, shipping_fee, shipping_amount, tax_amount, vat_amount, discount_amount, total, total_amount, coupon_code, fraud_score, fraud_action, currency, shipping_address, shipping_city, shipping_country, shipping_postal_code, customer_phone, delivery_location, delivery_note, tracking_number, selected_partner_id, selected_service_area_id, estimated_delivery_min, estimated_delivery_max, payment_gateway_code, payment_gateway_fee_amount, payment_customer_total_amount, payment_gateway_fee_passed_to_customer, paid_at, country_code, created_at, updated_at, is_deleted, deleted_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | orders |
| Law 9: Naming (snake_case, plural) | PASS | orders |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### OrderItem (order_items)

- **File**: `backend/domains\orders\models\order_entities.py`
- **Schema**: orders
- **Tablename**: `order_items`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, order_id, product_id, variant_id, supplier_id, quantity, unit_price, price, total_price, product_name, product_image, selected_size, selected_color, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | orders |
| Law 9: Naming (snake_case, plural) | PASS | order_items |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### OrderLogisticsAllocation (order_logistics_allocations)

- **File**: `backend/domains\orders\models\order_entities.py`
- **Schema**: orders
- **Tablename**: `order_logistics_allocations`
- **Columns**: uuid, version, is_deleted, deleted_at, id, order_id, supplier_id, shipment_id, partner_id, service_area_id, allocation_source, partner_name_snapshot, partner_code_snapshot, service_area_label_snapshot, destination_country, destination_city, shipping_amount, pickup_charge, dropoff_charge, accepted_vehicle_rule_id, accepted_vehicle_type, accepted_vehicle_multiplier, accepted_shipping_amount, accepted_pickup_charge, accepted_dropoff_charge, estimated_delivery_min, estimated_delivery_max, currency, pricing_breakdown_json, accepted_pricing_breakdown_json, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | orders |
| Law 9: Naming (snake_case, plural) | PASS | order_logistics_allocations |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ReturnRequest (return_requests)

- **File**: `backend/domains\orders\models\order_entities.py`
- **Schema**: orders
- **Tablename**: `return_requests`
- **Columns**: uuid, version, is_deleted, deleted_at, id, order_id, order_item_id, customer_id, intent, reason, description, details, supplier_review_state, images, status_code, refund_amount, items, return_window_days, delivered_at, return_deadline, resolution_notes, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | orders |
| Law 9: Naming (snake_case, plural) | PASS | return_requests |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### OrderNotification (order_notifications)

- **File**: `backend/domains\orders\models\order_entities.py`
- **Schema**: orders
- **Tablename**: `order_notifications`
- **Columns**: uuid, version, updated_at, is_deleted, deleted_at, id, user_id, order_id, title, message, channel, is_read, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | orders |
| Law 9: Naming (snake_case, plural) | PASS | order_notifications |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### PaymentMethod (payment_methods)

- **File**: `backend/domains\payments\models\payment_models.py`
- **Schema**: payments
- **Tablename**: `payment_methods`
- **Columns**: id, is_deleted, deleted_at, version, user_id, country_code, provider, provider_method_id, method_type, last4, brand, expires_at, is_default, metadata_json, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | payments |
| Law 9: Naming (snake_case, plural) | PASS | payment_methods |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PaymentAttempt (payment_attempts)

- **File**: `backend/domains\payments\models\payment_models.py`
- **Schema**: payments
- **Tablename**: `payment_attempts`
- **Columns**: id, is_deleted, version, payment_id, country_code, attempt_no, status, provider, provider_intent_id, error_code, error_message, raw_response, attempted_at, completed_at, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | payments |
| Law 9: Naming (snake_case, plural) | PASS | payment_attempts |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Refund (refunds)

- **File**: `backend/domains\payments\models\payment_models.py`
- **Schema**: payments
- **Tablename**: `refunds`
- **Columns**: id, is_deleted, version, payment_id, country_code, amount, currency, reason, status, provider, provider_refund_id, notes, requested_by_id, approved_by_id, requested_at, completed_at, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 22: FK column requested_by_id missing ondelete; Law 22: FK column approved_by_id missing ondelete

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | payments |
| Law 9: Naming (snake_case, plural) | PASS | refunds |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | FAIL | Missing ondelete on FK |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PaymentIntent (payment_intents)

- **File**: `backend/domains\payments\models\payment_models.py`
- **Schema**: payments
- **Tablename**: `payment_intents`
- **Columns**: id, is_deleted, version, order_id, user_id, country_code, amount, currency, provider, provider_intent_id, status, client_secret, finance_payment_id, metadata_json, expires_at, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | payments |
| Law 9: Naming (snake_case, plural) | PASS | payment_intents |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### CouponUsage (coupon_usages)

- **File**: `backend/domains\promotions\models\coupon_usage.py`
- **Schema**: promotions
- **Tablename**: `coupon_usages`
- **Columns**: id, coupon_id, user_id, order_id, country_code, created_at, updated_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | promotions |
| Law 9: Naming (snake_case, plural) | PASS | coupon_usages |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### UserPoints (user_points)

- **File**: `backend/domains\promotions\models\loyalty_points.py`
- **Schema**: promotions
- **Tablename**: `user_points`
- **Columns**: id, user_id, balance, lifetime_earned, lifetime_redeemed, loyalty_tier, points_expire_at, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | promotions |
| Law 9: Naming (snake_case, plural) | PASS | user_points |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PointsTransaction (points_transactions)

- **File**: `backend/domains\promotions\models\loyalty_points.py`
- **Schema**: promotions
- **Tablename**: `points_transactions`
- **Columns**: id, user_id, points, transaction_type, order_id, source_description, balance_after, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | promotions |
| Law 9: Naming (snake_case, plural) | PASS | points_transactions |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PromotionEngineConfig (promotion_engine_configs)

- **File**: `backend/domains\promotions\models\promotion_config.py`
- **Schema**: promotions
- **Tablename**: `promotion_engine_configs`
- **Columns**: id, country_code, engine_enabled, allow_product_coupons, allow_category_coupons, allow_order_tier_discounts, allow_referral_rewards, allow_supplier_promotions, allow_global_coupons, stacking_mode, max_combined_discount_percent, max_combined_discount_amount, show_savings_line_item, tier_discount_visible, points_per_omr, referral_referrer_points, referral_referee_points, points_expiry_months, referral_monthly_cap, referral_verification_delay_days, min_points_redeem, allow_partial_points_redemption, created_at, updated_at, is_deleted, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | promotions |
| Law 9: Naming (snake_case, plural) | PASS | promotion_engine_configs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### PromotionLedgerEntry (promotion_ledger_entries)

- **File**: `backend/domains\promotions\models\promotion_ledger.py`
- **Schema**: promotions
- **Tablename**: `promotion_ledger_entries`
- **Columns**: id, promotion_id, order_id, user_id, promotion_type, promotion_code, tier_id, amount, entry_type, discount_amount, points_awarded, points_redeemed, stacking_flag, source, metadata_json, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | promotions |
| Law 9: Naming (snake_case, plural) | PASS | promotion_ledger_entries |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Coupon (coupons)

- **File**: `backend/domains\promotions\models\promotions.py`
- **Schema**: promotions
- **Tablename**: `coupons`
- **Columns**: id, code, discount_type, discount_value, minimum_order, maximum_discount, usage_limit, usage_count, starts_at, expires_at, is_active, is_deleted, deleted_at, deleted_by_id, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | promotions |
| Law 9: Naming (snake_case, plural) | PASS | coupons |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### Banner (banners)

- **File**: `backend/domains\promotions\models\promotions.py`
- **Schema**: promotions
- **Tablename**: `banners`
- **Columns**: id, title, subtitle, image_url, link, banner_type, is_active, is_deleted, deleted_at, deleted_by_id, sort_order, bg_color, text_color, subtitle_color, btn_bg_color, btn_text_color, badge_text, badge_color, effect, video_url, cta_label, cta_url, starts_at, ends_at, created_by_id, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | promotions |
| Law 9: Naming (snake_case, plural) | PASS | banners |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### BOGOPromotion (bogo_promotions)

- **File**: `backend/domains\promotions\models\promotions.py`
- **Schema**: promotions
- **Tablename**: `bogo_promotions`
- **Columns**: id, title, description, buy_quantity, free_quantity, free_discount_pct, apply_to, target_id, max_uses_per_customer, stacking_allowed, is_active, starts_at, ends_at, country_code, created_at, updated_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | promotions |
| Law 9: Naming (snake_case, plural) | PASS | bogo_promotions |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### FlashSale (flash_sales)

- **File**: `backend/domains\promotions\models\promotions.py`
- **Schema**: promotions
- **Tablename**: `flash_sales`
- **Columns**: id, title, description, starts_at, ends_at, discount_pct, is_active, is_deleted, deleted_at, deleted_by_id, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | promotions |
| Law 9: Naming (snake_case, plural) | PASS | flash_sales |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### FraudEvent (fraud_events)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `fraud_events`
- **Columns**: id, user_id, order_id, event_type, ip_address, device_hash, session_id, fraud_score, triggered_rules, details, is_flagged, status_code, reviewed_by_id, reviewed_at, is_deleted, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 20: Missing required column: updated_at; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | fraud_events |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### FraudBlacklist (fraud_blacklists)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `fraud_blacklists`
- **Columns**: id, identifier_type, identifier_value, identifier_value_hash, reason, is_active, status_code, created_at, is_deleted, expires_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 20: Missing required column: updated_at; Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | fraud_blacklists |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### FraudRule (fraud_rules)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `fraud_rules`
- **Columns**: id, rule_key, name, description, weight, condition_json, action, is_active, is_global, country_code, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | fraud_rules |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### ManualReviewQueue (manual_review_queues)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `manual_review_queues`
- **Columns**: id, entity_type, entity_id, fraud_score, triggered_rules, reason, priority, assigned_to_id, admin_notes, status_code, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | manual_review_queues |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### IPReputation (ip_reputations)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `ip_reputations`
- **Columns**: id, ip_address, reputation_score, is_blocked, is_proxy, is_tor, is_vpn, is_hosting, asn, country_code, last_seen_at, updated_at, created_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: updated_at missing server_default=func.now(); Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | ip_reputations |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### DeviceFingerprint (device_fingerprints)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `device_fingerprints`
- **Columns**: id, user_id, fingerprint_hash, user_agent, ip_addresses, is_trusted, is_blocked, risk_score, headless_attempts, account_count, first_seen_at, last_seen_at, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 19: Missing required column: created_at; Law 20: Missing required column: updated_at; Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | device_fingerprints |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | FAIL | MISSING |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### CreditCardBin (credit_card_bins)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `credit_card_bins`
- **Columns**: id, bin, brand, bank, country, is_blacklisted, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | credit_card_bins |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### ReturnAbusePattern (return_abuse_patterns)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `return_abuse_patterns`
- **Columns**: id, user_id, abuse_type, occurrence_count, first_occurrence, last_occurrence, is_blocked, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 19: Missing required column: created_at; Law 20: Missing required column: updated_at; Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | return_abuse_patterns |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | FAIL | MISSING |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### LogisticsFraudIndicator (logistics_fraud_indicators)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `logistics_fraud_indicators`
- **Columns**: id, partner_id, indicator_type, value, is_active, is_deleted, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 20: Missing required column: updated_at; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | logistics_fraud_indicators |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### FraudAlert (fraud_alerts)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `fraud_alerts`
- **Columns**: id, alert_type, entity_type, entity_id, fraud_score, triggered_rules, priority, details, is_resolved, resolved_at, is_deleted, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 20: Missing required column: updated_at; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | fraud_alerts |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### IPAccountLinkage (ip_account_linkages)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `ip_account_linkages`
- **Columns**: id, ip_address, user_id, device_fingerprint, session_id, interaction_count, is_suspicious, last_seen, is_deleted
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 19: Missing required column: created_at; Law 20: Missing required column: updated_at; Law 21: Missing required column: country_code

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | ip_account_linkages |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | FAIL | MISSING |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### VelocityCounter (fraud_velocity_counters)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `fraud_velocity_counters`
- **Columns**: id, key, count, window_start, window_end, entity_type, entity_id, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | fraud_velocity_counters |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### FraudScoringLog (fraud_scoring_logs)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `fraud_scoring_logs`
- **Columns**: id, event_type, user_id, order_id, ip_address, device_hash, session_id, raw_score, triggered_rules, metadata_json, action_taken, is_deleted, created_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 20: Missing required column: updated_at; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | fraud_scoring_logs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### FraudCase (fraud_cases)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `fraud_cases`
- **Columns**: id, case_number, title, description, fraud_score, priority, status_code, entity_type, entity_id, assigned_to_id, created_by_id, resolved_at, resolution_notes, is_deleted, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | fraud_cases |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### FraudCaseAssignment (fraud_case_assignments)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `fraud_case_assignments`
- **Columns**: id, case_id, assigned_to_id, assigned_by_id, role_at_assignment, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | fraud_case_assignments |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### DLPViolation (dlp_violations)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `dlp_violations`
- **Columns**: id, violation_type, severity, sender_id, recipient_email, detected_content, action_taken, status_code, reviewed_by_id, reviewed_at, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | dlp_violations |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### MeetingTranscript (meeting_transcripts)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `meeting_transcripts`
- **Columns**: id, room_id, language, segments, action_items, summary, word_count, duration_seconds, is_deleted, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | meeting_transcripts |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### MeetingActionItem (meeting_action_items)

- **File**: `backend/domains\security\models\fraud.py`
- **Schema**: security
- **Tablename**: `meeting_action_items`
- **Columns**: id, meeting_id, entity_type, entity_id, action, metadata_json, status_code, assigned_to_id, is_deleted, created_at, due_date
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 20: Missing required column: updated_at; Law 21: Missing required column: country_code; Law 19: created_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | meeting_action_items |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | FAIL | MISSING |
| Required: is_deleted | PASS | Present |

### AlertEscalationRule (alert_escalation_rules)

- **File**: `backend/domains\security\models\security_schema_models.py`
- **Schema**: security
- **Tablename**: `alert_escalation_rules`
- **Columns**: id, alert_type, severity, threshold_value, current_tier, is_active, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 22: FK column country_code missing ondelete

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | alert_escalation_rules |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | FAIL | Missing ondelete on FK |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### DocumentVerification (document_verifications)

- **File**: `backend/domains\security\models\security_schema_models.py`
- **Schema**: security
- **Tablename**: `document_verifications`
- **Columns**: id, pipeline_id, document_type, document_data, status, verified_at, verifier_id, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 22: FK column country_code missing ondelete

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | document_verifications |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | FAIL | Missing ondelete on FK |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### KYCVerification (kyc_verifications)

- **File**: `backend/domains\security\models\security_schema_models.py`
- **Schema**: security
- **Tablename**: `kyc_verifications`
- **Columns**: id, user_id, status, provider, verification_data, document_types, submitted_at, reviewed_at, reviewer_id, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 22: FK column country_code missing ondelete

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | security |
| Law 9: Naming (snake_case, plural) | PASS | kyc_verifications |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | FAIL | Missing ondelete on FK |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SupplierFraudIndicator (supplier_fraud_indicators)

- **File**: `backend/domains\suppliers\models\fraud_indicators.py`
- **Schema**: suppliers
- **Tablename**: `supplier_fraud_indicators`
- **Columns**: id, supplier_id, indicator_type, value, is_active, is_deleted, country_code, created_at, updated_at
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: None

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | suppliers |
| Law 9: Naming (snake_case, plural) | PASS | supplier_fraud_indicators |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SupplierBadgeCatalog (supplier_badge_catalogs)

- **File**: `backend/domains\suppliers\models\suppliers.py`
- **Schema**: suppliers
- **Tablename**: `supplier_badge_catalogs`
- **Columns**: uuid, version, is_deleted, deleted_at, id, name, badge_level, description, benefits, price, currency, validity_days, is_active, credibility_weight, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | suppliers |
| Law 9: Naming (snake_case, plural) | PASS | supplier_badge_catalogs |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SupplierBadge (supplier_badges)

- **File**: `backend/domains\suppliers\models\suppliers.py`
- **Schema**: suppliers
- **Tablename**: `supplier_badges`
- **Columns**: uuid, version, is_deleted, deleted_at, id, supplier_id, catalog_id, badge_name, badge_level, status, issued_at, expires_at, assigned_by, billing_reference, credibility_weight, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | suppliers |
| Law 9: Naming (snake_case, plural) | PASS | supplier_badges |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SupplierBadgeBillingHistory (supplier_badge_billing_histories)

- **File**: `backend/domains\suppliers\models\suppliers.py`
- **Schema**: suppliers
- **Tablename**: `supplier_badge_billing_histories`
- **Columns**: uuid, version, is_deleted, deleted_at, id, supplier_id, badge_id, catalog_id, billing_reference, charge_type, amount, currency, status, period_start, period_end, due_at, billed_at, paid_at, payment_method, notes, created_at, updated_at, country_code
- **Status**: NEW
- **Project Completion Blocker**: no
- **Issues**: Law 19: created_at missing server_default=func.now(); Law 19: updated_at missing server_default=func.now()

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | suppliers |
| Law 9: Naming (snake_case, plural) | PASS | supplier_badge_billing_histories |
| Law 19: Timestamps server_default | FAIL | Missing server_default on timestamps |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | PASS | Present |
| Required: country_code | PASS | Present |
| Required: is_deleted | PASS | Present |

### SupplierDispute (supplier_disputes)

- **File**: `backend/domains\suppliers\models\suppliers.py`
- **Schema**: suppliers
- **Tablename**: `supplier_disputes`
- **Columns**: id, supplier_id, order_id, reason, status, country_code, created_at
- **Status**: NEW
- **Project Completion Blocker**: yes
- **Issues**: Law 20: Missing required column: updated_at; Law 22: Missing required column: is_deleted

#### Detailed Checks

| Check | Status | Details |
|-------|--------|---------|
| Law 6: Schema declared | PASS | suppliers |
| Law 9: Naming (snake_case, plural) | PASS | supplier_disputes |
| Law 19: Timestamps server_default | PASS | All timestamps have server_default |
| Law 20: No Float on money fields | PASS | No Float money fields |
| Law 21: country_code String(2) | PASS | All country_code fields are String(2) |
| Law 22: FK ondelete present | PASS | All FK columns have ondelete |
| Law 23: is_deleted boolean default false | PASS | is_deleted properly defined |
| Law 24: No duplicate tablename | PASS | Unique tablename |
| Required: created_at | PASS | Present |
| Required: updated_at | FAIL | MISSING |
| Required: country_code | PASS | Present |
| Required: is_deleted | FAIL | MISSING |
