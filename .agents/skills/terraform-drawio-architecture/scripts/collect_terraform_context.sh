#!/usr/bin/env bash

set -euo pipefail

terraform_root=""
full_source=0
max_lines="${MAX_LINES:-500}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
terraform_runner="$script_dir/terraform_exec.sh"

for arg in "$@"; do
  case "$arg" in
    --full) full_source=1 ;;
    *) terraform_root="$arg" ;;
  esac
done

if [[ -z "$terraform_root" || ! -d "$terraform_root" ]]; then
  echo "usage: bash collect_terraform_context.sh [--full] <terraform-root>" >&2
  exit 2
fi

terraform_root="$(cd "${terraform_root%/}" && pwd -P)"

section() {
  printf '\n========== %s ==========\n' "$1"
}

list_tf_files() {
  find "$terraform_root" -type f \
    \( -name '*.tf' -o -name '*.tf.json' \) \
    ! -path '*/.terraform/*' \
    ! -path '*/node_modules/*' \
    ! -path '*/.venv/*' \
    -print | LC_ALL=C sort
}

dump_file() {
  local file="$1"
  local total
  total="$(wc -l < "$file" | tr -d ' ')"
  printf '\n----- %s (%s lines) -----\n' "$file" "$total"
  sed -n "1,${max_lines}p" "$file"
  if (( total > max_lines )); then
    printf '\n[... %s lines omitted; read %s directly ...]\n' \
      "$((total - max_lines))" "$file"
  fi
}

section "ROOT"
printf '%s\n' "$terraform_root"

section "TOOL AVAILABILITY"
if terraform_resolution="$(bash "$terraform_runner" --cwd "$terraform_root" --resolve-only 2>/dev/null)"; then
  printf 'terraform command: %s\n' "$terraform_resolution"
  bash "$terraform_runner" --cwd "$terraform_root" -- version | sed -n '1,3p'
else
  echo "terraform: unavailable through TERRAFORM_BIN, mise, and PATH (static analysis only)"
fi

section "TERRAFORM FILES"
list_tf_files

section "BLOCK HEADERS"
if command -v rg >/dev/null 2>&1; then
  rg -n --glob '*.tf' --glob '*.tf.json' \
    '^\s*(terraform|provider|resource|data|module|variable|output|locals|moved|import|removed|check)\b' \
    "$terraform_root" || true
else
  while IFS= read -r file; do
    grep -nE '^\s*(terraform|provider|resource|data|module|variable|output|locals|moved|import|removed|check)\b' \
      "$file" || true
  done < <(list_tf_files)
fi

section "REFERENCE CANDIDATES"
if command -v rg >/dev/null 2>&1; then
  rg -n --glob '*.tf' \
    '\b(module|data|local|var|aws_[A-Za-z0-9_]+|azurerm_[A-Za-z0-9_]+|azuread_[A-Za-z0-9_]+|google_[A-Za-z0-9_]+|google-beta_[A-Za-z0-9_]+)\.[A-Za-z0-9_-]+' \
    "$terraform_root" || true
else
  echo "rg is unavailable; inspect references in the source dump"
fi

section "GENERATED RUNTIME ARTIFACTS (PATHS ONLY)"
find "$terraform_root" -type f \
  \( -name '*.tfstate' -o -name '*.tfstate.backup' -o -name '*.tfplan' -o -name '.terraform.lock.hcl' \) \
  -print | LC_ALL=C sort

# 既定では全ソースをダンプしない。BLOCK HEADERSとREFERENCE CANDIDATESが行番号付きの
# 索引になっているので、根拠付けに必要なファイルだけを個別に読めばよい。
# 小さなルートを一括で見たい場合だけ --full を使う。
if (( full_source )); then
  section "SOURCE"
  while IFS= read -r file; do
    dump_file "$file"
  done < <(list_tf_files)
else
  section "SOURCE"
  echo "(omitted by default; evidence requires reading the relevant .tf files directly."
  echo " Re-run with --full to inline every file.)"
fi

section "END"
