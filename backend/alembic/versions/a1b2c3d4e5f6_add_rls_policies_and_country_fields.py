"""Migration to add RLS policies and country_code fields for logistic/supplier/commission tables."""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6_add_rls_policies_and_country_fields'
down_revision = 'b2c3d4e5f6g7_add_employee_hcm_models'
branch_labels = None
depends_on = None


def upgrade():
    # Add country_code to LogisticsPartner
    op.add_column('logistics_partners', sa.Column('country_code', sa.String(10), nullable=True))
    op.create_foreign_key('fk_logistics_partners_country', 'logistics_partners', 'country_configs', ['country_code'], ['code'], ondelete='SET NULL')
    op.create_index('ix_logistics_partners_country', 'logistics_partners', ['country_code'])
    
    # Add country_code to SupplierProfile
    op.add_column('supplier_profiles', sa.Column('country_code', sa.String(10), nullable=True))
    op.create_foreign_key('fk_supplier_profiles_country', 'supplier_profiles', 'country_configs', ['country_code'], ['code'], ondelete='SET NULL')
    op.create_index('ix_supplier_profiles_country', 'supplier_profiles', ['country_code'])
    
    # Add country_code to CommissionAgreement
    op.add_column('commission_agreements', sa.Column('country_code', sa.String(10), nullable=True))
    op.create_foreign_key('fk_commission_agreements_country', 'commission_agreements', 'country_configs', ['country_code'], ['code'], ondelete='SET NULL')
    op.create_index('ix_commission_agreements_country', 'commission_agreements', ['country_code'])
    
    # Add country_code to LogisticsPartnerPayout
    op.add_column('logistics_partner_payouts', sa.Column('country_code', sa.String(10), nullable=True))
    op.create_foreign_key('fk_logistics_partner_payouts_country', 'logistics_partner_payouts', 'country_configs', ['country_code'], ['code'], ondelete='SET NULL')
    
    # Add country_code to Payout (supplier payouts)
    op.add_column('payouts', sa.Column('country_code', sa.String(10), nullable=True))
    op.create_foreign_key('fk_payouts_country', 'payouts', 'country_configs', ['country_code'], ['code'], ondelete='SET NULL')
    
    # Create RLS policy function
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


def downgrade():
    op.execute("DROP POLICY IF EXISTS 'Users can view logistics partners in accessible countries' ON logistics_partners;")
    op.execute("DROP POLICY IF EXISTS 'Users can view suppliers in accessible countries' ON supplier_profiles;")
    op.execute("DROP POLICY IF EXISTS 'Users can view commission agreements in accessible countries' ON commission_agreements;")
    op.execute("DROP POLICY IF EXISTS 'Users can view payouts in accessible countries' ON payouts;")
    
    op.execute("ALTER TABLE logistics_partners DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE supplier_profiles DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE commission_agreements DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE logistics_partner_payouts DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE payouts DISABLE ROW LEVEL SECURITY;")
    
    op.execute("DROP FUNCTION IF EXISTS auth.country_access_check(TEXT);")
    
    op.drop_column('payouts', 'country_code')
    op.drop_column('logistics_partner_payouts', 'country_code')
    op.drop_column('commission_agreements', 'country_code')
    op.drop_constraint('fk_supplier_profiles_country', 'supplier_profiles', type_='foreignkey')
    op.drop_column('supplier_profiles', 'country_code')
    op.drop_constraint('fk_logistics_partners_country', 'logistics_partners', type_='foreignkey')
    op.drop_column('logistics_partners', 'country_code')
