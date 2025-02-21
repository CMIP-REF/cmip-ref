# Build the container for the the REF compute engine
# This docker container packages up the REF cli tool with the default set of metric providers
# used as part of the CMIP7 FastTrack process.

FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

WORKDIR /app

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-workspace --no-editable --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app

# Sync the project as non-editable installs
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable --no-dev

# Runtime container
# Copy the installed packages from the build stage to decrease the size of the final image
FROM python:3.10-slim AS runtime

LABEL maintainer="Jared Lewis <jared.lewis@climate-resource.com>"
LABEL description="Docker image for the CMIP REF compute engine"

# Allow celery to run as root
ENV C_FORCE_ROOT=false
ENV PATH="/app/.venv/bin:${PATH}"

# Copy the installed packages from the build stage
COPY --from=build --chown=app:app /app/.venv /app/.venv
COPY --from=build --chown=app:app /app/scripts /app/scripts

# Location of the REF configuration files
ENV REF_CONFIGURATION=/ref
ENV REF_METRICS_ILAMB_DATA_DIR=/app/cache/ilamb
ENV REF_METRICS_ESMVALTOOL_DATA_DIR=/app/cache/esmvaltool

#RUN python /app/scripts/fetch-ilamb-data.py ilamb.txt
#RUN python /app/scripts/fetch-ilamb-data.py iomb.txt

# Run the REF CLI tool by default
ENTRYPOINT ["/app/.venv/bin/ref"]
