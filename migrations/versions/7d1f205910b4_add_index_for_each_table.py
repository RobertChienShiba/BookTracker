"""add index for each table

Revision ID: 7d1f205910b4
Revises: 6ec0c543a307
Create Date: 2024-10-31 04:33:28.380219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel



# revision identifiers, used by Alembic.
revision: str = '7d1f205910b4'
down_revision: Union[str, None] = '6ec0c543a307'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_books_uid'), 'books', ['uid'], unique=True)
    op.create_index(op.f('ix_reviews_uid'), 'reviews', ['uid'], unique=True)
    op.create_index(op.f('ix_tags_uid'), 'tags', ['uid'], unique=True)
    op.create_index(op.f('ix_users_uid'), 'users', ['uid'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_uid'), table_name='users')
    op.drop_index(op.f('ix_tags_uid'), table_name='tags')
    op.drop_index(op.f('ix_reviews_uid'), table_name='reviews')
    op.drop_index(op.f('ix_books_uid'), table_name='books')
    # ### end Alembic commands ###
