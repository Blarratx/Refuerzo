from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_prioridad_to_tickets"
down_revision: Union[str, Sequence[str], None] = "0001_create_tickets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ticket_priority_enum = sa.Enum("bajo", "medio", "alto", name="ticket_priority")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        ticket_priority_enum.create(bind, checkfirst=True)
    op.add_column(
        "tickets",
        sa.Column("prioridad", ticket_priority_enum, nullable=False, server_default="medio"),
    )


def downgrade() -> None:
    op.drop_column("tickets", "prioridad")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        ticket_priority_enum.drop(bind, checkfirst=True)
