# Guest templates

The libvirt backend clones every guest from a template volume in the `tiergen` storage pool
(`/var/lib/libvirt/images/tiergen`, made through libvirt, so nothing under it needs your
permissions). `build.py` makes the templates once, with internet through libvirt's `default`
NAT network; runs never have internet.

## Media

Downloaded, not redistributed; the evaluation licences are Microsoft's and expire (180 days
for Server, 90 for the client).

| file | source | size |
|---|---|---|
| `debian-13-genericcloud-amd64.qcow2` | https://cloud.debian.org/images/cloud/trixie/latest/ | 0.4 GB |
| `server2022-eval.iso` | https://go.microsoft.com/fwlink/p/?LinkID=2195280&clcid=0x409&culture=en-us&country=US (Windows Server 2022 evaluation, Evaluation Center) | 5.0 GB |
| `win10-ltsc2021-eval.iso` | https://go.microsoft.com/fwlink/p/?LinkID=2195404&clcid=0x409&culture=en-us&country=US (Windows 10 Enterprise LTSC 2021 evaluation) | 4.9 GB |
| `virtio-win/virtio-win-0.1.302.iso` | https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso (redirects to the release) | 0.9 GB |
| `windows/python-3.12.10-amd64.exe` | https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe (3.12's last Windows installer; the Windows CI job runs 3.12) | 27 MB |
| `windows/Sysmon.zip` | https://download.sysinternals.com/files/Sysmon.zip (unversioned URL) | 3 MB |

Keep them under `~/.local/share/tiergen/media/`; `build.py` uploads what it needs into the
pool. Debian 12 ships Python 3.11, below the workspace's 3.12, which is why the Linux
template is Debian 13. fedorapeople puts a browser check in front of browser user agents;
`curl -L` with its own gets the file. No checksum is published for the virtio-win ISO, only
for the RPMs that carry it, so these are the SHA-256 sums of the files the templates were
built from (2026-10-12):

```
303f7ae40dad495d6ae474fdc571df58958a4dbc5c37a522d80f9a203867949d  virtio-win-0.1.302.iso
3e4fa6d8507b554856fc9ca6079cc402df11a8b79344871669f0251535255325  server2022-eval.iso
e4ab2e3535be5748252a8d5d57539a6e59be8d6726345ee10e7afd2cb89fefb5  win10-ltsc2021-eval.iso
67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb  python-3.12.10-amd64.exe
00ecf1b46aec99299d3ae0bca79dc621458bd014b20b509d7c5c8e8c8611aa54  Sysmon.zip
```

## Linux

```
uv run python scripts/templates/build.py linux --image ~/.local/share/tiergen/media/debian-13-genericcloud-amd64.qcow2
```

Boots the cloud image once with `linux/user-data` and `linux/network-config` (a static
address on the NAT, `192.168.122.250`, with public name servers, matched by interface name
rather than MAC; a host firewall such as `ufw` with a drop policy swallows a guest's DHCP
and DNS requests into `virbr0` while forwarding still works, which stalled the first
builds, so neither is relied on):
Python, pip, httpx, nmap, nginx, ethtool, the QEMU guest agent and `libbpf1` for the
attribution collector, the distribution's nginx disabled, root's password `tiergen` for the console when something needs looking at. Once
the agent answers, the build waits for cloud-init through it, checks the packages, reads
cloud-init's log back when something failed, removes the build's network configuration and
disables cloud-init so a run's guest inherits neither, and powers the guest off; the volume
is `template-linux-agent.qcow2`. The agent's own packages are not in the template: each run
builds them into wheels on its ISO, so a source change needs no rebuild. The first build
without the explicit network configuration failed on name resolution and powered off
regardless, which is why the build now watches the guest instead of trusting it.

## Windows

```
uv run python scripts/templates/build.py windows --iso ~/.local/share/tiergen/media/win10-ltsc2021-eval.iso
```

The workstation template, `template-windows-agent.qcow2`, by unattended install onto an
empty 64 GB disk. Three CDs: the Windows ISO, virtio-win, and a build CD (`TGBUILD`) the
script writes with `windows/autounattend.xml` at its root, `windows/setup.ps1`,
`windows/provision.ps1`, `windows/sysmon.xml`, the Python installer, Sysmon, and the
agent's third-party wheels for CPython 3.12 on Windows, pinned by `uv.lock`. The install
CD's boot loader waits for a key, so the script presses one for the first half minute. In
WinPE the answer file loads virtio's storage, network and serial drivers, so the installed
system boots from the virtio disk the backend gives every clone; it partitions for UEFI,
sets the time zone to UTC (libvirt's real-time clock is UTC), and creates the `tiergen`
administrator, password `Tiergen-2026!`, which also becomes the built-in Administrator's.
At first logon `setup.ps1` installs the virtio guest tools and the QEMU guest agent. From
there the build drives the guest through the agent: `provision.ps1` installs Python to
`C:\Python312`, the wheels, and Sysmon with `sysmon.xml` (process creation and termination,
network connections and DNS queries; everything high-volume off), turns hibernation off so
a clone boots cold, and removes the logon password from the registry; then the guest shuts
down. Nothing in the build uses the network, so the host firewall that stalled the Linux
builds does not matter here. The guest is not generalised (no sysprep): clones share the
template's machine SID, which isolated runs do not notice, and a domain-joined pair cloned
together stays joined. The build has a VNC display on the host's loopback
(`virsh -c qemu:///system vncdisplay tiergen-build-windows-agent`) for watching it. Install
media and virtio-win stay in the pool as `media-*` volumes for the next build.

The domain controller (Server 2022, promoted) and the join come next.
