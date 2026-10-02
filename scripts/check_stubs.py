"""Fail unless every stub package in uv.lock stubs the version of the package it is installed for.

A typeshed stub's version is the stubbed package's version plus a date, so ``types-docker
7.2.0.20260923`` stubs ``docker 7.2.0``. A bump of one without the other passes pyright
against the wrong signatures. Runs as a pre-commit hook and in the ``lock`` CI job.
"""

import sys
import tomllib
from pathlib import Path

PAIRS = [("docker", "types-docker")]


def main() -> int:
    lock = tomllib.loads(Path("uv.lock").read_text(encoding="utf-8"))
    versions = {p["name"]: p["version"] for p in lock["package"]}
    bad = 0
    for package, stub in PAIRS:
        have, stubbed = versions.get(package), versions.get(stub)
        if have is None or stubbed is None:
            print(f"{package}: {have}, {stub}: {stubbed}; both must be locked")
            bad = 1
        elif not stubbed.startswith(have + "."):
            print(f"{stub} {stubbed} does not stub {package} {have}")
            bad = 1
    if not bad:
        print("stubs match: " + ", ".join(f"{s} -> {p} {versions[p]}" for p, s in PAIRS))
    return bad


if __name__ == "__main__":
    sys.exit(main())
