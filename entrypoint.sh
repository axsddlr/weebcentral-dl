#!/bin/sh
set -e

# Bootstrap required files that Docker bind-mounts may have created as directories
# or that don't exist on first run.

APPUSER_UID="${APPUSER_UID:-1000}"

# --- config.toml ---
if [ -d "/app/config.toml" ]; then
    echo "entrypoint: /app/config.toml is a directory (host file missing), writing config inside it"
    CONFIG_FILE="/app/config.toml/.container-config.toml"
    if [ -f "/app/example.config.toml" ]; then
        cp "/app/example.config.toml" "$CONFIG_FILE"
    else
        cat > "$CONFIG_FILE" <<'TOML'
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
    chown "$APPUSER_UID" "$CONFIG_FILE"
    export CONFIG_FILE="$CONFIG_FILE"
elif [ ! -f "/app/config.toml" ]; then
    if [ -f "/app/example.config.toml" ]; then
        echo "entrypoint: creating /app/config.toml from example.config.toml"
        cp "/app/example.config.toml" "/app/config.toml"
        chown "$APPUSER_UID" "/app/config.toml"
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
        chown "$APPUSER_UID" "/app/config.toml"
    fi
else
    # Fix ownership of bind-mounted config file (host file may be root-owned)
    chown "$APPUSER_UID" "/app/config.toml" 2>/dev/null || true
fi

# --- weebcentral.db ---
if [ -d "/app/weebcentral.db" ]; then
    echo "entrypoint: /app/weebcentral.db is a directory (host file missing), creating db inside it"
    WEEBCENTRAL_DB_PATH="/app/weebcentral.db/.container-weebcentral.db"
    export WEEBCENTRAL_DB_PATH="$WEEBCENTRAL_DB_PATH"
elif [ ! -f "/app/weebcentral.db" ]; then
    echo "entrypoint: creating empty /app/weebcentral.db"
    touch "/app/weebcentral.db"
    chown "$APPUSER_UID" "/app/weebcentral.db"
else
    # Fix ownership of bind-mounted db file
    chown "$APPUSER_UID" "/app/weebcentral.db" 2>/dev/null || true
fi

# --- manga_downloads ---
mkdir -p "/app/manga_downloads"

# Drop privileges and run the CMD
exec setpriv --reuid="$APPUSER_UID" --regid="$APPUSER_UID" --clear-groups "$@"
