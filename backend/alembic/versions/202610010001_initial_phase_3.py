"""initial phase 3 schema

Revision ID: 202610010001
Revises: 
Create Date: 2026-10-01 00:01:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "202610010001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("nickname", sa.String(length=80), nullable=True),
        sa.Column("gender_presentation", sa.String(length=50), nullable=False),
        sa.Column("school_type", sa.String(length=30), nullable=False),
        sa.Column("boarding_status", sa.String(length=20), nullable=False),
        sa.Column("appearance", sa.JSON(), nullable=True),
        sa.Column("traits", sa.JSON(), nullable=False),
        sa.Column("academic_strengths", sa.JSON(), nullable=False),
        sa.Column("academic_weaknesses", sa.JSON(), nullable=False),
        sa.Column("current_class", sa.String(length=40), nullable=False),
        sa.Column("money", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reputation", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ambitions", sa.JSON(), nullable=False),
        sa.Column("family_context", sa.String(length=200), nullable=False),
        sa.Column("current_location", sa.String(length=120), nullable=False),
        sa.Column("current_mood", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("money >= 0", name="ck_players_money_non_negative"),
        sa.CheckConstraint("age >= 12 AND age <= 25", name="ck_players_age_game_range"),
        sa.CheckConstraint("reputation >= 0 AND reputation <= 100", name="ck_players_reputation_range"),
    )

    op.create_table(
        "npcs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("class_name", sa.String(length=40), nullable=False),
        sa.Column("appearance", sa.JSON(), nullable=True),
        sa.Column("personality", sa.JSON(), nullable=False),
        sa.Column("goals", sa.JSON(), nullable=False),
        sa.Column("fears", sa.JSON(), nullable=False),
        sa.Column("current_location", sa.String(length=120), nullable=False),
        sa.Column("current_mood", sa.String(length=50), nullable=False),
        sa.Column("schedule", sa.JSON(), nullable=False),
        sa.Column("speech_style", sa.String(length=80), nullable=False),
        sa.Column("slang_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tier", sa.String(length=20), nullable=False, server_default="supporting"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("age >= 12 AND age <= 80", name="ck_npcs_age_game_range"),
        sa.CheckConstraint("slang_level >= 0 AND slang_level <= 100", name="ck_npcs_slang_level_range"),
    )

    op.create_table(
        "relationships",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("player_id", sa.String(length=64), nullable=False),
        sa.Column("npc_id", sa.String(length=64), nullable=False),
        sa.Column("trust", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("closeness", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("respect", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resentment", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("romantic_interest", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="stranger"),
        sa.Column("history", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("player_id", "npc_id", name="uq_relationships_player_npc"),
        sa.CheckConstraint("trust >= 0 AND trust <= 100", name="ck_relationships_trust_range"),
        sa.CheckConstraint("closeness >= 0 AND closeness <= 100", name="ck_relationships_closeness_range"),
        sa.CheckConstraint("respect >= 0 AND respect <= 100", name="ck_relationships_respect_range"),
        sa.CheckConstraint("resentment >= 0 AND resentment <= 100", name="ck_relationships_resentment_range"),
        sa.CheckConstraint("romantic_interest >= 0 AND romantic_interest <= 100", name="ck_relationships_romantic_interest_range"),
    )

    op.create_table(
        "memories",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("subject_id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("event", sa.String(length=500), nullable=False),
        sa.Column("emotion", sa.String(length=80), nullable=False),
        sa.Column("importance", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("timestamp", sa.String(length=50), nullable=False),
        sa.Column("expiration", sa.String(length=50), nullable=True),
        sa.Column("related_npc_ids", sa.JSON(), nullable=False),
        sa.Column("related_story_id", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("importance IN ('low', 'medium', 'high', 'critical')", name="ck_memories_importance_valid"),
    )

    op.create_table(
        "secrets",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("content", sa.String(length=1000), nullable=False),
        sa.Column("importance", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("discovery_method", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="hidden"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("importance IN ('low', 'medium', 'high', 'critical')", name="ck_secrets_importance_valid"),
        sa.CheckConstraint("status IN ('hidden', 'partially_known', 'exposed', 'resolved')", name="ck_secrets_status_valid"),
    )

    op.create_table(
        "secret_knowledge",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("secret_id", sa.String(length=64), nullable=False),
        sa.Column("character_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["secret_id"], ["secrets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "rumours",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("origin_id", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=False),
        sa.Column("current_story", sa.String(length=500), nullable=False),
        sa.Column("known_by", sa.JSON(), nullable=False),
        sa.Column("credibility", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("spread_rate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("credibility >= 0 AND credibility <= 100", name="ck_rumours_credibility_range"),
        sa.CheckConstraint("spread_rate >= 0 AND spread_rate <= 100", name="ck_rumours_spread_rate_range"),
    )

    op.create_table(
        "items",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("item_type", sa.String(length=30), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("location", sa.String(length=120), nullable=False),
        sa.Column("story_relevance", sa.String(length=250), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quantity >= 0", name="ck_items_quantity_non_negative"),
    )

    op.create_table(
        "player_inventory",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("player_id", sa.String(length=64), nullable=False),
        sa.Column("item_id", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("location", sa.String(length=120), nullable=False, server_default="bag"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("player_id", "item_id", name="uq_player_inventory_player_item"),
        sa.CheckConstraint("quantity >= 0", name="ck_player_inventory_quantity_non_negative"),
    )

    op.create_table(
        "story_progress",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("current_year", sa.String(length=10), nullable=False, server_default="SS1"),
        sa.Column("current_term", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("current_episode", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("current_scene", sa.String(length=120), nullable=False, server_default="campus"),
        sa.Column("completed_episodes", sa.JSON(), nullable=False),
        sa.Column("active_storylines", sa.JSON(), nullable=False),
        sa.Column("story_flags", sa.JSON(), nullable=False),
        sa.Column("major_choices", sa.JSON(), nullable=False),
        sa.Column("unlocked_events", sa.JSON(), nullable=False),
        sa.Column("unlocked_locations", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("current_term >= 1 AND current_term <= 3", name="ck_story_progress_term_range"),
        sa.CheckConstraint("current_year IN ('SS1', 'SS2', 'SS3')", name="ck_story_progress_year_valid"),
    )


def downgrade() -> None:
    op.drop_table("story_progress")
    op.drop_table("player_inventory")
    op.drop_table("items")
    op.drop_table("rumours")
    op.drop_table("secret_knowledge")
    op.drop_table("secrets")
    op.drop_table("memories")
    op.drop_table("relationships")
    op.drop_table("npcs")
    op.drop_table("players")
