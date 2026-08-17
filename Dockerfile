FROM python:3.12.13-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf AS build

WORKDIR /build
COPY pyproject.toml constraints.lock LICENSE ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/pip \
    PIP_CONSTRAINT=/build/constraints.lock \
    python -m pip wheel --wheel-dir /wheels ".[dev]"

FROM python:3.12.13-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    BENCHMARK_OUTPUT=/app/benchmarks/results/summary.json

WORKDIR /app
COPY constraints.lock LICENSE ./
COPY --from=build /wheels /opt/wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/opt/wheels \
        -c constraints.lock "model-drift-detector[dev]==1.0.0" \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/benchmarks/results /app/benchmarks/publication \
    && chown -R appuser:appuser /app

COPY src ./src
COPY tests ./tests
COPY benchmarks ./benchmarks
COPY contracts ./contracts
COPY .portfolio/contracts ./.portfolio/contracts
COPY tools/aggregate_results.py ./tools/aggregate_results.py
COPY tools/build_v2_evidence.py ./tools/build_v2_evidence.py
COPY project.yaml ./

USER appuser

ENTRYPOINT ["model-drift-detector"]
CMD ["benchmark"]
