"""empty message

Revision ID: 7badc62b4f0f
Revises: 
Create Date: 2021-11-11 13:27:08.125891

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7badc62b4f0f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('elo_user_rating',
    sa.Column('timestamp_creation', sa.DateTime(timezone=128), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('rapid', sa.Integer(), nullable=True),
    sa.Column('blitz', sa.Integer(), nullable=True),
    sa.Column('standard', sa.Integer(), nullable=True),
    sa.Column('bullet', sa.Integer(), nullable=True),
    sa.Column('puzzles', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('timestamp_creation', sa.DateTime(timezone=128), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=128), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('has_avatar', sa.Boolean(), nullable=True),
    sa.Column('last_active', sa.DateTime(timezone=128), nullable=True),
    sa.Column('is_confirmed', sa.Boolean(), nullable=True),
    sa.Column('elo', sa.Integer(), nullable=True),
    sa.Column('theme', sa.String(length=32), nullable=True),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('private', sa.Boolean(), nullable=True),
    sa.Column('country', sa.String(length=8), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    op.create_table('blog_post',
    sa.Column('timestamp_creation', sa.DateTime(timezone=128), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('subject', sa.String(length=32), nullable=True),
    sa.Column('content', sa.String(length=4096), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('upvotes', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('friends',
    sa.Column('user1_id', sa.Integer(), nullable=True),
    sa.Column('user2_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user1_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['user2_id'], ['user.id'], )
    )
    op.create_table('game',
    sa.Column('timestamp_creation', sa.DateTime(timezone=128), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('host_id', sa.Integer(), nullable=True),
    sa.Column('guest_id', sa.Integer(), nullable=True),
    sa.Column('state', sa.Integer(), nullable=True),
    sa.Column('AI', sa.String(length=32), nullable=True),
    sa.Column('time_limit', sa.Integer(), nullable=True),
    sa.Column('is_host_white', sa.Boolean(), nullable=True),
    sa.Column('show_eval_bar', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['guest_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['host_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('game', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_game_state'), ['state'], unique=False)

    op.create_table('matchmaker_request',
    sa.Column('timestamp_creation', sa.DateTime(timezone=128), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ranked', sa.Boolean(), nullable=True),
    sa.Column('min_rank', sa.Integer(), nullable=True),
    sa.Column('max_rank', sa.Integer(), nullable=True),
    sa.Column('time', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('message',
    sa.Column('timestamp_creation', sa.DateTime(timezone=128), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('content', sa.String(length=1024), nullable=True),
    sa.Column('timestamp', sa.DateTime(timezone=128), nullable=True),
    sa.Column('sender_id', sa.Integer(), nullable=True),
    sa.Column('receiver_id', sa.Integer(), nullable=True),
    sa.Column('sender_seen', sa.Boolean(), nullable=True),
    sa.Column('receiver_seen', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['receiver_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_message_timestamp'), ['timestamp'], unique=False)

    op.create_table('recovery_try',
    sa.Column('timestamp_creation', sa.DateTime(timezone=128), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('ipaddr', sa.String(length=64), nullable=True),
    sa.Column('is_confirmed', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('blog_post_comment',
    sa.Column('timestamp_creation', sa.DateTime(timezone=128), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('content', sa.String(length=128), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('post_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['post_id'], ['blog_post.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('game_state',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('placement', sa.String(length=256), nullable=True),
    sa.Column('turn', sa.String(length=1), nullable=True),
    sa.Column('move', sa.Integer(), nullable=True),
    sa.Column('white_castle_king_side', sa.Boolean(), nullable=True),
    sa.Column('white_castle_queen_side', sa.Boolean(), nullable=True),
    sa.Column('black_castle_king_side', sa.Boolean(), nullable=True),
    sa.Column('black_castle_queen_side', sa.Boolean(), nullable=True),
    sa.Column('half_move_clock', sa.Integer(), nullable=True),
    sa.Column('game_id', sa.Integer(), nullable=True),
    sa.Column('en_passent', sa.String(length=2), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['game.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('liked_posts',
    sa.Column('luser_id', sa.Integer(), nullable=False),
    sa.Column('blog_post_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['blog_post_id'], ['blog_post.id'], ),
    sa.ForeignKeyConstraint(['luser_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('luser_id', 'blog_post_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('liked_posts')
    op.drop_table('game_state')
    op.drop_table('blog_post_comment')
    op.drop_table('recovery_try')
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_message_timestamp'))

    op.drop_table('message')
    op.drop_table('matchmaker_request')
    with op.batch_alter_table('game', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_game_state'))

    op.drop_table('game')
    op.drop_table('friends')
    op.drop_table('blog_post')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))
        batch_op.drop_index(batch_op.f('ix_user_email'))

    op.drop_table('user')
    op.drop_table('elo_user_rating')
    # ### end Alembic commands ###