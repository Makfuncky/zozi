"""add_materialized_views_for_tier4_analytics

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-06-24 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 's_c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create materialized view for supplier health scores
    op.execute("""
        CREATE MATERIALIZED VIEW supplier_health_scores AS
        SELECT 
            s.id as supplier_id,
            s.name as supplier_name,
            -- Calculate fulfillment rate (orders delivered on time / total orders)
            COALESCE(
                (SELECT COUNT(*) 
                 FROM orders o 
                 JOIN shipments sh ON o.id = sh.order_id 
                 WHERE o.supplier_id = s.id 
                   AND sh.status = 'delivered' 
                   AND sh.actual_delivery <= sh.estimated_delivery
                   AND o.created_at >= datetime('now', '-90 days')),
                0) / NULLIF(
                    (SELECT COUNT(*) 
                     FROM orders o 
                     JOIN shipments sh ON o.id = sh.order_id 
                     WHERE o.supplier_id = s.id 
                       AND sh.status IN ('delivered', 'shipped', 'in_transit')
                       AND o.created_at >= datetime('now', '-90 days')), 0
                ) * 100 as fulfillment_rate_percent,
            
            -- Calculate return rate (returned items / total items sold)
            COALESCE(
                (SELECT COUNT(*) 
                 FROM return_requests rr 
                 JOIN order_items oi ON rr.order_item_id = oi.id 
                 JOIN orders o ON oi.order_id = o.id 
                 WHERE o.supplier_id = s.id 
                   AND rr.status IN ('approved', 'completed')
                   AND o.created_at >= datetime('now', '-90 days')), 0)::FLOAT /
                NULLIF(
                    (SELECT SUM(oi.quantity) 
                     FROM order_items oi 
                     JOIN orders o ON oi.order_id = o.id 
                     WHERE o.supplier_id = s.id 
                       AND o.created_at >= datetime('now', '-90 days')), 0
                ) * 100 as return_rate_percent,
            
            -- Average rating from reviews
            COALESCE(
                (SELECT AVG(r.rating) 
                 FROM reviews r 
                 JOIN products p ON r.product_id = p.id 
                 WHERE p.supplier_id = s.id
                   AND r.created_at >= datetime('now', '-90 days')), 0) as avg_rating,
            
            -- Response time to customer inquiries (hours - simplified calculation)
            COALESCE(
                (SELECT AVG(
                    strftime('%s', CASE 
                        WHEN r.responded_at IS NOT NULL THEN r.responded_at 
                        ELSE datetime('now') 
                        END
                    ) - strftime('%s', 
                        CASE 
                            WHEN r.created_at IS NOT NULL THEN r.created_at 
                            ELSE datetime('now') 
                            END
                    )) / 3600.0
                 FROM support_tickets r
                 WHERE r.related_entity_type = 'product'
                   AND (SELECT p.supplier_id FROM products p WHERE p.id = r.related_entity_id) = s.id
                   AND r.responded_at IS NOT NULL
                   AND r.created_at >= datetime('now', '-90 days')), 0) as avg_response_time_hours,
            
            -- Overall health score (weighted average)
            (
                COALESCE(
                    (SELECT COUNT(*) 
                     FROM orders o 
                     JOIN shipments sh ON o.id = sh.order_id 
                     WHERE o.supplier_id = s.id 
                       AND sh.status = 'delivered' 
                       AND sh.actual_delivery <= sh.estimated_delivery
                       AND o.created_at >= datetime('now', '-90 days')), 0) / NULLIF(
                    (SELECT COUNT(*) 
                     FROM orders o 
                     JOIN shipments sh ON o.id = sh.order_id 
                     WHERE o.supplier_id = s.id 
                       AND sh.status IN ('delivered', 'shipped', 'in_transit')
                       AND o.created_at >= datetime('now', '-90 days')), 0
                ) * 0.4 +  -- 40% weight for fulfillment
                
                (100 - COALESCE(
                    (SELECT COUNT(*) 
                     FROM return_requests rr 
                     JOIN order_items oi ON rr.order_item_id = oi.id 
                     JOIN orders o ON oi.order_id = o.id 
                     WHERE o.supplier_id = s.id 
                       AND rr.status IN ('approved', 'completed')
                       AND o.created_at >= datetime('now', '-90 days')), 0)::FLOAT /
                NULLIF(
                    (SELECT SUM(oi.quantity) 
                     FROM order_items oi 
                     JOIN orders o ON oi.order_id = o.id 
                     WHERE o.supplier_id = s.id 
                       AND o.created_at >= datetime('now', '-90 days')), 0
                ) * 100) * 0.3 +  -- 30% weight for returns (inverted)
                
                COALESCE(
                    (SELECT AVG(r.rating) * 20  -- Convert 1-5 scale to 0-100
                     FROM reviews r 
                     JOIN products p ON r.product_id = p.id 
                     WHERE p.supplier_id = s.id
                       AND r.created_at >= datetime('now', '-90 days')), 0) * 0.3  -- 30% weight for reviews
            ) as health_score,
            
            -- Last updated timestamp
            datetime('now') as last_updated
            
        FROM users s
        WHERE s.role = 'supplier'
          AND s.is_active = true
    """)
    
    # Create unique index on supplier_id
    op.execute("CREATE UNIQUE INDEX ix_supplier_health_scores_supplier_id ON supplier_health_scores (supplier_id)")
    
    # Create materialized view for logistics SLA performance
    op.execute("""
        CREATE MATERIALIZED VIEW logistics_sla_performance AS
        SELECT 
            lp.id as partner_id,
            lp.name as partner_name,
            lp.code as partner_code,
            -- On-time delivery percentage
            COALESCE(
                (SELECT COUNT(*) 
                 FROM shipments sh 
                 WHERE sh.assigned_partner_id = lp.id
                   AND sh.status = 'delivered'
                   AND sh.actual_delivery <= sh.estimated_delivery
                   AND sh.actual_delivery >= datetime('now', '-30 days')), 0) / NULLIF(
                    (SELECT COUNT(*) 
                     FROM shipments sh 
                     WHERE sh.assigned_partner_id = lp.id
                       AND sh.status = 'delivered'
                       AND sh.actual_delivery >= datetime('now', '-30 days')), 0
                ) * 100 as on_time_delivery_percent,
            
            -- Average delay for late deliveries (hours - simplified calculation)
            COALESCE(
                (SELECT AVG(
                    strftime('%s', CASE 
                        WHEN sh.actual_delivery IS NOT NULL THEN sh.actual_delivery 
                        ELSE datetime('now') 
                        END
                    ) - strftime('%s', 
                        CASE 
                            WHEN sh.estimated_delivery IS NOT NULL THEN sh.estimated_delivery 
                            ELSE datetime('now') 
                            END
                    )) / 3600.0
                 FROM shipments sh 
                 WHERE sh.assigned_partner_id = lp.id
                   AND sh.status = 'delivered'
                   AND sh.actual_delivery > sh.estimated_delivery
                   AND sh.actual_delivery >= datetime('now', '-30 days')), 0) as avg_delay_hours,
            
            -- Pickup timeliness percentage
            COALESCE(
                (SELECT COUNT(*) 
                 FROM shipments sh 
                 WHERE sh.assigned_partner_id = lp.id
                   AND sh.status IN ('picked_up', 'in_transit', 'delivered')
                   AND sh.picked_at <= sh.scheduled_pickup
                   AND sh.created_at >= datetime('now', '-30 days')), 0) / NULLIF(
                    (SELECT COUNT(*) 
                     FROM shipments sh 
                     WHERE sh.assigned_partner_id = lp.id
                       AND sh.status IN ('picked_up', 'in_transit', 'delivered')
                       AND sh.created_at >= datetime('now', '-30 days')), 0
                ) * 100 as pickup_timeliness_percent,
            
            -- Overall SLA score
            (
                COALESCE(
                    (SELECT COUNT(*) 
                     FROM shipments sh 
                     WHERE sh.assigned_partner_id = lp.id
                       AND sh.status = 'delivered'
                       AND sh.actual_delivery <= sh.estimated_delivery
                       AND sh.actual_delivery >= datetime('now', '-30 days')), 0) / NULLIF(
                    (SELECT COUNT(*) 
                     FROM shipments sh 
                     WHERE sh.assigned_partner_id = lp.id
                       AND sh.status = 'delivered'
                       AND sh.actual_delivery >= datetime('now', '-30 days')), 0
                ) * 0.5 +  -- 50% weight for delivery timeliness
                
                (100 - COALESCE(
                    (SELECT AVG(
                        strftime('%s', CASE 
                            WHEN sh.actual_delivery IS NOT NULL THEN sh.actual_delivery 
                            ELSE datetime('now') 
                            END
                        ) - strftime('%s', 
                            CASE 
                                WHEN sh.estimated_delivery IS NOT NULL THEN sh.estimated_delivery 
                                ELSE datetime('now') 
                                END
                        )) / 3600.0
                     FROM shipments sh 
                     WHERE sh.assigned_partner_id = lp.id
                       AND sh.status = 'delivered'
                       AND sh.actual_delivery > sh.estimated_delivery
                       AND sh.actual_delivery >= datetime('now', '-30 days')), 0) * 2  -- Cap at 50 hours max delay for scoring
                ) * 0.3 +  -- 30% weight for delay severity (inverted and scaled)
                
                COALESCE(
                    (SELECT COUNT(*) 
                     FROM shipments sh 
                     WHERE sh.assigned_partner_id = lp.id
                       AND sh.status IN ('picked_up', 'in_transit', 'delivered')
                       AND sh.picked_at <= sh.scheduled_pickup
                       AND sh.created_at >= datetime('now', '-30 days')), 0) / NULLIF(
                    (SELECT COUNT(*) 
                     FROM shipments sh 
                     WHERE sh.assigned_partner_id = lp.id
                       AND sh.status IN ('picked_up', 'in_transit', 'delivered')
                       AND sh.created_at >= datetime('now', '-30 days')), 0
                ) * 0.2  -- 20% weight for pickup timeliness
            ) as sla_score,
            
            -- Total shipments in period
            (SELECT COUNT(*) 
             FROM shipments sh 
             WHERE sh.assigned_partner_id = lp.id
               AND sh.created_at >= datetime('now', '-30 days')) as total_shipments_30d,
            
            -- Last updated timestamp
            datetime('now') as last_updated
            
        FROM logistics_partners lp
        WHERE lp.is_active = true
          AND lp.verification_status = 'approved'
    """)
    
    # Create unique index on partner_id
    op.execute("CREATE UNIQUE INDEX ix_logistics_sla_performance_partner_id ON logistics_sla_performance (partner_id)")


def downgrade() -> None:
    # Drop materialized views
    op.execute("DROP MATERIALIZED VIEW IF EXISTS logistics_sla_performance")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS supplier_health_scores")

