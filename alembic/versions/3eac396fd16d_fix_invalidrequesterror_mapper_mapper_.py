"""fix: InvalidRequestError: Mapper 'Mapper[Lab(labs)]' has no property 'teachers' 

Revision ID: 3eac396fd16d
Revises: b6c21bc597e9
Create Date: 2025-08-17 17:02:57.691831

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3eac396fd16d'
down_revision: Union[str, None] = 'b6c21bc597e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
