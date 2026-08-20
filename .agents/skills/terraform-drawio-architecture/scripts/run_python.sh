#!/usr/bin/env sh

# Run a skill script with whichever standard Python command is available.
# The scripts use PEP 604 union syntax, so Python 3.10 or later is required.
set -eu

if [ "$#" -eq 0 ]; then
  echo "usage: sh scripts/run_python.sh <script.py> [args ...]" >&2
  exit 2
fi

for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 \
    && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
      >/dev/null 2>&1; then
    exec "$candidate" "$@"
  fi
done

echo "ERROR: Python 3.10 or later is required. Make either 'python3' or 'python' available." >&2
exit 127
