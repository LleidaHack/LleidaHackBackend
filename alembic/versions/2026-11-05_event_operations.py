"""Event operations, immutable audit, meal rounds, coins and judging."""

from alembic import op

revision = "20261105_operations"
down_revision = "20261010_notes_audit"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "\nCREATE TABLE event_operations (\n\tevent_id INTEGER NOT NULL, \n\tversion INTEGER NOT NULL, \n\tconfig JSON NOT NULL, \n\tPRIMARY KEY (event_id), \n\tFOREIGN KEY(event_id) REFERENCES event (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE event_presentation (\n\tid SERIAL NOT NULL, \n\tevent_id INTEGER NOT NULL, \n\tgroup_id INTEGER NOT NULL, \n\troom VARCHAR(80) NOT NULL, \n\ttrack VARCHAR(80) NOT NULL, \n\tposition INTEGER NOT NULL, \n\tscheduled_at TIMESTAMP WITH TIME ZONE, \n\tstate VARCHAR(30) NOT NULL, \n\tpinned INTEGER NOT NULL, \n\tversion INTEGER NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (event_id, group_id, track), \n\tFOREIGN KEY(event_id) REFERENCES event (id), \n\tFOREIGN KEY(group_id) REFERENCES hacker_group (id)\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_event_presentation_event_id ON event_presentation (event_id)"
    )
    op.execute(
        "\nCREATE TABLE event_push_subscription (\n\tid SERIAL NOT NULL, \n\tevent_id INTEGER NOT NULL, \n\tendpoint VARCHAR NOT NULL, \n\tsubscription JSON NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(event_id) REFERENCES event (id), \n\tUNIQUE (endpoint)\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_event_push_subscription_event_id ON event_push_subscription (event_id)"
    )
    op.execute(
        "\nCREATE TABLE operation_audit (\n\tid SERIAL NOT NULL, \n\tevent_id INTEGER NOT NULL, \n\tactor_id INTEGER, \n\tuser_id INTEGER, \n\taction VARCHAR(60) NOT NULL, \n\toutcome VARCHAR(30) NOT NULL, \n\toperation_id VARCHAR(100) NOT NULL, \n\tdevice VARCHAR(100) NOT NULL, \n\tdetails JSON NOT NULL, \n\tresult JSON NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (event_id, operation_id), \n\tFOREIGN KEY(event_id) REFERENCES event (id), \n\tFOREIGN KEY(actor_id) REFERENCES my_user (id), \n\tFOREIGN KEY(user_id) REFERENCES my_user (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_operation_audit_event_id ON operation_audit (event_id)")
    op.execute(
        "\nCREATE TABLE coin_movement (\n\tid SERIAL NOT NULL, \n\tevent_id INTEGER NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\tamount INTEGER NOT NULL, \n\tbalance_before INTEGER NOT NULL, \n\tbalance_after INTEGER NOT NULL, \n\treason VARCHAR(500) NOT NULL, \n\taudit_id INTEGER NOT NULL, \n\treversal_of INTEGER, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(event_id) REFERENCES event (id), \n\tFOREIGN KEY(user_id) REFERENCES my_user (id), \n\tFOREIGN KEY(audit_id) REFERENCES operation_audit (id), \n\tUNIQUE (reversal_of), \n\tFOREIGN KEY(reversal_of) REFERENCES coin_movement (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_coin_movement_user_id ON coin_movement (user_id)")
    op.execute("CREATE INDEX ix_coin_movement_event_id ON coin_movement (event_id)")
    op.execute(
        "\nCREATE TABLE event_push_delivery (\n\tid SERIAL NOT NULL, \n\tevent_id INTEGER NOT NULL, \n\tsubscription_id INTEGER NOT NULL, \n\talert_id VARCHAR(100) NOT NULL, \n\tpayload JSON NOT NULL, \n\tattempts INTEGER NOT NULL, \n\tstate VARCHAR(30) NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (subscription_id, alert_id), \n\tFOREIGN KEY(event_id) REFERENCES event (id), \n\tFOREIGN KEY(subscription_id) REFERENCES event_push_subscription (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE operation_scan (\n\tid SERIAL NOT NULL, \n\tevent_id INTEGER NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\tkind VARCHAR(30) NOT NULL, \n\ttarget VARCHAR(100) NOT NULL, \n\tround INTEGER NOT NULL, \n\taudit_id INTEGER, \n\tPRIMARY KEY (id), \n\tUNIQUE (event_id, user_id, kind, target, round), \n\tFOREIGN KEY(event_id) REFERENCES event (id), \n\tFOREIGN KEY(user_id) REFERENCES my_user (id), \n\tFOREIGN KEY(audit_id) REFERENCES operation_audit (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_operation_scan_event_id ON operation_scan (event_id)")
    op.execute(
        "INSERT INTO operation_scan (event_id,user_id,kind,target,round) SELECT m.event_id,hm.user_id,'meal',CAST(m.id AS VARCHAR),1 FROM hacker_meal hm JOIN meal m ON m.id=hm.meal_id"
    )


def downgrade():
    op.drop_table("operation_scan")
    op.drop_table("event_push_delivery")
    op.drop_table("coin_movement")
    op.drop_table("operation_audit")
    op.drop_table("event_push_subscription")
    op.drop_table("event_presentation")
    op.drop_table("event_operations")
