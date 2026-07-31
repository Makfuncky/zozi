with open('backend/controllers/auth_controller.py', 'r') as f:
    content = f.read()

# Replace _record_referral_event calls with service function
content = content.replace('_record_referral_event(', 'record_referral_event(')

# Replace the register_user function with a version that uses service functions
old_register = '''    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password),
        role=user.role,
        phone=user.phone,
        referral_code=_generate_unique_referral_code(db),
        country_code=DEFAULT_COUNTRY,
        referred_by_user_id=_user_id(referrer) if referrer is not None else None,
        email_verified=customer_auto_verified,
    )
    db.add(db_user)
    db.flush()

    if referrer is not None and user.role == "customer":
        setattr(
            referrer,
            "referral_points",
            int(cast(int | None, getattr(referrer, "referral_points", 0)) or 0) + REFERRAL_REFERRER_BONUS,
        )
        setattr(
            db_user,
            "referral_points",
            int(cast(int | None, getattr(db_user, "referral_points", 0)) or 0) + REFERRAL_NEW_CUSTOMER_BONUS,
        )
        _record_referral_event(
            db,
            user_id=_user_id(referrer),
            event_type="referral_invite_success",
            points=REFERRAL_REFERRER_BONUS,
            channel="referral_code",
            referred_user_id=_user_id(db_user),
        )
        _record_referral_event(
            db,
            user_id=_user_id(db_user),
            event_type="referral_join_bonus",
            points=REFERRAL_NEW_CUSTOMER_BONUS,
            channel="referral_code",
            referred_user_id=_user_id(referrer),
        )

    # Create supplier business profile
    if user.role == "supplier":
        supplier_slug_base = re.sub(
            r"[^a-z0-9]+",
            "-",
            (user.business_name or user.username or f"supplier-{db_user.id}").strip().lower(),
        ).strip("-") or f"supplier-{db_user.id}"
        profile = SupplierProfile(
            user_id=db_user.id,
            business_name=user.business_name.strip() if user.business_name else None,
            slug=f"{supplier_slug_base}-{db_user.id}",
            business_type=user.business_type or "individual",
            country=user.country,
            country_code=DEFAULT_COUNTRY,
            phone_business=user.phone,
            website=user.website_url,
            is_terms_accepted=True,
            terms_version="1.0",
            verification_status="pending",
        )
        db.add(profile)

    if user.role == "logistics_partner":
        db.add(
            LogisticsPartner(
                name=f"{db_user.username} Logistics",
                code=_next_logistics_partner_code(db, cast(int, getattr(db_user, "id"))),
                contact_name=db_user.username,
                contact_email=db_user.email,
                contact_phone=db_user.phone,
                status="pending_onboarding",
                country_code=DEFAULT_COUNTRY,
                user_id=db_user.id,
            )
        )

    db.commit()
    created_user_id = cast(int, getattr(db_user, "id"))

    if require_customer_verification:
        raw_token = secrets.token_urlsafe(32)
        db.add(
            EmailVerificationToken(
                user_id=created_user_id,
                token=raw_token,
                expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=VERIFY_TOKEN_TTL_HOURS),
            )
        )
        db.commit()'''

new_register = '''    db_user = create_user(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password),
        role=user.role,
        phone=user.phone,
        referral_code=_generate_unique_referral_code(db),
        country_code=DEFAULT_COUNTRY,
        referred_by_user_id=_user_id(referrer) if referrer is not None else None,
        email_verified=customer_auto_verified,
    )

    if referrer is not None and user.role == "customer":
        update_user_referral_points(db, referrer, db_user, db_user)
        record_referral_event(
            db,
            user_id=_user_id(referrer),
            event_type="referral_invite_success",
            points=REFERRAL_REFERRER_BONUS,
            channel="referral_code",
            referred_user_id=_user_id(db_user),
        )
        record_referral_event(
            db,
            user_id=_user_id(db_user),
            event_type="referral_join_bonus",
            points=REFERRAL_NEW_CUSTOMER_BONUS,
            channel="referral_code",
            referred_user_id=_user_id(referrer),
        )

    # Create supplier business profile
    if user.role == "supplier":
        supplier_slug_base = re.sub(
            r"[^a-z0-9]+",
            "-",
            (user.business_name or user.username or f"supplier-{db_user.id}").strip().lower(),
        ).strip("-") or f"supplier-{db_user.id}"
        profile = SupplierProfile(
            user_id=db_user.id,
            business_name=user.business_name.strip() if user.business_name else None,
            slug=f"{supplier_slug_base}-{db_user.id}",
            business_type=user.business_type or "individual",
            country=user.country,
            country_code=DEFAULT_COUNTRY,
            phone_business=user.phone,
            website=user.website_url,
            is_terms_accepted=True,
            terms_version="1.0",
            verification_status="pending",
        )
        db.add(profile)
        db.commit()

    if user.role == "logistics_partner":
        db.add(
            LogisticsPartner(
                name=f"{db_user.username} Logistics",
                code=_next_logistics_partner_code(db, cast(int, getattr(db_user, "id"))),
                contact_name=db_user.username,
                contact_email=db_user.email,
                contact_phone=db_user.phone,
                status="pending_onboarding",
                country_code=DEFAULT_COUNTRY,
                user_id=db_user.id,
            )
        )
        db.commit()

    created_user_id = cast(int, getattr(db_user, "id"))

    if require_customer_verification:
        raw_token = secrets.token_urlsafe(32)
        create_email_verification_token(
            db,
            user_id=created_user_id,
            raw_token=raw_token,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=VERIFY_TOKEN_TTL_HOURS),
        )'''

content = content.replace(old_register, new_register)

with open('backend/controllers/auth_controller.py', 'w') as f:
    f.write(content)

print('Updated register_user')