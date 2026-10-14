"""add_users_and_case_user_id

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-14 22:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'users' not in tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('hashed_password', sa.String(length=255), nullable=False),
            sa.Column('full_name', sa.String(length=255), nullable=True),
            sa.Column('role', sa.String(length=32), nullable=False, server_default='patient'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
        )
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)

    cases_columns = [col['name'] for col in inspector.get_columns('cases')]
    if 'user_id' not in cases_columns:
        with op.batch_alter_table('cases', schema=None) as batch_op:
            batch_op.add_column(sa.Column('user_id', sa.Uuid(), nullable=True))
            batch_op.create_index(batch_op.f('ix_cases_user_id'), ['user_id'], unique=False)
            batch_op.create_foreign_key(
                batch_op.f('fk_cases_user_id_users'),
                'users',
                ['user_id'],
                ['id'],
                ondelete='SET NULL'
            )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cases_columns = [col['name'] for col in inspector.get_columns('cases')]
    if 'user_id' in cases_columns:
        with op.batch_alter_table('cases', schema=None) as batch_op:
            batch_op.drop_constraint(batch_op.f('fk_cases_user_id_users'), type_='foreignkey')
            batch_op.drop_index(batch_op.f('ix_cases_user_id'))
            batch_op.drop_column('user_id')

    tables = inspector.get_table_names()
    if 'users' in tables:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_users_email'))
        op.drop_table('users')
