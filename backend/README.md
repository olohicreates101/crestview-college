# Crestview College Backend

Phase 1 provides a minimal FastAPI service, environment-based settings, and a health check. No database or game systems are included yet.

## Requirements

- Python 3.12 or newer

## Set up on Windows PowerShell

From the `backend` directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks virtual environment activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again.

## Run the API

From the `backend` directory, with the virtual environment active:

```powershell
uvicorn app.main:app --reload
```

The health endpoint is available at <http://127.0.0.1:8000/health>.

## Phase 2 — Domain Models

Domain models define the game concepts used by Crestview College without depending on a database, request/response layer, or UI code. They capture the core world state for players, NPCs, relationships, memories, secrets, rumours, items, and story progression.

These models currently exist as plain Pydantic data structures only. They are intentionally independent of PostgreSQL, SQLAlchemy, Supabase, FastAPI request/response handling, and the Godot client. The database persistence layer will be added in Phase 3.

## Phase 3 — Database

Phase 3 adds PostgreSQL persistence for the existing Crestview College backend. The architecture keeps the domain layer separate from the database layer: Pydantic models remain the game-facing domain layer, SQLAlchemy models persist database state, and repository classes provide the conversion boundary.

The project uses SQLAlchemy 2.x for database access, PostgreSQL for storage, Alembic for migration management, and `psycopg` for the PostgreSQL driver. The database configuration is controlled through `DATABASE_URL`, which should point to a local PostgreSQL instance during development.

Local setup example:

```powershell
Copy-Item .env.example .env
# Edit .env to set DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/crestview
```

Migration commands:

```powershell
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

Test command:

```powershell
python -m pytest -q
```

The project does not add a new API layer for game state yet; the existing health endpoint continues to work and the database layer is kept separate from API logic.

## Phase 4 — Game State Engine

The game state engine is the rules layer for Crestview College. It tracks where the player is, what time it is, what the player can do, whether actions are valid, and what state changes happen after a valid action. The goal is to make gameplay decisions explicit, testable, and independent from AI, UI, and persistence code.

`GameState` holds the current world, clock, location, flags, and recent events. `GameEngine` validates and executes player actions, advances time, emits events, and returns structured `ActionResult` responses instead of throwing generic exceptions for normal gameplay rejections.

The game clock uses fictional school time rather than real-world time and defines the main periods used in-game: late night, morning, school day, afternoon, evening, and night. Locations are graph-based and movement is only valid when a connection exists between the current location and the intended destination.

Flags provide simple state tracking for story conditions and progression markers. They can be checked, set, and cleared without building a full story engine yet.

## Phase 5 — Story Engine

Phase 5 adds the data-driven story engine for the first authored episode: `SS1 — Term 1 — Episode 1`. The story is kept narrative-first and file-driven: JSON defines the episode, scenes, dialogue, choices, conditions, and consequences, while Python code interprets them and applies game-state-safe outcomes.

The main architecture is:

- `game-data/episodes/` stores the authored episode JSON
- `game-data/characters/` stores the narrative cast for the episode
- `game-data/locations/` stores location metadata
- `game-data/items/` stores item metadata used by the story layer
- `app/story_engine.py` loads and validates the data and controls progression
- `GameEngine` remains the validating movement/time layer underneath it

The story engine exposes the core responsibilities of an episode: load episode data, determine the active scene, check if a scene is available, return valid choices, apply consequences, move to the next scene, and mark completion. It does not bypass the game-state rules layer; movement and time changes are still executed through the validated `GameEngine` when needed.

The First Day episode opens at the school gate and follows the player through the classroom introduction, break time, the first meaningful conversation with Amaka, the social choice, the mystery message, and the end-of-day hook. The story remains intentionally manageable and convergent, rather than creating a large branching tree.

The condition system accepts controlled types only: `FLAG_TRUE`, `FLAG_FALSE`, `LOCATION_IS`, `TIME_BEFORE`, `TIME_AFTER`, and `RELATIONSHIP_AT_LEAST`. The consequence system accepts controlled types only: `SET_FLAG`, `CLEAR_FLAG`, `ADVANCE_TIME`, `MOVE_PLAYER`, `ADD_ITEM`, `REMOVE_ITEM`, `ADD_MONEY`, `CHANGE_RELATIONSHIP`, `ADD_MEMORY`, and `CHANGE_REPUTATION`.

To run the story-engine tests:

```powershell
python -m pytest -q tests/test_story_engine.py
```

## Phase 7 — Controlled AI Conversation

Phase 7 introduces a controlled AI conversation pipeline that keeps the game engine as the source of truth. The AI can interpret a player message, identify intent, generate character-appropriate dialogue, and propose safe relationship effects, but it cannot directly mutate `GameState`, create secrets, alter world state, or decide story progression. All game-affecting outcomes remain validated and applied by the existing rules layer.

The architecture is intentionally narrow:

- `ConversationIntent` captures the parsed intent and metadata.
- `ConversationContext` creates a limited view of the player, character, relationship, flags, and relevant memory only.
- `AIProvider` defines the provider abstraction for model access.
- `MockAIProvider` is deterministic and offline-friendly for tests.
- `IntentParser` classifies a player message into a controlled set of intents such as `TALK`, `ASK`, `LIE`, `APOLOGIZE`, `HELP`, `REFUSE`, `AGREE`, `DISAGREE`, `INVESTIGATE`, and `LEAVE`.
- `ContextBuilder` filters the context down to relevant details and avoids hidden or private knowledge.
- `ResponseValidator` rejects invented names, invented locations, made-up secrets, forbidden knowledge, and direct state-modifying instructions.
- `ConversationService` coordinates parsing, context building, AI generation, validation, and fallback behavior.
- `StoryEngine.start_ai_conversation()` adds a controlled first-day Amaka interaction without changing the existing narrative flow or allowing AI to be the director of the story.

Fallback behavior is character-specific and kept light. If the provider fails or a response is invalid, the system uses a safe authored fallback line instead of a generic "Sorry, I don't understand." response.

### Why the AI cannot control the game state

The AI is treated as a character actor, not a world-authoring system. It may generate dialogue and tone, but it cannot directly set flags, change money, create items, move the player, or decide hidden story progression. Any approved effect is treated as a proposed consequence and must pass validation before the game engine or story layer may act on it.

## Phase 9 — Persistence and Save/Load

Phase 9 adds a game-save persistence layer that serializes the current `GameState` and a runtime snapshot into PostgreSQL without replacing the in-memory runtime model. The architecture keeps the database as a durable store and the active `GameState` as the authoritative runtime state. Save data is versioned and validated before it is reloaded.

### Save architecture

- `app/persistence/save_service.py` owns serialization, validation, and load logic.
- `app/db/models/save.py` stores a single save record with `game_version`, `schema_version`, and the serialized payload.
- `GameSaveService.save_game()` writes a complete snapshot in a transaction.
- `GameSaveService.load_game()` validates the schema and restores the `GameState` world, clock, flags, and runtime data.
- A save can preserve runtime details such as inventory, relationship state, phone state, story progress, secrets, rumours, memory records, and NPC runtime state.

### Save versioning

The persistence layer uses a simple versioned schema:

- `game_version`: current game version label
- `schema_version`: monotonically increasing save schema version

Older saves are rejected with a clear validation error instead of being silently altered.

### API endpoints

The existing FastAPI app now includes minimal persistence endpoints:

```http
POST /saves
GET /saves
GET /saves/{save_id}
DELETE /saves/{save_id}
```

These endpoints accept or return JSON-safe data only. They do not expose SQLAlchemy models directly.

### Persistence tests

To run the save/load tests:

```powershell
python -m pytest -q tests/test_persistence.py
```

### PostgreSQL requirements

The project keeps PostgreSQL support alongside the existing SQLAlchemy setup. If a local PostgreSQL instance is not configured, the repository-layer database tests remain skipped as before. The save/load logic itself is tested without needing a running database.

### Known limitations

- The persistence layer is intentionally focused on explicit JSON-safe serialization and validation.
- It does not add a full autosave scheduler or multi-slot save management yet.
- It preserves the runtime snapshot the project already supports, but does not invent a new gameplay engine or duplicate the existing `GameState` model.

## Run tests

From the `backend` directory, with the virtual environment active:

```powershell
pytest
```
