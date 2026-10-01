import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "game-data"


def _load_items():
    items = []
    for path in sorted(ROOT.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            for entry in payload:
                if isinstance(entry, dict):
                    items.append((path.relative_to(ROOT).as_posix(), entry))
        elif isinstance(payload, dict):
            items.append((path.relative_to(ROOT).as_posix(), payload))
    return items


def test_game_data_ids_are_unique_and_placeholder_free():
    seen = {}
    for rel_path, item in _load_items():
        item_id = item.get("id")
        if item_id:
            assert item_id not in seen, f"Duplicate ID {item_id!r} in {seen[item_id]} and {rel_path}"
            seen[item_id] = rel_path

        serialized = json.dumps(item)
        assert "TODO" not in serialized, f"Placeholder TODO found in {rel_path}"


def test_game_data_references_point_to_real_ids():
    items = _load_items()

    location_ids = {
        item["id"]
        for _, item in items
        if isinstance(item, dict) and "id" in item and item.get("category") in {"core_school", "boarding", "outside_school", "core", "science", "technology", "social_science", "arts", "physical", "commercial", "religion", "elective", "school_cycle", "school_culture", "competition", "club_activity", "academic", "discipline", "appearance", "technology", "movement", "social", "boarding", "institutional"}
    }
    character_ids = {
        item["id"]
        for _, item in items
        if isinstance(item, dict) and "id" in item and item.get("class_or_role")
    }

    location_ids |= {
        "school_gate", "security_post", "assembly_ground", "corridors", "classrooms", "staff_room",
        "principal_admin_block", "library", "ict_lab", "science_lab", "canteen", "sick_bay",
        "sports_field", "hall", "notice_boards", "hostel_blocks", "dorm_rooms", "dining_hall",
        "hostel_courtyard", "bus_stop", "nearby_road", "small_shops", "friends_home"
    }

    character_ids |= {
        "amaka", "chuka", "sandra", "mr_adeyemi", "mysterious_student", "class_captain",
        "security_guard", "hostel_prefect", "school_nurse", "principal", "vice_principal",
        "head_boy", "head_girl", "school_librarian", "biology_teacher", "chemistry_teacher",
        "ict_teacher", "english_teacher", "sports_captain", "house_captain", "canteen_vendor",
        "bus_conductor", "shop_owner", "students", "prefects", "teachers", "boarders"
    }

    for rel_path, item in items:
        for key in ("related_locations", "locations", "common_locations", "associated_locations", "location"):
            values = item.get(key, [])
            if isinstance(values, str):
                values = [values]
            elif not isinstance(values, list):
                continue
            for ref in values:
                if isinstance(ref, str):
                    ref = ref.strip()
                    if not ref or not re.fullmatch(r"[a-z0-9_]+", ref):
                        continue
                    assert ref in location_ids, f"Unknown location reference {ref!r} in {rel_path}"

        for key in ("related_characters", "associated_npcs", "leaders", "leader"):
            values = item.get(key, [])
            if isinstance(values, str):
                values = [values]
            elif not isinstance(values, list):
                continue
            for ref in values:
                if isinstance(ref, str):
                    ref = ref.strip()
                    if not ref or not re.fullmatch(r"[a-z0-9_]+", ref):
                        continue
                    assert ref in character_ids, f"Unknown character reference {ref!r} in {rel_path}"
