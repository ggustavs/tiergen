"""Stands in for dumpcap: writes a small pcapng for the -i interfaces, then waits for SIGINT."""

import signal
import sys
import time
from pathlib import Path

from tiergen.runtime.capture.pcapng import Interface, Packet, Writer

args = sys.argv[1:]
file = Path(args[args.index("-w") + 1])
names = [args[i + 1] for i, a in enumerate(args) if a == "-i"]
frame = bytes(range(14)) + b"fake"
with file.open("wb") as f:
    writer = Writer(f, "fake-dumpcap")
    for name in names:
        writer.add_interface(Interface(name))
    for i in range(len(names)):
        writer.write_packet(Packet(i, 1_700_000_000_000_000_000 + i, frame))


def _exit(signum: int, frame: object) -> None:
    sys.exit(0)


signal.signal(signal.SIGINT, _exit)
print("capturing", file=sys.stderr, flush=True)
while True:
    time.sleep(0.05)
