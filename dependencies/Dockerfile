FROM python:3.12-slim-bookworm

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  ca-certificates \
  ssh-client && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Download the latest installer (pinned)
ADD https://astral.sh/uv/0.6.9/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed Python modules are on the `PATH`
ENV PATH="/.venv/bin:/root/.local/bin/:$PATH"

WORKDIR /
COPY pyproject.toml  .
COPY uv.lock .
RUN uv sync --frozen
