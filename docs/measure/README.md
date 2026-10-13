# Measurements

Reports of the measurements behind design decisions, as the scripts under
`scripts/measure/` wrote them. Each script re-reads its raw output with `--report-only`; the
raw output (traces, captures, sensor logs) stays with whoever ran it.

| Report | Script | Date | Question |
|---|---|---|---|
| [windows-smb.md](windows-smb.md) | `windows_smb.py` | 2026-10-12 | Which events name the process behind an SMB connection? |
| [windows-kerberos.md](windows-kerberos.md) | `windows_kerberos.py` | 2026-10-12 | Which events name the process behind a Kerberos exchange? |
| [windows-links.md](windows-links.md) | `windows_links.py` | 2026-10-13 | What links a request to its traffic, on the host, on the wire and in each sensor's records? |

`windows-links.md` ran Suricata with `-k none`. With checksum validation on, Suricata
tracked none of the SMB connections and half of the Kerberos ones from the Windows
guests, whose virtio NICs offload checksums.
