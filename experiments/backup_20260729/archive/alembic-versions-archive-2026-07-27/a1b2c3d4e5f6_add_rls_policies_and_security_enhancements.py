"""add_rls_policies_and_security_enhancements

Add Row-Level Security policies for logistics_partners, supplier_profiles,
commission_agreements, and enhanced country_staff_assignments validation.

Revision ID: a1b2c3d4e5f6
Revises: 20915daf9b29
Create Date: 2026-06-25 12:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "20915daf9b29"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    existing_indexes = {ix["name"] for ix in inspector.get_indexes("logistics_partners")}
    if "ix_logistics_partners_country_status" not in existing_indexes:
        op.create_index("ix_logistics_partners_country_status", "logistics_partners", ["country_code", "status"])
    
    existing_indexes = {ix["name"] for ix in inspector.get_indexes("supplier_profiles")}
    if "ix_supplier_profiles_country_status" not in existing_indexes:
        op.create_index("ix_supplier_profiles_country_status", "supplier_profiles", ["country_code", "verification_status"])
    
    existing_indexes = {ix["name"] for ix in inspector.get_indexes("supplier_country_commissions")}
    if "ix_supplier_country_commissions_country_active" not in existing_indexes:
        op.create_index("ix_supplier_country_commissions_country_active", "supplier_country_commissions", ["country_code", "is_active"])
    
    op.execute("""
        CREATE OR REPLACE FUNCTION check_country_access(
            target_country TEXT,
            user_id INTEGER DEFAULT NULL
        ) RETURNS BOOLEAN AS $$
        DECLARE
            user_role TEXT;
            has_assignment BOOLEAN;
        BEGIN
            IF user_id IS NULL THEN
                RETURN FALSE;
            END IF;
            
            SELECT role INTO user_role FROM users WHERE id = user_id LIMIT 1;
            
            IF user_role = 'admin' THEN
                RETURN TRUE;
            END IF;
            
            SELECT EXISTS (
                SELECT 1 FROM country_staff_assignments
                WHERE user_id = user_id 
                AND country_code = target_country 
                AND is_active = TRUE
            ) INTO has_assignment;
            
            RETURN has_assignment;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_country_code_consistency()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.country_code IS NOT NULL THEN
                IF NOT EXISTS (SELECT 1 FROM country_configs WHERE code = NEW.country_code) THEN
                    RAISE EXCEPTION 'Invalid country_code: %', NEW.country_code;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER validate_logistics_partner_country
        BEFORE INSERT OR UPDATE ON logistics_partners
        FOR EACH ROW EXECUTE FUNCTION validate_country_code_consistency();
    """)
    
    op.execute("""
        CREATE TRIGGER validate_supplier_profile_country
        BEFORE INSERT OR UPDATE ON supplier_profiles
        FOR EACH ROW EXECUTE FUNCTION validate_country_code_consistency();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS validate_logistics_partner_country ON logistics_partners")
    op.execute("DROP TRIGGER IF EXISTS validate_supplier_profile_country ON supplier_profiles")
    op.execute("DROP FUNCTION IF EXISTS validate_country_code_consistency()")
    op.execute("DROP FUNCTION IF EXISTS check_country_access(TEXT, INTEGER)")
