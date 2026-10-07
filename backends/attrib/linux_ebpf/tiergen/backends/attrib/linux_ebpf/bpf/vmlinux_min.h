// SPDX-License-Identifier: GPL-2.0-or-later
/* The kernel types the programs touch, no more. Every struct is marked for CO-RE, so
 * field offsets are relocated against the running kernel's BTF at load time; the layout
 * written here only has to name the fields, not place them. Wire formats (IP, TCP, UDP
 * headers, sockaddr_in) come from the uapi headers instead. */
#ifndef __VMLINUX_H__
#define __VMLINUX_H__

#include <linux/types.h>

struct pt_regs {
    unsigned long r15, r14, r13, r12, bp, bx, r11, r10, r9, r8, ax, cx, dx, si, di, orig_ax,
        ip, cs, flags, sp, ss;
};

struct sock_common {
    union {
        __u32 skc_daddr;
    };
    union {
        __u32 skc_rcv_saddr;
    };
    union {
        struct {
            __be16 skc_dport;
            __u16 skc_num;
        };
    };
    unsigned short skc_family;
} __attribute__((preserve_access_index));

struct sock {
    struct sock_common __sk_common;
} __attribute__((preserve_access_index));

struct msghdr {
    void *msg_name;
    int msg_namelen;
} __attribute__((preserve_access_index));

#endif
