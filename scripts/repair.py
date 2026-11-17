"""Entrada compatível com os compiladores anteriores durante a migração."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.repair_console import main

if __name__ == "__main__":
    raise SystemExit(main(globals().get("__compiled__"), entrada=__file__))
