# docbench verification container.
# Everything except the LLM provider is pinned here: python version, package
# version, cases, rulesets, prompts, scoring code. Two modes:
#   offline: --network none, scores replayed deterministically from var/cache
#   online:  provider egress only; keys come from the environment, never baked in
FROM python:3.10-slim

ENV PYTHONHASHSEED=0 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY docbench ./docbench
RUN pip install --no-cache-dir .

COPY rulesets ./rulesets
COPY cases ./cases

RUN useradd --create-home bench

# The runner writes to /app/var/{cache,runs}; mount host dirs there.
VOLUME ["/app/var/cache", "/app/var/runs"]

ENTRYPOINT ["docbench"]
CMD ["--help"]
