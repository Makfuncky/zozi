"""add_product_minimum_stock_maximum_stock_view_count

Revision ID: d0e1f2a3b4c5
Revises: b1c8f348e2c7
Create Date: 2026-06-22 15:18:24.322447

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd0e1f2a3b4c5'
down_revision = 'b1c8f348e2c7'
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    from alembic import op as _op
    from sqlalchemy import inspect
    conn = _op.get_bind()
    inspector = inspect(conn)
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    if not _column_exists("products", "minimum_stock"):
        op.add_column("products", sa.Column("minimum_stock", sa.Integer(), nullable=True, server_default=sa.text("0")))
    if not _column_exists("products", "maximum_stock"):
        op.add_column("products", sa.Column("maximum_stock", sa.Integer(), nullable=True, server_default=sa.text("0")))
    if not _column_exists("products", "view_count"):
        op.add_column("products", sa.Column("view_count", sa.Integer(), server_default=sa.text("0"), nullable=False))


def downgrade() -> None:
    with op.batch_alter_table("products") as batch_op:
        if _column_exists("products", "view_count"):
            batch_op.drop_column("view_count")
        if _column_exists("products", "maximum_stock"):
            batch_op.drop_column("maximum_stock")
        if _column_exists("products", "minimum_stock"):
            batch_op.drop_column("minimum_stock")

