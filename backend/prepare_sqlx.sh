#!/bin/bash
set -e

echo "==> Preparing sqlx offline mode data..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable not set"
    echo "Please set it in your .env file or export it"
    exit 1
fi

# Install sqlx-cli if not already installed
if ! command -v sqlx &> /dev/null; then
    echo "==> Installing sqlx-cli..."
    cargo install sqlx-cli --no-default-features --features postgres
fi

# Run migrations
echo "==> Running database migrations..."
sqlx migrate run

# Prepare sqlx offline data
echo "==> Generating sqlx offline query data..."
cargo sqlx prepare

echo "==> Done! You can now build with SQLX_OFFLINE=true"
echo "==> The .sqlx directory contains the prepared query data"
