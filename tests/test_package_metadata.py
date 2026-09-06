from pathlib import Path

import aurora


def test_version_matches_package_metadata_source():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    assert f'version = "{aurora.__version__}"' in text


def test_required_community_files_exist():
    root = Path(__file__).resolve().parents[1]
    for name in (
        "LICENSE",
        "README.md",
        ".github/CONTRIBUTING.md",
        ".github/CODE_OF_CONDUCT.md",
        ".github/SECURITY.md",
        "CITATION.cff",
    ):
        assert (root / name).is_file(), name
