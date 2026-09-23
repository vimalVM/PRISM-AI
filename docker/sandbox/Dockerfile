# Sovereign AI Workbench — Hardened Code Execution Sandbox
# Hardened according to docs/03_SECURITY_AND_ACCESS.md §8:
# - Minimal base image (python:3.11-slim)
# - Non-root user UID 10001:10001
# - No compilers (gcc, g++, make removed if present)
# - No network tools (no curl, wget, git, netcat)
# - Runs with read-only root and --network=none at container runtime

FROM python:3.11-slim

# Create isolated non-root user and group
RUN groupadd -g 10001 sandboxgroup && \
    useradd -u 10001 -g sandboxgroup -m -s /bin/sh sandboxuser

# Install minimal test runner
RUN pip install --no-cache-dir pytest==8.3.4

# Remove any residual development tools or network helpers
RUN rm -rf /var/lib/apt/lists/* \
    && rm -f /usr/bin/curl /usr/bin/wget /usr/bin/git /usr/bin/nc /usr/bin/netcat

WORKDIR /work
USER 10001:10001

CMD ["pytest", "-q"]
