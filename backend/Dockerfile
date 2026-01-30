# syntax=docker/dockerfile:1.7
# Static build - fully self-contained, no external dependencies

FROM rust:1.93.0-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    musl-tools \
    ca-certificates \
    postgresql-15 \
    postgresql-contrib-15 \
    postgresql-15-postgis-3 \
    && rm -rf /var/lib/apt/lists/*

RUN rustup target add x86_64-unknown-linux-musl

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY migrations ./migrations

# Build dependencies
RUN --mount=type=cache,target=/usr/local/cargo/registry,sharing=locked \
    --mount=type=cache,target=/usr/local/cargo/git,sharing=locked \
    mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    RUSTFLAGS='-C target-feature=+crt-static' cargo build --release --target x86_64-unknown-linux-musl && \
    rm -rf src

COPY src ./src

# Start postgres, run migrations, build app
RUN --mount=type=cache,target=/usr/local/cargo/registry,sharing=locked \
    --mount=type=cache,target=/usr/local/cargo/git,sharing=locked \
    mkdir -p /var/run/postgresql && \
    chown postgres:postgres /var/run/postgresql && \
    su - postgres -c "/usr/lib/postgresql/15/bin/initdb -D /tmp/pgdata" && \
    su - postgres -c "/usr/lib/postgresql/15/bin/pg_ctl -D /tmp/pgdata -l /tmp/logfile start" && \
    sleep 2 && \
    su - postgres -c "createdb bioradar_build" && \
    su - postgres -c "psql -d bioradar_build -c 'CREATE EXTENSION IF NOT EXISTS postgis;'" && \
    export DATABASE_URL=postgresql://postgres@localhost:5432/bioradar_build && \
    cd /app && \
    cargo install sqlx-cli --no-default-features --features postgres && \
    sqlx migrate run && \
    touch src/main.rs && \
    RUSTFLAGS='-C target-feature=+crt-static' cargo build --release --locked --target x86_64-unknown-linux-musl && \
    strip --strip-all target/x86_64-unknown-linux-musl/release/backend && \
    su - postgres -c "/usr/lib/postgresql/15/bin/pg_ctl -D /tmp/pgdata stop"

FROM scratch

WORKDIR /app

COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /app/target/x86_64-unknown-linux-musl/release/backend /app/backend
COPY --from=builder /app/migrations /app/migrations

EXPOSE 8000

CMD ["/app/backend"]