# The Linux agent's image: Python, the tools the first runtimes need, and the workspace
# packages the agent imports, installed from the build context that image.py assembles.
FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends nginx nmap iproute2 openssl ethtool \
    && rm -rf /var/lib/apt/lists/*
COPY . /src
RUN pip install --no-cache-dir /src/core /src/protocols /src/interfaces /src/impls/_base \
    /src/impls/httpx /src/impls/nginx /src/impls/nmap /src/runtime/agent_linux \
    && rm -rf /src
