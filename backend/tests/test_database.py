import pytest
from sqlalchemy import inspect, text

from app.config import settings
from app.db.database import SessionLocal, engine
from app.db.models import NPC, Player, Relationship
from app.models.npc import NPC as NPCDomain
from app.models.player import Appearance, Player as PlayerDomain, SchoolType, BoardingStatus
from app.models.relationship import Relationship as RelationshipDomain, RelationshipStatus
from app.repositories import NPCRepository, PlayerRepository, RelationshipRepository


@pytest.fixture(scope="session")
def db_session():
    if not settings.database_url or (
        "localhost" not in settings.database_url
        and "127.0.0.1" not in settings.database_url
    ):
        pytest.skip("Local PostgreSQL is not configured via DATABASE_URL; database integration tests were skipped.")

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL is unavailable locally: {exc}")

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.mark.usefixtures("db_session")
def test_database_connection_works(db_session):
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar_one()
    assert result == 1


@pytest.mark.usefixtures("db_session")
def test_database_tables_are_present(db_session):
    inspector = inspect(engine)
    expected_tables = {
        "players",
        "npcs",
        "relationships",
        "memories",
        "secrets",
        "secret_knowledge",
        "rumours",
        "items",
        "player_inventory",
        "story_progress",
    }
    tables = set(inspector.get_table_names())
    assert expected_tables.issubset(tables)


@pytest.mark.usefixtures("db_session")
def test_player_repository_persistence(db_session):
    repo = PlayerRepository(db_session)
    player = PlayerDomain(
        id="db-player-1",
        name="Mariam Bello",
        age=17,
        nickname="Mimi",
        gender_presentation="female",
        school_type=SchoolType.GOVERNMENT,
        boarding_status=BoardingStatus.DAY,
        appearance=Appearance(
            skin_tone="light brown",
            hair="long black",
            eyes="brown",
            glasses=False,
            height_build="average",
            uniform="crestview blazer",
            shoes="black shoes",
            backpack="green backpack",
        ),
        traits=["kind"],
        academic_strengths=["chemistry"],
        academic_weaknesses=["history"],
        current_class="SS2-A",
        money=1500.0,
        reputation=40,
        ambitions=["join medicine"],
        family_context="supportive home",
        current_location="Library",
        current_mood="calm",
        inventory_ids=["db-item-1"],
    )

    record = repo.create(player)
    db_session.flush()

    assert db_session.get(Player, record.id) is not None
    assert record.name == "Mariam Bello"


@pytest.mark.usefixtures("db_session")
def test_npc_repository_persistence(db_session):
    repo = NPCRepository(db_session)
    npc = NPCDomain(
        id="db-npc-1",
        name="Miss Amina",
        age=29,
        class_name="SS3-A",
        appearance=Appearance(
            skin_tone="deep brown",
            hair="tight curls",
            eyes="dark brown",
            glasses=True,
            height_build="slim",
            uniform="crestview blazer",
            shoes="brown flats",
            backpack="black satchel",
        ),
        personality=["patient", "strict"],
        goals=["teach well"],
        fears=["losing control"],
        current_location="Classroom 5",
        current_mood="focused",
        secrets=[],
        memory_ids=[],
        relationship_ids=[],
        schedule=["class period"],
        speech_style="formal",
        slang_level=20,
    )

    record = repo.create(npc)
    db_session.flush()

    assert db_session.get(NPC, record.id) is not None
    assert record.name == "Miss Amina"


@pytest.mark.usefixtures("db_session")
def test_relationship_repository_persistence(db_session):
    repo = RelationshipRepository(db_session)
    relationship = RelationshipDomain(
        player_id="db-player-1",
        npc_id="db-npc-1",
        trust=70,
        closeness=60,
        respect=80,
        resentment=5,
        romantic_interest=0,
        status=RelationshipStatus.FRIEND,
        history=["met at school"],
    )

    record = repo.create(relationship)
    db_session.flush()

    result = repo.get_between_player_and_npc("db-player-1", "db-npc-1")
    assert result is not None
    assert result.status == "friend"
    assert result.trust == 70
