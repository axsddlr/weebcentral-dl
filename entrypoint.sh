#!/bin/sh
set -e

# Bootstrap required files that Docker bind-mounts may have created as directories
# or that don't exist on first run.

# --- config.toml ---
if [ -d "/app/config.toml" ]; then
    echo "entrypoint: /app/config.toml is a directory (Docker bind-mount quirk), replacing with file"
    rm -rf "/app/config.toml"
fi
if [ ! -f "/app/config.toml" ]; then
    if [ -f "/app/example.config.toml" ]; then
        echo "entrypoint: creating /app/config.toml from example.config.toml"
        cp "/app/example.config.toml" "/app/config.toml"
    else
        echo "entrypoint: creating minimal /app/config.toml"
        cat > "/app/config.toml" <<'TOML'
[downloader]
output_dir = "./manga_downloads"
library_paths = []
latest = false
sequence = false
zip = false
use_english_title = false
comicinfo = false
rlc = 10
max_sleep = 120
max_retries = 5
parallel_workers = 99

[ntfy]
ntfy_url = ""
TOML
    fi
fi

# --- weebcentral.db ---
if [ -d "/app/weebcentral.db" ]; then
    echo "entrypoint: /app/weebcentral.db is a directory (Docker bind-mount quirk), replacing with empty file"
    rm -rf "/app/weebcentral.db"
fi
if [ ! -f "/app/weebcentral.db" ]; then
    echo "entrypoint: creating empty /app/weebcentral.db"
    touch "/app/weebcentral.db"
fi

# --- manga_downloads ---
mkdir -p "/app/manga_downloads"

exec "$@"
