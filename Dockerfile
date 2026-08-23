# docbench verification container.
# The application dependency graph is locked in uv.lock. Two modes:
#   offline: --network none, scores replayed deterministically from var/cache
#   online:  provider egress only; keys come from the environment, never baked in
FROM ghcr.io/astral-sh/uv:0.10.8 AS uv
FROM python:3.10-slim

ENV PYTHONHASHSEED=0 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY docbench ./docbench
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

COPY rulesets ./rulesets
COPY cases ./cases

RUN useradd --create-home bench

# The runner writes to /app/var/{cache,runs}; mount host dirs there.
VOLUME ["/app/var/cache", "/app/var/runs"]

ENTRYPOINT ["docbench"]
CMD ["--help"]
