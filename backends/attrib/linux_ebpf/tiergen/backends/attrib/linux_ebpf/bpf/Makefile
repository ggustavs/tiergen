# Built inside the collector image; nothing here runs on the host.
CLANG ?= clang
BPFTOOL ?= bpftool
ARCH ?= x86

all: tiergen-attrib-collector

# The uapi headers include <asm/types.h>, which Debian keeps under the multiarch directory
# that a bpf-target clang does not search on its own.
MULTIARCH := $(shell $(CC) -print-multiarch)

attrib.bpf.o: attrib.bpf.c vmlinux_min.h
	$(CLANG) -O2 -g -target bpf -D__TARGET_ARCH_$(ARCH) -I/usr/include/$(MULTIARCH) -Wall -c $< -o $@

attrib.skel.h: attrib.bpf.o
	$(BPFTOOL) gen skeleton $< > $@

tiergen-attrib-collector: collector.c attrib.skel.h
	$(CC) -O2 -Wall -o $@ $< -lbpf -lelf -lz

clean:
	rm -f attrib.bpf.o attrib.skel.h tiergen-attrib-collector
