import json

import pytest

from aurora.scenarios import REFERENCE_SCENARIOS, load_scenarios, save_scenarios
from aurora.types import Scenario


def test_reference_scenarios_are_unique_and_valid():
    names = [scenario.name for scenario in REFERENCE_SCENARIOS]
    assert len(names) == len(set(names))
    for scenario in REFERENCE_SCENARIOS:
        scenario.validate()


def test_manifest_roundtrip(tmp_path):
    path = save_scenarios(tmp_path / "scenarios.json", REFERENCE_SCENARIOS[:2])
    assert load_scenarios(path) == REFERENCE_SCENARIOS[:2]


def test_manifest_rejects_unknown_schema(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"schema_version": "9", "scenarios": []}))
    with pytest.raises(ValueError, match="schema_version"):
        load_scenarios(path)


def test_manifest_rejects_empty_scenarios(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"schema_version": "1.0", "scenarios": []}))
    with pytest.raises(ValueError, match="no scenarios"):
        load_scenarios(path)


def test_manifest_rejects_duplicate_names(tmp_path):
    path = tmp_path / "bad.json"
    payload = {
        "schema_version": "1.0",
        "scenarios": [Scenario(name="same").to_dict(), Scenario(name="same").to_dict()],
    }
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="unique"):
        load_scenarios(path)
