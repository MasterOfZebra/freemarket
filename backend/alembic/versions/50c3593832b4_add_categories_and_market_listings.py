"""add categories and market listings

Revision ID: 50c3593832b4
Revises:
Create Date: 2025-10-20 18:45:23.095363

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '50c3593832b4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Безопасное создание типов
    conn.execute(text("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'listingsection') THEN
            CREATE TYPE listingsection AS ENUM ('wants', 'offers');
        END IF;
    END
    $$;
    """))

    conn.execute(text("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'listingstatus') THEN
            CREATE TYPE listingstatus AS ENUM ('active', 'archived');
        END IF;
    END
    $$;
    """))

    # Теперь указываем create_type=False, чтобы SQLAlchemy не пытался создать их повторно
    listing_section_enum = sa.Enum('wants', 'offers', name='listingsection', create_type=False)
    listing_status_enum = sa.Enum('active', 'archived', name='listingstatus', create_type=False)

    # Таблица категорий
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('section', sa.String(), nullable=False),  # Временно как String
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id']),
        sa.UniqueConstraint('section', 'parent_id', 'slug', name='uq_category_section_parent_slug')
    )
    op.create_index('ix_category_section_parent', 'categories', ['section', 'parent_id'])

    # Таблица объявлений
    op.create_table(
        'market_listings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('type', sa.String(), nullable=False),  # Временно как String
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('subcategory_id', sa.Integer(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('contact', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False), # Временно как String
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.ForeignKeyConstraint(['subcategory_id'], ['categories.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )
    op.create_index('ix_market_listing_type_category_status', 'market_listings', ['type', 'category_id', 'status'])
    op.create_index('ix_market_listing_created_desc', 'market_listings', ['created_at', 'status'])

    # Теперь меняем тип колонок на ENUM через ALTER TABLE
    op.execute("ALTER TABLE categories ALTER COLUMN section TYPE listingsection USING section::listingsection")
    op.execute("ALTER TABLE market_listings ALTER COLUMN type TYPE listingsection USING type::listingsection")
    op.execute("ALTER TABLE market_listings ALTER COLUMN status TYPE listingstatus USING status::listingstatus")
    op.execute("ALTER TABLE market_listings ALTER COLUMN status SET DEFAULT 'active'")


def downgrade() -> None:
    op.drop_index('ix_market_listing_created_desc', table_name='market_listings')
    op.drop_index('ix_market_listing_type_category_status', table_name='market_listings')
    op.drop_table('market_listings')

    op.drop_index('ix_category_section_parent', table_name='categories')
    op.drop_table('categories')

    conn = op.get_bind()
    conn.execute(text("""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'listingstatus') THEN
            DROP TYPE listingstatus;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'listingsection') THEN
            DROP TYPE listingsection;
        END IF;
    END
    $$;
    """))
