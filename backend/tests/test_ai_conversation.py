from app.ai_conversation import (
    AIResponse,
    ContextBuilder,
    ConversationIntent,
    ConversationService,
    IntentParser,
    MockAIProvider,
    ResponseValidator,
)
from app.game_state import GameState, build_initial_world
from app.story_engine import StoryEngine


def test_intent_parser_detects_valid_intent_and_target() -> None:
    parsed = IntentParser().parse("I'm sorry, Amaka. I was rude to you.")

    assert parsed.intent == "APOLOGIZE"
    assert parsed.target == "amaka"
    assert parsed.confidence >= 0.7
    assert parsed.tone in {"sincere", "gentle", "neutral"}


def test_intent_parser_rejects_unknown_intent_gracefully() -> None:
    parsed = IntentParser().parse("hshdjsdjsd an impossible phrase 9943")

    assert parsed.intent == "TALK"
    assert parsed.target is None
    assert parsed.confidence <= 1.0


def test_context_builder_includes_relevant_story_state() -> None:
    state = GameState(world=build_initial_world(), current_location="corridor")
    state.flags["friendly_with_amaka"] = True
    story_state = {
        "flags": {"friendly_with_amaka": True, "secret_suspicion": True},
        "relationship_scores": {"amaka": 10},
        "memories": ["Amaka told me she likes quiet spaces."],
        "recent_conversation": ["Amaka: You seem calm for a first day."],
    }

    context = ContextBuilder().build(
        game_state=state,
        story_state=story_state,
        character_id="amaka",
        player_message="I am nervous but I like talking to you.",
    )

    assert context.character_id == "amaka"
    assert context.player_name == "player"
    assert context.current_location == "corridor"
    assert "friendly_with_amaka" in context.active_story_flags
    assert any("quiet spaces" in memory for memory in context.recent_memories)
    assert "secret_suspicion" not in context.active_story_flags


def test_mock_provider_generates_reply_without_api_key() -> None:
    provider = MockAIProvider()
    context = ContextBuilder().build(
        game_state=GameState(world=build_initial_world(), current_location="canteen"),
        story_state={"flags": {}, "relationship_scores": {"amaka": 4}, "memories": [], "recent_conversation": []},
        character_id="amaka",
        player_message="I feel out of place here.",
    )

    response = provider.generate_response(context, "I feel out of place here.")

    assert isinstance(response, AIResponse)
    assert response.dialogue
    assert response.intent in {"TALK", "HELP", "APOLOGIZE", "COMPLIMENT"}


def test_response_validator_rejects_invented_secret_and_character() -> None:
    context = ContextBuilder().build(
        game_state=GameState(world=build_initial_world(), current_location="school_gate"),
        story_state={"flags": {}, "relationship_scores": {}, "memories": [], "recent_conversation": []},
        character_id="amaka",
        player_message="I'm nervous.",
    )
    bad_response = AIResponse(
        dialogue="I know your secret about the missing ledger and I know Chinedu is hiding it.",
        emotion="angry",
        tone="sharp",
        intent="TALK",
        memory_candidate=False,
        relationship_effect=None,
        requires_validation=True,
    )

    result = ResponseValidator().validate(bad_response, context)

    assert result.valid is False
    assert "secret" in result.reason.lower() or "invented" in result.reason.lower()


def test_service_uses_fallback_when_provider_fails() -> None:
    state = GameState(world=build_initial_world(), current_location="corridor")
    service = ConversationService(game_state=state, story_state={"flags": {}, "relationship_scores": {}, "memories": [], "recent_conversation": []})

    response = service.process(
        character_id="amaka",
        player_message="I don't understand anything here.",
        provider=None,
    )

    assert response.validated is True
    assert "Amaka" in response.dialogue or "I" in response.dialogue


def test_relationship_effects_are_controlled_and_none_by_default() -> None:
    service = ConversationService(
        game_state=GameState(world=build_initial_world(), current_location="school_gate"),
        story_state={"flags": {}, "relationship_scores": {}, "memories": [], "recent_conversation": []},
    )

    response = service.process(
        character_id="amaka",
        player_message="You seem nice.",
        provider=MockAIProvider(),
    )

    assert response.relationship_effect in {None, "NONE", "POSITIVE_SMALL", "POSITIVE_MEDIUM"}


def test_ai_cannot_mutate_game_state_directly() -> None:
    state = GameState(world=build_initial_world(), current_location="school_gate")
    service = ConversationService(
        game_state=state,
        story_state={"flags": {}, "relationship_scores": {}, "memories": [], "recent_conversation": []},
    )

    response = service.process(
        character_id="amaka",
        player_message="I want to leave school and go to London.",
        provider=MockAIProvider(),
    )

    assert response.dialogue
    assert state.current_location == "school_gate"
    assert state.flags == {}


def test_first_day_amaka_ai_conversation_opportunity_works() -> None:
    engine = StoryEngine(game_state=GameState(world=build_initial_world(), current_location="school_gate"))
    engine.start_episode("ss1_term1_episode1")

    engine.choose("enter_confidently")
    engine.choose("listen_to_adeyemi")
    engine.choose("stay_with_classmates")
    engine.choose("be_friendly")
    engine.choose("follow_sandra")

    response = engine.start_ai_conversation(
        character_id="amaka",
        player_message="Honestly, I'm nervous. I don't know anyone here.",
    )

    assert response.dialogue
    assert response.intent in {"TALK", "HELP", "COMPLIMENT", "APOLOGIZE"}
    assert "amaka" in engine.story_state["recent_conversation"][-1].lower()
