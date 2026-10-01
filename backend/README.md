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

## Run tests

From the `backend` directory, with the virtual environment active:

```powershell
pytest
```
