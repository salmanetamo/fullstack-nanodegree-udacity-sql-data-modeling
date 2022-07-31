"""empty message

Revision ID: 4c3352384bca
Revises: 528e661e8b3a
Create Date: 2022-07-30 21:40:52.628420

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c3352384bca'
down_revision = '528e661e8b3a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Artist_Genre')
    op.drop_table('Venue_Genre')
    op.drop_table('Genre')
    op.add_column('Artist', sa.Column('genres', sa.String(length=120), nullable=True))
    op.add_column('Venue', sa.Column('genres', sa.String(length=120), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'genres')
    op.drop_column('Artist', 'genres')
    op.create_table('Venue_Genre',
    sa.Column('venue_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('genre_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['genre_id'], ['Genre.id'], name='Venue_Genre_genre_id_fkey'),
    sa.ForeignKeyConstraint(['venue_id'], ['Venue.id'], name='Venue_Genre_venue_id_fkey'),
    sa.PrimaryKeyConstraint('venue_id', 'genre_id', name='Venue_Genre_pkey')
    )
    op.create_table('Artist_Genre',
    sa.Column('artist_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('genre_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['artist_id'], ['Artist.id'], name='Artist_Genre_artist_id_fkey'),
    sa.ForeignKeyConstraint(['genre_id'], ['Genre.id'], name='Artist_Genre_genre_id_fkey'),
    sa.PrimaryKeyConstraint('artist_id', 'genre_id', name='Artist_Genre_pkey')
    )
    op.create_table('Genre',
    sa.Column('id', sa.INTEGER(), server_default=sa.text('nextval(\'"Genre_id_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='Genre_pkey')
    )
    # ### end Alembic commands ###