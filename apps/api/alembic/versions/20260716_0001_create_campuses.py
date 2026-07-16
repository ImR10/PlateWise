"""Create campuses table.

Revision ID: 20260716_0001
Revises:
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260716_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("slug", name="uq_campuses_slug"),
    )
    op.create_index("ix_campuses_name", "campuses", ["name"])


def downgrade() -> None:
    op.drop_index("ix_campuses_name", table_name="campuses")
    op.drop_table("campuses")
