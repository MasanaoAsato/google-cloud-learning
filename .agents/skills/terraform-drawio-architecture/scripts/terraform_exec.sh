#!/usr/bin/env bash

set -euo pipefail

working_dir="$PWD"
resolve_only=0

usage() {
  cat >&2 <<'EOF'
usage: bash terraform_exec.sh [--cwd <directory>] [--resolve-only] [--] [terraform-args...]

Resolution order:
  1. TERRAFORM_BIN
  2. Terraform selected by mise for --cwd
  3. terraform on PATH
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cwd)
      if [[ $# -lt 2 ]]; then
        usage
        exit 2
      fi
      working_dir="$2"
      shift 2
      ;;
    --resolve-only)
      resolve_only=1
      shift
      ;;
    --)
      shift
      break
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [[ ! -d "$working_dir" ]]; then
  echo "ERROR: working directory does not exist: $working_dir" >&2
  exit 2
fi
working_dir="$(cd "$working_dir" && pwd -P)"

resolve_binary() {
  local requested="$1"
  if [[ -x "$requested" ]]; then
    printf '%s\n' "$requested"
    return 0
  fi
  command -v "$requested" 2>/dev/null
}

if [[ -n "${TERRAFORM_BIN:-}" ]]; then
  if ! terraform_binary="$(resolve_binary "$TERRAFORM_BIN")"; then
    echo "ERROR: TERRAFORM_BIN is not executable or on PATH: $TERRAFORM_BIN" >&2
    exit 1
  fi
  if (( resolve_only )); then
    printf 'TERRAFORM_BIN: %s\n' "$terraform_binary"
    exit 0
  fi
  cd "$working_dir"
  exec "$terraform_binary" "$@"
fi

if command -v mise >/dev/null 2>&1 && mise -C "$working_dir" which terraform >/dev/null 2>&1; then
  if (( resolve_only )); then
    terraform_binary="$(mise -C "$working_dir" which terraform)"
    printf 'mise: %s\n' "$terraform_binary"
    exit 0
  fi
  exec mise exec -C "$working_dir" -- terraform "$@"
fi

if command -v terraform >/dev/null 2>&1; then
  terraform_binary="$(command -v terraform)"
  if (( resolve_only )); then
    printf 'PATH: %s\n' "$terraform_binary"
    exit 0
  fi
  cd "$working_dir"
  exec "$terraform_binary" "$@"
fi

echo "ERROR: Terraform was not found through TERRAFORM_BIN, mise, or PATH." >&2
exit 127
