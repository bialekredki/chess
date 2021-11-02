"""empty message

Revision ID: 493a1345ab75
Revises: 7569d9904914
Create Date: 2021-11-01 11:58:10.057507

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '493a1345ab75'
down_revision = '7569d9904914'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chess_board_theme',
    sa.Column('name', sa.String(length=32), nullable=False),
    sa.Column('piece_set', sa.String(length=32), nullable=True),
    sa.Column('black_tile_colour', sa.Integer(), nullable=True),
    sa.Column('white_tile_colour', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('name')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('chess_board_theme')
    # ### end Alembic commands ###
