#!/bin/sh
# What a Linux guest runs first, through the guest agent: mounts the run ISO, gives each
# interface its planned address by MAC, installs the agent's wheels, and starts the agent
# held at its gate. Everything it needs is on the ISO; host.json says what this host is.
set -eu
MOUNT=/mnt/tiergen
OUT=/tiergen/out
mkdir -p "$MOUNT" "$OUT" /tiergen
if ! mountpoint -q "$MOUNT"; then
    mount -o ro LABEL=TIERGEN "$MOUNT" 2>/dev/null || mount -o ro /dev/sr0 "$MOUNT"
fi
python3 - "$MOUNT/host.json" <<'EOF'
import json, subprocess, sys
host = json.load(open(sys.argv[1]))
by_mac = {}
for name in __import__("os").listdir("/sys/class/net"):
    try:
        by_mac[open(f"/sys/class/net/{name}/address").read().strip().lower()] = name
    except OSError:
        pass
for a in host["attachments"]:
    dev = by_mac[a["mac"].lower()]
    subprocess.run(["ip", "link", "set", dev, "up"], check=True)
    subprocess.run(["ip", "addr", "replace", f"{a['address']}/{a['prefix']}", "dev", dev], check=True)
for r in host["routes"]:
    subprocess.run(["ip", "route", "replace", r["cidr"], "via", r["via"]], check=True)
subprocess.run(["hostnamectl", "set-hostname", host["hostname"]], check=False)
if host["forwards"]:
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)
EOF
pip install --quiet --no-index --no-deps --break-system-packages "$MOUNT"/wheels/*.whl
cd /tiergen
nohup tiergen-agent "$MOUNT/run/$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['program'])" "$MOUNT/host.json")" --out "$OUT" --go /tiergen/go > /tiergen/bootstrap.log 2>&1 &
echo "agent started"
