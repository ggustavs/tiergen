"""What the agent writes: ``invocations.jsonl``, one record per line, and ``agent.log``."""

import json
import logging
import os
import sys
from pathlib import Path

from tiergen.core.codec import from_json, to_json
from tiergen.core.records import InvocationRecord

RECORDS = "invocations.jsonl"
LOG = "agent.log"


class Recorder:
    """Appends records to ``out/invocations.jsonl``. Each record is one ``write`` on a file
    opened for appending, so the behaviour processes of one agent share the file."""

    def __init__(self, out: Path) -> None:
        self._fd = os.open(out / RECORDS, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)

    def write(self, record: InvocationRecord) -> None:
        os.write(self._fd, (json.dumps(to_json(record)) + "\n").encode("utf-8"))

    def close(self) -> None:
        os.close(self._fd)


def read_records(path: Path) -> list[InvocationRecord]:
    """The records in a file the ``Recorder`` wrote."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return [from_json(InvocationRecord, json.loads(line)) for line in lines if line]


def setup_logging(out: Path) -> logging.Logger:
    """The agent's logger, to ``out/agent.log`` and to stderr, process id on every line."""
    log = logging.getLogger("tiergen.agent")
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(process)d %(levelname)s %(message)s")
    for handler in (
        logging.FileHandler(out / LOG, encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ):
        handler.setFormatter(fmt)
        log.addHandler(handler)
    return log
