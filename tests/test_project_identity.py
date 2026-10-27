from importlib.util import find_spec
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_quanta_package_is_importable():
    assert find_spec("quanta") is not None


def test_project_metadata_uses_quanta_name():
    with (ROOT / "pyproject.toml").open("rb") as file:
        project = tomllib.load(file)["project"]

    assert project["name"] == "assignment2-quanta"
