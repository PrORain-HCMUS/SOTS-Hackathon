# syntax=docker/dockerfile:1.7

############################
# Stage 1: Builder
############################
FROM --platform=$BUILDPLATFORM rust:alpine3.21 AS builder

COPY --from=tonistiigi/xx:1.6.1 / /
ARG TARGETPLATFORM

RUN apk add --no-cache clang lld musl-dev git file

RUN xx-apk add --no-cache musl-dev gcc

WORKDIR /app

ENV RUSTFLAGS="-C target-feature=+crt-static -C link-arg=-static -C target-cpu=generic"

# --- Build Rust App ---
COPY Cargo.toml Cargo.lock ./

RUN --mount=type=cache,target=/usr/local/cargo/registry,sharing=locked \
    --mount=type=cache,target=/usr/local/cargo/git,sharing=locked \
    mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    xx-cargo build --release --locked --bin backend && \
    rm -rf src target/*/release/backend* target/*/release/deps/backend*

COPY src ./src
COPY migrations ./migrations

RUN --mount=type=cache,target=/usr/local/cargo/registry,sharing=locked \
    --mount=type=cache,target=/usr/local/cargo/git,sharing=locked \
    touch src/main.rs && \
    xx-cargo build --release --locked --bin backend && \
    cp target/*/release/backend /tmp/backend && \
    xx-verify /tmp/backend && \
    strip --strip-all /tmp/backend

# Create non-root user for scratch image
RUN echo "appuser:x:10001:10001::/app:/sbin/nologin" >> /etc/passwd && \
    echo "appgroup:x:10001:" >> /etc/group

############################
# Stage 2: Minimal scratch runtime
############################
FROM scratch

COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

WORKDIR /app

COPY --from=builder /tmp/backend /app/backend

USER 10001:10001

ENV RUST_LOG=info

EXPOSE 8000

CMD ["/app/backend"]