# The collector's image: built once against the toolchain, run with only libbpf.
FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends \
    clang llvm bpftool libbpf-dev libelf-dev zlib1g-dev linux-libc-dev make gcc \
    && rm -rf /var/lib/apt/lists/*
COPY bpf /src
RUN make -C /src

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends libbpf1 libelf1 zlib1g \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/tiergen-attrib-collector /usr/local/bin/tiergen-attrib-collector
