FROM node:22 AS react

WORKDIR /app
COPY js/package*.json .
RUN npm install --production

COPY js/. .
RUN ls && npm run build

FROM python:3.12-slim AS builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache
RUN pip install poetry==1.4.2

WORKDIR /app
# Setup the virtualenv
COPY pyproject.toml poetry.lock ./
RUN  --mount=type=cache,target=$POETRY_CACHE_DIR \
       touch README.md \
    && poetry install --only=main --no-interaction --no-ansi --without dev --no-root

FROM python:3.12-slim AS rahsia

WORKDIR /app
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Copy the virtualenv over from the builder
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
# Copy the static assets over from the react build image
COPY --from=react /app/build/static static
COPY --from=react /app/build/index.html static/index.html

COPY rahsia rahsia
CMD ["uvicorn", "rahsia:app"]
