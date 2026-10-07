/* Who caused which connection, from the kernel's side.
 *
 * Every event carries the cgroup of the task or socket that caused it and the cgroup of
 * the container it ran in, the ancestor at a depth the loader sets, so user space never
 * resolves a path after the fact. Addresses are IPv4; ports are host order; timestamps are
 * boot-time nanoseconds the loader shifts onto the wall clock. */
#include "vmlinux_min.h"
#include <linux/bpf.h>
#include <linux/in.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
#include <bpf/bpf_endian.h>

#define AF_INET 2
#define ETH_P_IP 0x0800

enum kind { EV_CONNECT = 1, EV_ACCEPT, EV_CLOSE, EV_UDP_SEND, EV_UDP_RECV, EV_PACKET };

struct event {
    __u64 ts;
    __u64 cg;
    __u64 container_cg;
    __u64 sk;
    __u32 pid;
    __u32 tgid;
    __u32 saddr;
    __u32 daddr;
    __u16 sport;
    __u16 dport;
    __u8 kind;
    __u8 proto;
};

/* The depth of the containers' cgroups: 2 for /system.slice/docker-<id>.scope. */
const volatile __u32 depth = 2;

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 22);
} events SEC(".maps");

struct entry {
    __u64 sk;
    __u64 msg;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 4096);
    __type(key, __u64);
    __type(value, struct entry);
} inflight SEC(".maps"); /* pid_tgid -> what a function was called with, for its return probe */

struct flow {
    __u64 cg;
    __u32 saddr;
    __u32 daddr;
    __u16 sport;
    __u16 dport;
    __u8 proto;
};

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 65536);
    __type(key, struct flow);
    __type(value, __u8);
} seen SEC(".maps"); /* flows already reported by the packet hook */

static __always_inline struct event *reserve(__u8 kind)
{
    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;
    __u64 id = bpf_get_current_pid_tgid();
    e->kind = kind;
    e->ts = bpf_ktime_get_boot_ns();
    e->cg = bpf_get_current_cgroup_id();
    e->container_cg = bpf_get_current_ancestor_cgroup_id(depth);
    e->tgid = id >> 32;
    e->pid = (__u32)id;
    e->sk = 0;
    e->proto = 0;
    e->saddr = e->daddr = 0;
    e->sport = e->dport = 0;
    return e;
}

/* The socket's own view: local address and port, remote address and port. */
static __always_inline void fill_sock(struct event *e, struct sock *sk)
{
    e->sk = (__u64)sk;
    e->saddr = BPF_CORE_READ(sk, __sk_common.skc_rcv_saddr);
    e->sport = BPF_CORE_READ(sk, __sk_common.skc_num);
    e->daddr = BPF_CORE_READ(sk, __sk_common.skc_daddr);
    e->dport = bpf_ntohs(BPF_CORE_READ(sk, __sk_common.skc_dport));
}

SEC("kprobe/tcp_v4_connect")
int BPF_KPROBE(connect_entry, struct sock *sk)
{
    __u64 id = bpf_get_current_pid_tgid();
    struct entry in = {.sk = (__u64)sk, .msg = 0};
    bpf_map_update_elem(&inflight, &id, &in, BPF_ANY);
    return 0;
}

SEC("kretprobe/tcp_v4_connect")
int BPF_KRETPROBE(connect_return, int ret)
{
    __u64 id = bpf_get_current_pid_tgid();
    struct entry *in = bpf_map_lookup_elem(&inflight, &id);
    if (!in)
        return 0;
    struct sock *sk = (struct sock *)in->sk;
    bpf_map_delete_elem(&inflight, &id);
    if (ret != 0)
        return 0;
    struct event *e = reserve(EV_CONNECT);
    if (!e)
        return 0;
    e->proto = IPPROTO_TCP;
    fill_sock(e, sk);
    bpf_ringbuf_submit(e, 0);
    return 0;
}

SEC("kretprobe/inet_csk_accept")
int BPF_KRETPROBE(accept_return, struct sock *newsk)
{
    if (!newsk)
        return 0;
    if (BPF_CORE_READ(newsk, __sk_common.skc_family) != AF_INET)
        return 0;
    struct event *e = reserve(EV_ACCEPT);
    if (!e)
        return 0;
    e->proto = IPPROTO_TCP;
    fill_sock(e, newsk);
    bpf_ringbuf_submit(e, 0);
    return 0;
}

SEC("kprobe/tcp_close")
int BPF_KPROBE(close_entry, struct sock *sk)
{
    if (BPF_CORE_READ(sk, __sk_common.skc_family) != AF_INET)
        return 0;
    struct event *e = reserve(EV_CLOSE);
    if (!e)
        return 0;
    e->proto = IPPROTO_TCP;
    fill_sock(e, sk);
    bpf_ringbuf_submit(e, 0);
    return 0;
}

/* The destination of an unconnected UDP send is in the message, in user memory. */
static __always_inline void fill_udp_peer(struct event *e, struct msghdr *msg)
{
    void *name = BPF_CORE_READ(msg, msg_name);
    int len = BPF_CORE_READ(msg, msg_namelen);
    struct sockaddr_in addr;
    if (!name || len < (int)sizeof(addr))
        return;
    if (bpf_probe_read_user(&addr, sizeof(addr), name))
        return;
    if (addr.sin_family != AF_INET)
        return;
    e->daddr = addr.sin_addr.s_addr;
    e->dport = bpf_ntohs(addr.sin_port);
}

SEC("kprobe/udp_sendmsg")
int BPF_KPROBE(udp_send_entry, struct sock *sk, struct msghdr *msg)
{
    struct event *e = reserve(EV_UDP_SEND);
    if (!e)
        return 0;
    e->proto = IPPROTO_UDP;
    fill_sock(e, sk);
    fill_udp_peer(e, msg);
    bpf_ringbuf_submit(e, 0);
    return 0;
}

SEC("kprobe/udp_recvmsg")
int BPF_KPROBE(udp_recv_entry, struct sock *sk, struct msghdr *msg)
{
    __u64 id = bpf_get_current_pid_tgid();
    struct entry in = {.sk = (__u64)sk, .msg = (__u64)msg};
    bpf_map_update_elem(&inflight, &id, &in, BPF_ANY);
    return 0;
}

SEC("kretprobe/udp_recvmsg")
int BPF_KRETPROBE(udp_recv_return, int ret)
{
    __u64 id = bpf_get_current_pid_tgid();
    struct entry *in = bpf_map_lookup_elem(&inflight, &id);
    if (!in)
        return 0;
    struct sock *sk = (struct sock *)in->sk;
    struct msghdr *msg = (struct msghdr *)in->msg;
    bpf_map_delete_elem(&inflight, &id);
    if (ret < 0)
        return 0;
    struct event *e = reserve(EV_UDP_RECV);
    if (!e)
        return 0;
    e->proto = IPPROTO_UDP;
    fill_sock(e, sk);      /* the local side */
    e->daddr = 0;
    e->dport = 0;
    fill_udp_peer(e, msg); /* the peer that sent what was received, as daddr/dport */
    bpf_ringbuf_submit(e, 0);
    return 0;
}

/* Every packet a socket in the container sends, raw sockets included: one event per
 * (cgroup, flow), so a scan costs one event per port. Local address first, as the
 * packet carries it. */
SEC("cgroup_skb/egress")
int packet_egress(struct __sk_buff *skb)
{
    if (skb->protocol != bpf_htons(ETH_P_IP))
        return 1;
    struct iphdr ip;
    if (bpf_skb_load_bytes(skb, 0, &ip, sizeof(ip)))
        return 1;
    struct flow f = {};
    f.cg = bpf_skb_cgroup_id(skb);
    f.saddr = ip.saddr;
    f.daddr = ip.daddr;
    f.proto = ip.protocol;
    __u32 off = ip.ihl * 4;
    if (ip.protocol == IPPROTO_TCP || ip.protocol == IPPROTO_UDP) {
        __be16 ports[2];
        if (bpf_skb_load_bytes(skb, off, ports, sizeof(ports)) == 0) {
            f.sport = bpf_ntohs(ports[0]);
            f.dport = bpf_ntohs(ports[1]);
        }
    }
    if (bpf_map_lookup_elem(&seen, &f))
        return 1;
    __u8 one = 1;
    bpf_map_update_elem(&seen, &f, &one, BPF_ANY);
    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 1;
    e->kind = EV_PACKET;
    e->ts = bpf_ktime_get_boot_ns();
    e->cg = f.cg;
    e->container_cg = bpf_skb_ancestor_cgroup_id(skb, depth);
    e->pid = e->tgid = 0; /* no task is reliably current on the egress path */
    e->sk = 0;
    e->proto = f.proto;
    e->saddr = f.saddr;
    e->daddr = f.daddr;
    e->sport = f.sport;
    e->dport = f.dport;
    bpf_ringbuf_submit(e, 0);
    return 1;
}

char LICENSE[] SEC("license") = "GPL";
