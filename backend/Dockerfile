# syntax=docker/dockerfile:1.7
# Static build using musl for FROM scratch runtime

# Stage 1: Build
FROM rust:1.82-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    musl-tools \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Add musl target for static linking
RUN rustup target add x86_64-unknown-linux-musl

WORKDIR /app

# Copy manifests
COPY Cargo.toml Cargo.lock ./

# Build dependencies (cache layer)
RUN --mount=type=cache,target=/usr/local/cargo/registry,sharing=locked \
    --mount=type=cache,target=/usr/local/cargo/git,sharing=locked \
    mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    RUSTFLAGS='-C target-feature=+crt-static' cargo build --release --target x86_64-unknown-linux-musl && \
    rm -rf src

# Copy source code
COPY src ./src

# Build application
RUN --mount=type=cache,target=/usr/local/cargo/registry,sharing=locked \
    --mount=type=cache,target=/usr/local/cargo/git,sharing=locked \
    touch src/main.rs && \
    RUSTFLAGS='-C target-feature=+crt-static' cargo build --release --locked --target x86_64-unknown-linux-musl && \
    strip --strip-all target/x86_64-unknown-linux-musl/release/backend

# Stage 2: Runtime
FROM scratch

WORKDIR /app

# Copy CA certificates for HTTPS
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy binary
COPY --from=builder /app/target/x86_64-unknown-linux-musl/release/backend /app/backend

# Copy migrations
COPY migrations /app/migrations

# Copy models (optional - if AI engine is configured)
# COPY models /app/models

# Expose port
EXPOSE 8000

# Run
CMD ["/app/backend"]