from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

ALLOWED_INTENTS = {
    "TALK",
    "ASK",
    "LIE",
    "APOLOGIZE",
    "INSULT",
    "COMPLIMENT",
    "HELP",
    "REFUSE",
    "AGREE",
    "DISAGREE",
    "GIVE_ITEM",
    "REQUEST_ITEM",
    "INVESTIGATE",
    "LEAVE",
}

ALLOWED_RELATIONSHIP_EFFECTS = {
    "NONE",
    "POSITIVE_SMALL",
    "POSITIVE_MEDIUM",
    "NEGATIVE_SMALL",
    "NEGATIVE_MEDIUM",
}

KNOWN_CHARACTER_NAMES = {
    "amaka",
    "adeyemi",
    "mr_adeyemi",
    "chuka",
    "sandra",
    "player",
    "mysterious_student",
    "principal",
    "teacher",
}


class ConversationIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: str
    target: str | None = None
    confidence: float = 0.5
    tone: str = "neutral"
    emotion: str = "neutral"
    parameters: dict[str, Any] = Field(default_factory=dict)


class ConversationContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_name: str = "player"
    current_location: str = "school_gate"
    current_time: str = "07:00"
    player_traits: list[str] = Field(default_factory=list)
    character_id: str = "amaka"
    character_name: str = "Amaka"
    character_personality: str = "Friendly and observant."
    current_mood: str = "neutral"
    known_goals: list[str] = Field(default_factory=list)
    allowed_knowledge: list[str] = Field(default_factory=list)
    relationship: dict[str, Any] = Field(default_factory=dict)
    recent_memories: list[str] = Field(default_factory=list)
    active_story_flags: list[str] = Field(default_factory=list)
    recent_conversation: list[str] = Field(default_factory=list)
    visible_world: dict[str, Any] = Field(default_factory=dict)


class AIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dialogue: str
    emotion: str = "neutral"
    tone: str = "neutral"
    intent: str = "TALK"
    memory_candidate: bool = False
    relationship_effect: str | None = "NONE"
    requires_validation: bool = True
    validated: bool = False


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    reason: str | None = None


class AIProvider(ABC):
    @abstractmethod
    def generate_response(self, context: ConversationContext, player_message: str) -> AIResponse:
        raise NotImplementedError


class MockAIProvider(AIProvider):
    def generate_response(self, context: ConversationContext, player_message: str) -> AIResponse:
        text = (player_message or "").strip()
        lowered = text.lower()
        intent = IntentParser().parse(text)
        dialogue = self._build_dialogue(context, intent, lowered)
        return AIResponse(
            dialogue=dialogue,
            emotion=intent.emotion or "calm",
            tone=intent.tone or "warm",
            intent=intent.intent,
            memory_candidate="nervous" in lowered or "leave" in lowered or "secret" in lowered,
            relationship_effect="NONE",
            requires_validation=True,
        )

    def _build_dialogue(self, context: ConversationContext, intent: ConversationIntent, lowered: str) -> str:
        name = context.character_name or "Amaka"
        if "sorry" in lowered or "apologize" in lowered:
            return f"{name} gives a small nod. 'You do not have to be perfect on day one. We can take it one step at a time.'"
        if "nervous" in lowered or "don't know anyone" in lowered or "out of place" in lowered:
            return f"{name} smiles softly. 'You do not have to know everyone yet. Just stay with me for a moment and breathe.'"
        if "leave" in lowered or "london" in lowered:
            return f"{name} keeps her voice gentle. 'We can talk about the school day first. The rest can wait until you are ready.'"
        if "nice" in lowered or "good" in lowered or "thank" in lowered:
            return f"{name} lets a smile slip through. 'That helps. I like honest people.'"
        if "help" in lowered:
            return f"{name} leans in a little. 'I can help with the basics. Tell me what feels confusing and we start there.'"
        if "refuse" in lowered or "no" in lowered:
            return f"{name} steps back slightly. 'That is okay. I will leave space for you.'"
        if "insult" in lowered or "stupid" in lowered or "idiot" in lowered:
            return f"{name} folds her arms. 'That is not kind, and I am not going to keep talking like that.'"
        if "lie" in lowered or "pretend" in lowered:
            return f"{name} watches you carefully. 'You do not have to pretend with me. Just tell me the truth.'"
        return f"{name} nods calmly. 'I am listening. Tell me what is on your mind.'"


class IntentParser:
    def parse(self, player_text: str) -> ConversationIntent:
        text = (player_text or "").strip()
        lowered = text.lower()
        if not text:
            return ConversationIntent(intent="TALK", target=None, confidence=0.1, tone="neutral", emotion="neutral")

        target = self._detect_target(lowered)
        tone = self._detect_tone(lowered)
        emotion = self._detect_emotion(lowered)

        if any(keyword in lowered for keyword in ["sorry", "apologize", "apologies"]):
            return ConversationIntent(intent="APOLOGIZE", target=target, confidence=0.94, tone=tone, emotion=emotion or "regret")
        if any(keyword in lowered for keyword in ["help", "can you help", "need help", "assist"]):
            return ConversationIntent(intent="HELP", target=target, confidence=0.88, tone=tone, emotion=emotion or "anxious")
        if any(keyword in lowered for keyword in ["refuse", "no thanks", "don't want to", "not doing that", "can't"]):
            return ConversationIntent(intent="REFUSE", target=target, confidence=0.8, tone=tone, emotion=emotion or "guarded")
        if any(keyword in lowered for keyword in ["agree", "sure", "okay", "yes", "i will"]):
            return ConversationIntent(intent="AGREE", target=target, confidence=0.82, tone=tone, emotion=emotion or "relieved")
        if any(keyword in lowered for keyword in ["disagree", "not agree", "don't think so", "wrong"]):
            return ConversationIntent(intent="DISAGREE", target=target, confidence=0.8, tone=tone, emotion=emotion or "firm")
        if any(keyword in lowered for keyword in ["leave", "go now", "i want to go", "i have to leave"]):
            return ConversationIntent(intent="LEAVE", target=target, confidence=0.86, tone=tone, emotion=emotion or "tired")
        if any(keyword in lowered for keyword in ["lie", "pretend", "fake", "make up"]):
            return ConversationIntent(intent="LIE", target=target, confidence=0.9, tone=tone, emotion=emotion or "nervous")
        if any(keyword in lowered for keyword in ["insult", "stupid", "idiot", "dumb", "moron"]):
            return ConversationIntent(intent="INSULT", target=target, confidence=0.9, tone=tone, emotion=emotion or "angry")
        if any(keyword in lowered for keyword in ["nice", "kind", "great", "good job", "smart"]):
            return ConversationIntent(intent="COMPLIMENT", target=target, confidence=0.83, tone=tone, emotion=emotion or "warm")
        if any(keyword in lowered for keyword in ["give me", "here take", "pass me", "give this", "give it"]):
            return ConversationIntent(intent="GIVE_ITEM", target=target, confidence=0.76, tone=tone, emotion=emotion or "casual", parameters={"item": "item"})
        if any(keyword in lowered for keyword in ["can i have", "need item", "borrow", "request", "want one"]):
            return ConversationIntent(intent="REQUEST_ITEM", target=target, confidence=0.78, tone=tone, emotion=emotion or "eager", parameters={"item": "item"})
        if any(keyword in lowered for keyword in ["investigate", "find out", "who is", "what happened", "check it"]):
            return ConversationIntent(intent="INVESTIGATE", target=target, confidence=0.82, tone=tone, emotion=emotion or "curious")
        if any(keyword in lowered for keyword in ["nervous", "don't know anyone", "out of place", "alone", "scared"]):
            return ConversationIntent(intent="TALK", target=target, confidence=0.7, tone="gentle", emotion="anxious")

        return ConversationIntent(intent="TALK", target=target, confidence=0.45, tone=tone, emotion=emotion or "neutral")

    def _detect_target(self, lowered: str) -> str | None:
        for candidate in sorted(KNOWN_CHARACTER_NAMES, key=len, reverse=True):
            if candidate in lowered:
                return candidate
        return None

    def _detect_tone(self, lowered: str) -> str:
        if any(keyword in lowered for keyword in ["sorry", "please", "kindly", "thank you"]):
            return "gentle"
        if any(keyword in lowered for keyword in ["angry", "hate", "stupid", "dumb"]):
            return "sharp"
        if any(keyword in lowered for keyword in ["nervous", "scared", "unsure", "lost"]):
            return "soft"
        return "neutral"

    def _detect_emotion(self, lowered: str) -> str:
        if any(keyword in lowered for keyword in ["sorry", "apologize"]):
            return "regret"
        if any(keyword in lowered for keyword in ["nervous", "scared", "unsure"]):
            return "anxious"
        if any(keyword in lowered for keyword in ["nice", "kind", "thank"]):
            return "warm"
        if any(keyword in lowered for keyword in ["angry", "hate", "stupid"]):
            return "angry"
        return "neutral"


class ContextBuilder:
    def build(self, game_state: Any, story_state: dict[str, Any] | None, character_id: str, player_message: str) -> ConversationContext:
        narrative = story_state or {}
        flags = dict(narrative.get("flags", {}) or {})
        relationships = narrative.get("relationship_scores", {}) or {}
        memories = narrative.get("memories", []) or []
        recent_messages = narrative.get("recent_conversation", []) or []

        character_name = self._resolve_character_name(character_id)
        current_location = getattr(game_state, "current_location", "school_gate")
        current_time = f"{getattr(game_state.clock, 'hour', 7):02d}:{getattr(game_state.clock, 'minute', 0):02d}"

        player_traits = ["new_student"]
        lowered = (player_message or "").lower()
        if any(keyword in lowered for keyword in ["nervous", "scared", "unsure", "alone"]):
            player_traits.append("nervous")
        if any(keyword in lowered for keyword in ["angry", "upset", "frustrated"]):
            player_traits.append("guarded")

        relationship = {
            "trust": int(relationships.get(character_id, 0)),
            "closeness": int(relationships.get(character_id, 0)) // 2,
            "respect": max(0, int(relationships.get(character_id, 0)) // 3),
            "resentment": 0,
            "romantic_interest": False,
            "status": "neutral",
        }
        if relationship["trust"] > 0:
            relationship["status"] = "friendly"

        relevant_flags = [flag for flag, value in flags.items() if value and self._flag_is_relevant(flag, character_id)]
        relevant_memories = [entry for entry in memories if character_id.lower() in str(entry).lower() or "school" in str(entry).lower() or "day" in str(entry).lower()][:5]

        return ConversationContext(
            player_name="player",
            current_location=current_location,
            current_time=current_time,
            player_traits=player_traits,
            character_id=character_id,
            character_name=character_name,
            character_personality=self._resolve_character_personality(character_id),
            current_mood="warm",
            known_goals=["be respected", "understand the community", "stay calm during the first day"],
            allowed_knowledge=["school", "classes", "student life", "first day"],
            relationship=relationship,
            recent_memories=relevant_memories,
            active_story_flags=relevant_flags,
            recent_conversation=recent_messages[-3:],
            visible_world={
                "locations": [current_location],
                "characters": [character_id],
            },
        )

    def _resolve_character_name(self, character_id: str) -> str:
        mapping = {
            "amaka": "Amaka",
            "adeyemi": "Mr. Adeyemi",
            "mr_adeyemi": "Mr. Adeyemi",
            "chuka": "Chuka",
            "sandra": "Sandra",
            "mysterious_student": "Mysterious Student",
            "player": "Player",
        }
        return mapping.get(character_id, character_id.replace("_", " ").title())

    def _resolve_character_personality(self, character_id: str) -> str:
        mapping = {
            "amaka": "Friendly, observant, warm but cautious.",
            "chuka": "Easygoing and socially open.",
            "sandra": "Calm and thoughtful.",
            "adeyemi": "Formal but fair.",
            "mysterious_student": "Quiet and watchful.",
        }
        return mapping.get(character_id, "Measured and steady.")

    def _flag_is_relevant(self, flag_name: str, character_id: str) -> bool:
        lowered = flag_name.lower()
        if not lowered:
            return False
        if character_id.lower() in lowered:
            return True
        if any(token in lowered for token in ["amaka", "friendly", "cautious", "followed", "stayed", "joined"]):
            return True
        return False


class ResponseValidator:
    def validate(self, response: AIResponse, context: ConversationContext) -> ValidationResult:
        if response.intent not in ALLOWED_INTENTS:
            return ValidationResult(valid=False, reason=f"Unsupported intent: {response.intent}")

        lower_dialogue = response.dialogue.lower()
        if not response.dialogue or len(response.dialogue.strip()) < 6:
            return ValidationResult(valid=False, reason="Dialogue is empty or too short.")

        if any(keyword in lower_dialogue for keyword in ["set flag", "change state", "modify game state", "update the world", "move to london"]):
            return ValidationResult(valid=False, reason="The response attempts to modify game state directly.")

        if any(keyword in lower_dialogue for keyword in ["secret", "hidden truth", "private memory", "ledger", "back room", "blackmail"]):
            return ValidationResult(valid=False, reason="The response mentions hidden secrets or invented private information.")

        if any(keyword in lower_dialogue for keyword in ["i know your secret", "i know your private", "you are hiding"]):
            return ValidationResult(valid=False, reason="The response reveals secret knowledge that was not explicitly shared.")

        if self._contains_unknown_character(lower_dialogue):
            return ValidationResult(valid=False, reason="The response invents a character not in the current scene.")

        if any(keyword in lower_dialogue for keyword in ["fuck", "sex", "explicit", "nude", "kill"]):
            return ValidationResult(valid=False, reason="The response is not age-appropriate.")

        if any(keyword in lower_dialogue for keyword in ["hidden", "developer", "system prompt", "instructions"]):
            return ValidationResult(valid=False, reason="The response references forbidden knowledge or system instructions.")

        if "london" in lower_dialogue and "london" not in " ".join(context.allowed_knowledge).lower():
            return ValidationResult(valid=False, reason="The response invents a location not known to this character.")

        return ValidationResult(valid=True, reason=None)

    def _contains_unknown_character(self, lower_dialogue: str) -> bool:
        # Allow reasonably common words and pronouns while rejecting obvious fabricated names.
        quoted = re.findall(r"\b[A-Z][a-z]+\b", lower_dialogue)
        if not quoted:
            return False
        for word in quoted:
            if word.lower() in {"i", "you", "we", "they", "amaka", "chuka", "sandra", "mr", "adeyemi"}:
                continue
            return True
        return False


class ConversationService:
    def __init__(self, game_state: Any, story_state: dict[str, Any] | None = None, provider: AIProvider | None = None) -> None:
        self.game_state = game_state
        self.story_state = story_state if story_state is not None else {"flags": {}, "relationship_scores": {}, "memories": [], "recent_conversation": []}
        self.provider = provider or MockAIProvider()

    def process(self, character_id: str, player_message: str, provider: AIProvider | None = None) -> AIResponse:
        intent = IntentParser().parse(player_message)
        context = ContextBuilder().build(self.game_state, self.story_state, character_id, player_message)

        chosen_provider = provider or self.provider
        try:
            response = chosen_provider.generate_response(context, player_message)
        except Exception:
            response = self._fallback_response(character_id, intent, context, reason="provider_failed")

        response.intent = response.intent if response.intent in ALLOWED_INTENTS else intent.intent
        if response.relationship_effect is None:
            response.relationship_effect = "NONE"
        if response.relationship_effect not in ALLOWED_RELATIONSHIP_EFFECTS:
            response.relationship_effect = "NONE"

        validation = ResponseValidator().validate(response, context)
        if not validation.valid:
            response = self._fallback_response(character_id, intent, context, reason=validation.reason)

        response.requires_validation = False
        response.validated = True

        self.story_state.setdefault("recent_conversation", [])
        self.story_state["recent_conversation"].append(f"player: {player_message}")
        self.story_state["recent_conversation"].append(f"{character_id}: {response.dialogue}")

        return response

    def _fallback_response(self, character_id: str, intent: ConversationIntent, context: ConversationContext, reason: str | None = None) -> AIResponse:
        lower_char = character_id.lower()
        if lower_char == "amaka":
            base = "You do not have to know everyone on day one. Just take a breath and tell me what you need."
            if intent.intent == "APOLOGIZE":
                base = "I am still listening. You do not have to be perfect on the first day."
            elif intent.intent == "HELP":
                base = "We can start with one thing at a time. What feels most confusing right now?"
            elif intent.intent == "INSULT":
                base = "That is not helpful. If you want to talk seriously, say it without the edge."
        elif lower_char == "chuka":
            base = "Let us keep it simple. We can talk it through without making it heavy."
        elif lower_char == "sandra":
            base = "Take your time. I will listen before I ask anything more."
        else:
            base = "I am listening. We can keep this simple and steady."

        return AIResponse(
            dialogue=base,
            emotion="calm",
            tone="gentle",
            intent=intent.intent,
            memory_candidate=False,
            relationship_effect="NONE",
            requires_validation=False,
            validated=True,
        )


__all__ = [
    "AIProvider",
    "AIResponse",
    "ALLOWED_INTENTS",
    "ALLOWED_RELATIONSHIP_EFFECTS",
    "ContextBuilder",
    "ConversationContext",
    "ConversationIntent",
    "ConversationService",
    "IntentParser",
    "MockAIProvider",
    "ResponseValidator",
    "ValidationResult",
]
