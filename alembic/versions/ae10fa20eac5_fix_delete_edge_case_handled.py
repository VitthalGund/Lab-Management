"""fix: delete edge case handled

Revision ID: ae10fa20eac5
Revises: 3eac396fd16d
Create Date: 2025-08-17 17:07:36.065428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae10fa20eac5'
down_revision: Union[str, None] = '3eac396fd16d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
