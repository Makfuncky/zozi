"""Migration to add database triggers for country-code consistency."""
from alembic import op

revision = 'b1c2d3e4f5g6_add_country_consistency_triggers'
down_revision = 's_b1c2d3e4f5g6'
branch_labels = None
depends_on = None


def upgrade():
    # Trigger to ensure country_code consistency in logistics_partner_payouts
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_logistics_payout_country()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.country_code IS NULL THEN
                SELECT country_code INTO NEW.country_code
                FROM logistics_partners
                WHERE id = NEW.partner_id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER tr_logistics_payout_country_check
        BEFORE INSERT OR UPDATE ON logistics_partner_payouts
        FOR EACH ROW EXECUTE FUNCTION validate_logistics_payout_country();
    """)
    
    # Trigger to ensure country_code consistency in payouts (supplier)
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_supplier_payout_country()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.country_code IS NULL THEN
                SELECT sp.country_code INTO NEW.country_code
                FROM supplier_profiles sp
                JOIN users u ON sp.user_id = u.id
                WHERE u.id = NEW.supplier_id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER tr_supplier_payout_country_check
        BEFORE INSERT OR UPDATE ON payouts
        FOR EACH ROW EXECUTE FUNCTION validate_supplier_payout_country();
    """)
    
    # Trigger to ensure country_code consistency in commission_agreements
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_commission_country()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.country_code IS NULL THEN
                SELECT country_code INTO NEW.country_code
                FROM supplier_profiles sp
                JOIN users u ON sp.user_id = u.id
                WHERE u.id = NEW.supplier_id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER tr_commission_country_check
        BEFORE INSERT OR UPDATE ON commission_agreements
        FOR EACH ROW EXECUTE FUNCTION validate_commission_country();
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS tr_logistics_payout_country_check ON logistics_partner_payouts;")
    op.execute("DROP TRIGGER IF EXISTS tr_supplier_payout_country_check ON payouts;")
    op.execute("DROP TRIGGER IF EXISTS tr_commission_country_check ON commission_agreements;")
    op.execute("DROP FUNCTION IF EXISTS validate_logistics_payout_country();")
    op.execute("DROP FUNCTION IF EXISTS validate_supplier_payout_country();")
    op.execute("DROP FUNCTION IF EXISTS validate_commission_country();")

