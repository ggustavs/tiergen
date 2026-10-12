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
| `virtio-win.iso` | https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso | 0.7 GB |

Keep them under `~/.local/share/tiergen/media/`; `build.py` uploads what it needs into the
pool. Debian 12 ships Python 3.11, below the workspace's 3.12, which is why the Linux
template is Debian 13.

## Linux

```
uv run python scripts/templates/build.py linux --image ~/.local/share/tiergen/media/debian-13-genericcloud-amd64.qcow2
```

Boots the cloud image once with `linux/user-data` and `linux/network-config` (a static
address on the NAT, `192.168.122.250`, with public name servers, matched by interface name
rather than MAC; a host firewall such as `ufw` with a drop policy swallows a guest's DHCP
and DNS requests into `virbr0` while forwarding still works, which stalled the first
builds, so neither is relied on):
Python, pip, httpx, nmap, nginx, ethtool and the QEMU guest agent, the distribution's nginx
disabled, root's password `tiergen` for the console when something needs looking at. Once
the agent answers, the build waits for cloud-init through it, checks the packages, reads
cloud-init's log back when something failed, removes the build's network configuration and
disables cloud-init so a run's guest inherits neither, and powers the guest off; the volume
is `template-linux-agent.qcow2`. The agent's own packages are not in the template: each run
builds them into wheels on its ISO, so a source change needs no rebuild. The first build
without the explicit network configuration failed on name resolution and powered off
regardless, which is why the build now watches the guest instead of trusting it.

## Windows

To come: the domain controller (Server 2022, promoted) and the workstation (Windows 10
LTSC, joined), by unattended install with the virtio drivers and the guest agent from
`virtio-win.iso`, then Python and Sysmon.
