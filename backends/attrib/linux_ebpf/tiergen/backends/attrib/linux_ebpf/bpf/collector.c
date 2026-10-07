// SPDX-License-Identifier: GPL-3.0-or-later
/* tiergen-attrib-collector: load the programs, attach them, print events as JSON lines.
 *
 *   tiergen-attrib-collector --depth N --out FILE CGROUP_PATH...
 *
 * The first line is a "start" event stamped with the wall clock, which also tells the
 * caller the collector is attached. Boot-time stamps from the kernel are shifted by the
 * wall-minus-boot offset taken at start, so every line is on the host's wall clock. SIGINT
 * or SIGTERM ends the collector after it has drained what is pending. */
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <bpf/libbpf.h>
#include "attrib.skel.h"

struct event {
    unsigned long long ts, cg, container_cg, sk;
    unsigned pid, tgid, saddr, daddr;
    unsigned short sport, dport;
    unsigned char kind, proto;
};

static const char *KINDS[] = {"?", "connect", "accept", "close", "udp_send", "udp_recv", "packet"};
static volatile sig_atomic_t stopping = 0;
static FILE *out;
static long long offset_ns; /* wall clock minus boot clock, nanoseconds */

static void on_signal(int sig) { (void)sig; stopping = 1; }

static long long now_ns(clockid_t clk)
{
    struct timespec ts;
    clock_gettime(clk, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

static const char *proto_name(unsigned char p)
{
    switch (p) {
    case 6: return "tcp";
    case 17: return "udp";
    case 1: return "icmp";
    default: return "other";
    }
}

static void addr(char *buf, unsigned a)
{
    struct in_addr in = {.s_addr = a};
    strcpy(buf, inet_ntoa(in));
}

static int handle(void *ctx, void *data, size_t len)
{
    (void)ctx;
    if (len < sizeof(struct event))
        return 0;
    const struct event *e = data;
    char src[16], dst[16];
    addr(src, e->saddr);
    addr(dst, e->daddr);
    fprintf(out,
            "{\"ev\":\"%s\",\"ts_ns\":%lld,\"cg\":%llu,\"container_cg\":%llu,\"pid\":%u,"
            "\"tgid\":%u,\"proto\":\"%s\",\"src\":\"%s\",\"sport\":%u,\"dst\":\"%s\","
            "\"dport\":%u,\"sk\":%llu}\n",
            KINDS[e->kind > 6 ? 0 : e->kind], (long long)e->ts + offset_ns, e->cg, e->container_cg,
            e->pid, e->tgid, proto_name(e->proto), src, e->sport, dst, e->dport, e->sk);
    fflush(out);
    return 0;
}

int main(int argc, char **argv)
{
    unsigned depth = 2;
    const char *path = NULL;
    int i = 1;
    for (; i < argc; i++) {
        if (!strcmp(argv[i], "--depth") && i + 1 < argc)
            depth = (unsigned)atoi(argv[++i]);
        else if (!strcmp(argv[i], "--out") && i + 1 < argc)
            path = argv[++i];
        else
            break;
    }
    if (!path || i >= argc) {
        fprintf(stderr, "usage: %s --depth N --out FILE CGROUP_PATH...\n", argv[0]);
        return 2;
    }
    out = fopen(path, "a");
    if (!out) {
        perror(path);
        return 1;
    }
    libbpf_set_strict_mode(LIBBPF_STRICT_ALL);
    struct attrib_bpf *skel = attrib_bpf__open();
    if (!skel) {
        fprintf(stderr, "cannot open the programs\n");
        return 1;
    }
    skel->rodata->depth = depth;
    if (attrib_bpf__load(skel)) {
        fprintf(stderr, "cannot load the programs (BTF, privileges?)\n");
        return 1;
    }
    if (attrib_bpf__attach(skel)) {
        fprintf(stderr, "cannot attach the probes\n");
        return 1;
    }
    for (; i < argc; i++) {
        int fd = open(argv[i], O_RDONLY);
        if (fd < 0) {
            perror(argv[i]);
            return 1;
        }
        if (!bpf_program__attach_cgroup(skel->progs.packet_egress, fd)) {
            fprintf(stderr, "cannot attach to cgroup %s: %s\n", argv[i], strerror(errno));
            return 1;
        }
    }
    offset_ns = now_ns(CLOCK_REALTIME) - now_ns(CLOCK_BOOTTIME);
    struct ring_buffer *rb = ring_buffer__new(bpf_map__fd(skel->maps.events), handle, NULL, NULL);
    if (!rb) {
        fprintf(stderr, "cannot read the events\n");
        return 1;
    }
    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);
    fprintf(out,
            "{\"ev\":\"start\",\"ts_ns\":%lld,\"cg\":0,\"container_cg\":0,\"pid\":%u,\"tgid\":%u,"
            "\"proto\":\"other\",\"src\":\"\",\"sport\":0,\"dst\":\"\",\"dport\":0,\"sk\":0}\n",
            now_ns(CLOCK_REALTIME), (unsigned)getpid(), (unsigned)getpid());
    fflush(out);
    while (!stopping) {
        int n = ring_buffer__poll(rb, 200);
        if (n < 0 && n != -EINTR)
            break;
    }
    ring_buffer__consume(rb);
    fflush(out);
    fclose(out);
    attrib_bpf__destroy(skel);
    return 0;
}
