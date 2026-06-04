#!/bin/bash
ENV_FILE="migratis/.env"

# ── Guard: the env file must exist ──────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: $ENV_FILE not found."
  echo "Create it first:  cp migratis/.env.example migratis/.env"
  exit 1
fi

# ── Guard: USE_SQLITE must be defined ───────────────────────────────────────
if ! grep -qiE '^[[:space:]]*USE_SQLITE[[:space:]]*=' "$ENV_FILE"; then
  echo "ERROR: USE_SQLITE is not set in $ENV_FILE."
  echo "Add one of:"
  echo "    USE_SQLITE=True    # SQLite (default, no database container)"
  echo "    USE_SQLITE=False   # PostgreSQL (starts the base-db container)"
  exit 1
fi

# ── Enable the "postgres" Compose profile when USE_SQLITE is disabled, so the
#    base-db container starts. In SQLite mode the profile stays off and no
#    database container is run. ───────────────────────────────────────────────
USE_SQLITE_VALUE=$(grep -iE '^[[:space:]]*USE_SQLITE[[:space:]]*=' "$ENV_FILE" \
  | tail -n1 | cut -d= -f2 | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')

case "$USE_SQLITE_VALUE" in
  false|0|no|off|n)
    PROFILE="--profile postgres"
    echo "USE_SQLITE is disabled — starting with PostgreSQL (base-db container)."
    ;;
  *)
    PROFILE=""
    echo "USE_SQLITE enabled — starting with SQLite, no database container."
    ;;
esac

cp docker_local/* ./

docker compose $PROFILE up --build

rm docker-compose.yml
rm Dockerfile
rm docker-entrypoint.sh
rm requirements.txt
