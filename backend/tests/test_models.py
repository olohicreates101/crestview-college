import pytest
from pydantic import ValidationError

from app.models import (
    Appearance,
    BoardingStatus,
    Item,
    ItemType,
    Memory,
    MemoryImportance,
    NPC,
    NPCTier,
    Player,
    Relationship,
    RelationshipStatus,
    Rumour,
    SchoolType,
    SchoolYear,
    Secret,
    SecretImportance,
    SecretStatus,
    StoryState,
)


def make_appearance() -> Appearance:
    return Appearance(
        skin_tone="dark brown",
        hair="short black",
        eyes="brown",
        glasses=False,
        height_build="average",
        uniform="crestview blazer",
        shoes="black loafers",
        backpack="green rucksack",
    )


def test_player_valid_creation() -> None:
    player = Player(
        id="player-1",
        name="Ada Okafor",
        age=16,
        nickname="Ada",
        gender_presentation="female",
        school_type=SchoolType.GOVERNMENT,
        boarding_status=BoardingStatus.DAY,
        appearance=make_appearance(),
        traits=["quiet", "determined"],
        academic_strengths=["biology", "mathematics"],
        academic_weaknesses=["public speaking"],
        current_class="SS1-A",
        money=5000.0,
        reputation=35,
        ambitions=["become a doctor"],
        family_context="single-parent household",
        current_location="Main Hall",
        current_mood="focused",
        inventory_ids=["item-1", "item-2"],
    )

    assert player.name == "Ada Okafor"
    assert player.school_type == SchoolType.GOVERNMENT
    assert player.appearance.backpack == "green rucksack"


def test_player_negative_money_rejected() -> None:
    with pytest.raises(ValidationError):
        Player(
            id="player-2",
            name="Bola",
            age=17,
            nickname="B",
            gender_presentation="male",
            school_type=SchoolType.PRIVATE,
            boarding_status=BoardingStatus.BOARDING,
            appearance=make_appearance(),
            traits=["brave"],
            academic_strengths=["history"],
            academic_weaknesses=["chemistry"],
            current_class="SS2-B",
            money=-10,
            reputation=40,
            ambitions=["leadership"],
            family_context="large family",
            current_location="Dormitory",
            current_mood="calm",
            inventory_ids=[],
        )


def test_player_invalid_age_rejected() -> None:
    with pytest.raises(ValidationError):
        Player(
            id="player-3",
            name="Chioma",
            age=8,
            nickname="Chi",
            gender_presentation="female",
            school_type=SchoolType.GOVERNMENT,
            boarding_status=BoardingStatus.DAY,
            appearance=make_appearance(),
            traits=["curious"],
            academic_strengths=["literature"],
            academic_weaknesses=["geometry"],
            current_class="SS1-C",
            money=2500,
            reputation=20,
            ambitions=["write novels"],
            family_context="supportive",
            current_location="Library",
            current_mood="curious",
            inventory_ids=["book-1"],
        )


def test_player_valid_nested_appearance() -> None:
    appearance = Appearance(
        skin_tone="light brown",
        hair="braided",
        eyes="hazel",
        glasses=True,
        height_build="slim",
        uniform="crestview sweater",
        shoes="white trainers",
        backpack="blue backpack",
    )

    player = Player(
        id="player-4",
        name="Tari",
        age=15,
        nickname="T",
        gender_presentation="nonbinary",
        school_type=SchoolType.PRIVATE,
        boarding_status=BoardingStatus.BOARDING,
        appearance=appearance,
        traits=["kind"],
        academic_strengths=["art"],
        academic_weaknesses=["physics"],
        current_class="SS1-D",
        money=1200,
        reputation=30,
        ambitions=["design games"],
        family_context="urban home",
        current_location="Classroom 2",
        current_mood="happy",
        inventory_ids=["sketchbook"],
    )

    assert player.appearance.glasses is True
    assert player.appearance.height_build == "slim"


def test_npc_valid_creation() -> None:
    npc = NPC(
        id="npc-1",
        name="Mr. Nnamdi",
        age=38,
        class_name="SS2-B",
        appearance=make_appearance(),
        personality=["strict", "fair"],
        goals=["teach well"],
        fears=["students losing focus"],
        current_location="Staff Room",
        current_mood="patient",
        secrets=["secret-1"],
        memory_ids=["memory-1"],
        relationship_ids=["relationship-1"],
        schedule=["morning duty", "class period"],
        speech_style="formal",
        slang_level=10,
        tier=NPCTier.CORE,
    )

    assert npc.tier == NPCTier.CORE
    assert npc.class_name == "SS2-B"


def test_npc_valid_tier() -> None:
    npc = NPC(
        id="npc-2",
        name="Zainab",
        age=17,
        class_name="SS3-A",
        appearance=make_appearance(),
        personality=["cheerful"],
        goals=["join the debate club"],
        fears=["being ignored"],
        current_location="Cafeteria",
        current_mood="excited",
        secrets=[],
        memory_ids=[],
        relationship_ids=[],
        schedule=["lunch break"],
        speech_style="casual",
        slang_level=60,
        tier=NPCTier.SUPPORTING,
    )

    assert npc.tier == NPCTier.SUPPORTING


def test_npc_invalid_required_fields() -> None:
    with pytest.raises(ValidationError):
        NPC(
            id="npc-3",
            age=18,
            class_name="SS1-A",
            appearance=make_appearance(),
            personality=["kind"],
            goals=["study"],
            fears=[],
            current_location="",
            current_mood="neutral",
            secrets=[],
            memory_ids=[],
            relationship_ids=[],
            schedule=[],
            speech_style="friendly",
            slang_level=25,
            tier=NPCTier.BACKGROUND,
        )


def test_relationship_valid_creation() -> None:
    relationship = Relationship(
        player_id="player-1",
        npc_id="npc-1",
        trust=80,
        closeness=70,
        respect=65,
        resentment=10,
        romantic_interest=0,
        status=RelationshipStatus.FRIEND,
        history=["met at orientation", "helped with homework"],
    )

    assert relationship.status == RelationshipStatus.FRIEND
    assert relationship.trust == 80


def test_relationship_values_below_zero_rejected() -> None:
    with pytest.raises(ValidationError):
        Relationship(
            player_id="player-1",
            npc_id="npc-2",
            trust=-1,
            closeness=50,
            respect=50,
            resentment=0,
            romantic_interest=0,
            status=RelationshipStatus.ACQUAINTANCE,
            history=[],
        )


def test_relationship_values_above_hundred_rejected() -> None:
    with pytest.raises(ValidationError):
        Relationship(
            player_id="player-1",
            npc_id="npc-2",
            trust=100,
            closeness=100,
            respect=101,
            resentment=0,
            romantic_interest=5,
            status=RelationshipStatus.CLOSE_FRIEND,
            history=[],
        )


def test_relationship_status_enum_values_valid() -> None:
    relationship = Relationship(
        player_id="player-1",
        npc_id="npc-3",
        trust=40,
        closeness=30,
        respect=50,
        resentment=15,
        romantic_interest=90,
        status=RelationshipStatus.CRUSH,
        history=["shared notes"],
    )

    assert relationship.status == RelationshipStatus.CRUSH


def test_memory_valid_creation() -> None:
    memory = Memory(
        id="memory-1",
        subject_id="npc-1",
        actor_id="player-1",
        event="Helped me carry my books after class.",
        emotion="grateful",
        importance=MemoryImportance.HIGH,
        timestamp="2025-02-14T09:00:00",
        expiration="2025-06-14T09:00:00",
        related_npc_ids=["npc-1", "npc-2"],
        related_story_id="story-1",
    )

    assert memory.importance == MemoryImportance.HIGH
    assert memory.event.startswith("Helped")


def test_memory_valid_importance() -> None:
    memory = Memory(
        id="memory-2",
        subject_id="player-1",
        actor_id="npc-2",
        event="Saw a secret meeting behind the library.",
        emotion="alert",
        importance=MemoryImportance.CRITICAL,
        timestamp="2025-02-15T10:10:00",
        related_npc_ids=["npc-2"],
        related_story_id="story-2",
    )

    assert memory.importance == MemoryImportance.CRITICAL


def test_secret_valid_creation() -> None:
    secret = Secret(
        id="secret-1",
        owner_id="npc-1",
        content="The headmaster is planning a sudden inspection.",
        known_by=["player-1", "npc-2"],
        importance=SecretImportance.HIGH,
        discovery_method="overheard a phone call",
        status=SecretStatus.PARTIALLY_KNOWN,
    )

    assert secret.known_by == ["player-1", "npc-2"]
    assert secret.status == SecretStatus.PARTIALLY_KNOWN


def test_secret_known_by_works() -> None:
    secret = Secret(
        id="secret-2",
        owner_id="player-1",
        content="I skipped the assembly to meet someone in secret.",
        known_by=["npc-3"],
        importance=SecretImportance.LOW,
        discovery_method="confession",
        status=SecretStatus.HIDDEN,
    )

    assert "npc-3" in secret.known_by


def test_rumour_valid_creation() -> None:
    rumour = Rumour(
        id="rumour-1",
        origin_id="npc-1",
        target_id="player-1",
        current_story="Someone saw Ada leaving the headmaster's office.",
        known_by=["npc-2", "npc-3"],
        credibility=65,
        spread_rate=40,
        created_at="2025-02-15T09:00:00",
        status="spreading",
    )

    assert rumour.credibility == 65
    assert rumour.status == "spreading"


def test_rumour_bounded_values() -> None:
    with pytest.raises(ValidationError):
        Rumour(
            id="rumour-2",
            origin_id="npc-2",
            target_id="npc-1",
            current_story="A rumour about exam leaks is circulating.",
            known_by=["player-1"],
            credibility=101,
            spread_rate=50,
            created_at="2025-02-16T08:00:00",
            status="active",
        )


def test_item_valid_creation() -> None:
    item = Item(
        id="item-1",
        name="Science notebook",
        type=ItemType.SCHOOL_SUPPLY,
        owner_id="player-1",
        quantity=2,
        location="bag",
        story_relevance="used during practicals",
    )

    assert item.type == ItemType.SCHOOL_SUPPLY
    assert item.quantity == 2


def test_item_negative_quantity_rejected() -> None:
    with pytest.raises(ValidationError):
        Item(
            id="item-2",
            name="Candy",
            type=ItemType.FOOD,
            owner_id="player-1",
            quantity=-1,
            location="pocket",
            story_relevance="snack",
        )


def test_story_valid_ss1_state() -> None:
    state = StoryState(
        current_year=SchoolYear.SS1,
        current_term=1,
        current_episode=1,
        current_scene="Assembly Hall",
        completed_episodes=[1],
        active_storylines=["first week"],
        story_flags=["orientation_started"],
        major_choices=[],
        unlocked_events=["open_day"],
        unlocked_locations=["library"],
    )

    assert state.current_year == SchoolYear.SS1
    assert state.current_term == 1


def test_story_invalid_term_rejected() -> None:
    with pytest.raises(ValidationError):
        StoryState(
            current_year=SchoolYear.SS2,
            current_term=4,
            current_episode=1,
            current_scene="classroom",
            completed_episodes=[],
            active_storylines=[],
            story_flags=[],
            major_choices=[],
            unlocked_events=[],
            unlocked_locations=[],
        )


def test_story_invalid_year_rejected() -> None:
    with pytest.raises(ValidationError):
        StoryState(
            current_year="SS5",
            current_term=2,
            current_episode=1,
            current_scene="field",
            completed_episodes=[],
            active_storylines=[],
            story_flags=[],
            major_choices=[],
            unlocked_events=[],
            unlocked_locations=[],
        )
