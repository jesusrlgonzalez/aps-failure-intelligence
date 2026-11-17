"""Version identifiers and the P01 dossier agree with each other (Owner order A5, A5-D02)."""
import re
import tomllib
from pathlib import Path

import aps_intel

ROOT = Path(__file__).resolve().parents[1]
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


def test_package_version_fields_agree_with_the_changelog():
    latest = re.search(r"^## \[(\d+\.\d+\.\d+)\]", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M).group(1)
    cff = re.search(r'^version: "([^"]+)"', (ROOT / "CITATION.cff").read_text(encoding="utf-8"), re.M).group(1)
    assert VERSION == aps_intel.__version__ == cff == latest


def test_p01_dossier_names_this_release_and_has_no_open_publication_items():
    dossier = ROOT / "docs" / "pilots" / "P01"
    verdict = (dossier / "04_dictamen.md").read_text(encoding="utf-8")
    assert f"v{VERSION}" in (dossier / "README.md").read_text(encoding="utf-8")
    assert f"`v{VERSION}`" in verdict
    assert "Aceptación formal del OWNER: emitida" in verdict
    assert "**DEMOSTRACIÓN NIVEL A APROBADA CON RESERVAS**" in verdict
    g6 = next(line for line in verdict.splitlines() if line.startswith("| G6"))
    assert "| PASS |" in g6 and "pendiente" not in g6.lower()
