"""Add the prize room to configured HackEPS events and backfill enrolled teams."""

from alembic import op

revision = "20261117_ribo_room"
down_revision = "20261117_ribo_prize"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE event_operations o SET config = jsonb_set(o.config::jsonb, '{rooms}',
            coalesce(o.config::jsonb->'rooms', '[]'::jsonb) ||
            '[{"id":"josep-maria-ribo","title":"Josep Maria Ribó","paused": false}]'),
            version = version + 1
        WHERE (EXISTS (SELECT 1 FROM event e WHERE e.id=o.event_id AND e.name ILIKE '%hackeps%')
            OR EXISTS (SELECT 1 FROM event_challenge_vote v WHERE v.event_id=o.event_id AND v.ribo_prize))
            AND NOT coalesce(o.config::jsonb->'rooms', '[]'::jsonb) @> '[{"id":"josep-maria-ribo"}]'
    """)
    op.execute("""
        INSERT INTO event_presentation (event_id,group_id,room,track,position,state,pinned,version)
        SELECT v.event_id,v.group_id,'josep-maria-ribo','josep-maria-ribo',0,'waiting',0,0
        FROM event_challenge_vote v WHERE v.ribo_prize AND EXISTS
            (SELECT 1 FROM event_presentation p WHERE p.event_id=v.event_id AND p.group_id=v.group_id)
        ON CONFLICT (event_id, group_id, track) DO NOTHING
    """)


def downgrade():
    # Rooms and judging records are valid operational data under the old schema.
    pass
