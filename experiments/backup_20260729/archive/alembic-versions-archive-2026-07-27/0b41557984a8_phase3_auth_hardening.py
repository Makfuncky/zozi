"""phase3_auth_hardening

Revision ID: 0b41557984a8
Revises: 5ca199ab0c03
Create Date: 2026-03-02 22:57:19.164773

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '0b41557984a8'
down_revision: Union[str, Sequence[str], None] = '5ca199ab0c03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'users' not in inspector.get_table_names():
        return
    existing_columns = {column['name'] for column in inspector.get_columns('users')}

    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'profile_image' not in existing_columns:
            batch_op.add_column(sa.Column('profile_image', sa.String(), nullable=True))
        if 'address_book' not in existing_columns:
            batch_op.add_column(sa.Column('address_book', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'users' not in inspector.get_table_names():
        return
    existing_columns = {column['name'] for column in inspector.get_columns('users')}

    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'address_book' in existing_columns:
            batch_op.drop_column('address_book')
        if 'profile_image' in existing_columns:
            batch_op.drop_column('profile_image')

