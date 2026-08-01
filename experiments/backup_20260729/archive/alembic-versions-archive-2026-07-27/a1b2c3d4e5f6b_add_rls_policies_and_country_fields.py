"""Add RLS policies and country fields

Revision ID: a1b2c3d4e5f6b
Revises: a1b2c3d4e5f6
Create Date: 2026-07-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6b'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION auth.country_access_check(country_code TEXT)
        RETURNS BOOLEAN AS $$
        DECLARE
            user_role TEXT;
            user_id INTEGER;
            has_access BOOLEAN;
        BEGIN
            SELECT current_user INTO user_role;
            -- Admin has access to all countries
            IF user_role = 'admin' THEN
                RETURN TRUE;
            END IF;
            
            -- Check staff assignment
            SELECT EXISTS (
                SELECT 1 FROM country_staff_assignments
                WHERE user_id = (SELECT id FROM users WHERE email = current_user LIMIT 1)
                AND country_code = auth.country_access_check.country_code
                AND is_active = TRUE
            ) INTO has_access;
            
            RETURN has_access;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)
    
    # Apply RLS policies
    op.execute("ALTER TABLE logistics_partners ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE supplier_profiles ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE commission_agreements ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE logistics_partner_payouts ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE payouts ENABLE ROW LEVEL SECURITY;")
    
    # Create RLS policies
    op.execute("""
        CREATE POLICY "Users can view logistics partners in accessible countries"
        ON logistics_partners FOR SELECT
        USING (country_code IS NULL OR auth.country_access_check(country_code));
    """)
    op.execute("""
        CREATE POLICY "Users can view suppliers in accessible countries"
        ON supplier_profiles FOR SELECT
        USING (country_code IS NULL OR auth.country_access_check(country_code));
    """)
    op.execute("""
        CREATE POLICY "Users can view commission agreements in accessible countries"
        ON commission_agreements FOR SELECT
        USING (country_code IS NULL OR auth.country_access_check(country_code));
    """)
    op.execute("""
        CREATE POLICY "Users can view payouts in accessible countries"
        ON payouts FOR SELECT
        USING (country_code IS NULL OR auth.country_access_check(country_code));
    """)
    
    # Add country_code to respective tables
    op.add_column('logistics_partners', sa.Column('country_code', sa.String(10), nullable=True))
    op.add_column('supplier_profiles', sa.Column('country_code', sa.String(10), nullable=True))
    op.add_column('commission_agreements', sa.Column('country_code', sa.String(10), nullable=True))
    op.add_column('logistics_partner_payouts', sa.Column('country_code', sa.String(10), nullable=True))
    op.add_column('payouts', sa.Column('country_code', sa.String(10), nullable=True))
    
    # Create foreign keys
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'fk_logistics_partners_country'
            ) THEN
                ALTER TABLE logistics_partners
                ADD CONSTRAINT fk_logistics_partners_country
                FOREIGN KEY (country_code) REFERENCES country_configs(code)
                ON DELETE SET NULL;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'fk_supplier_profiles_country'
            ) THEN
                ALTER TABLE supplier_profiles
                ADD CONSTRAINT fk_supplier_profiles_country
                FOREIGN KEY (country_code) REFERENCES country_configs(code)
                ON DELETE SET NULL;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'fk_commission_agreements_country'
            ) THEN
                ALTER TABLE commission_agreements
                ADD CONSTRAINT fk_commission_agreements_country
                FOREIGN KEY (country_code) REFERENCES country_configs(code)
                ON DELETE SET NULL;
            END IF;
            
            -- Note: logistics_partner_payouts and payouts don't have foreign keys in the current schema
        END
        $$;
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS 'Users can view logistics partners in accessible countries' ON logistics_partners;")
    op.execute("DROP POLICY IF EXISTS 'Users can view suppliers in accessible countries' ON supplier_profiles;")
    op.execute("DROP POLICY IF EXISTS 'Users can view commission agreements in accessible countries' ON commission_agreements;")
    op.execute("DROP POLICY IF EXISTS 'Users can view payouts in accessible countries' ON payouts;")
    
    # Drop RLS
    op.execute("ALTER TABLE payouts DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE logistics_partner_payouts DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE commission_agreements DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE supplier_profiles DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE logistics_partners DISABLE ROW LEVEL SECURITY;")
    
    # Drop the function
    op.execute("DROP FUNCTION IF EXISTS auth.country_access_check(TEXT);")
    
    # Drop foreign keys (SQLite doesn't support dropping constraints directly, need to recreate)
    op.execute("""
        DO $$
        BEGIN
            -- Note: Foreign key dropping would be schema-specific and may not work in all cases
            -- For simplicity, we'll let them remain (SQLite doesn't support dropping FKs directly)
        END
        $$;
    """)
    
    # Drop columns
    op.drop_column('payouts', 'country_code')
    op.drop_column('logistics_partner_payouts', 'country_code')
    op.drop_column('commission_agreements', 'country_code')
    op.drop_column('supplier_profiles', 'country_code')
    op.drop_column('logistics_partners', 'country_code')
