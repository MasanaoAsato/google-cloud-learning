#!/usr/bin/env bash
# 学習テーマ 1 つ分の情報源（IaC コード / ドキュメント / git 履歴）を一括で標準出力に吐く。
#
#   bash collect_context.sh <theme-dir>
#   bash collect_context.sh architectures/10
#
# クラウドにもディレクトリ名にも依存しない。IaC が Terraform 以外のリポジトリでは
# IAC_GLOB でコードの拡張子を指定する:
#
#   IAC_GLOB='*.bicep' bash collect_context.sh architectures/01
#
# 生成物・状態ファイル（.terraform/ 配下・tfstate・ロックファイル等）は
# 学習の役に立たないので除外する。
# 1 ファイルあたり MAX_LINES 行で打ち切り、打ち切った旨を明示する
# （切り詰められたファイルだけ、呼び出し側が個別に Read すればよい）。

set -uo pipefail

THEME_DIR="${1:-}"
MAX_LINES="${MAX_LINES:-400}"
IAC_GLOB="${IAC_GLOB:-*.tf}"

if [ -z "$THEME_DIR" ] || [ ! -d "$THEME_DIR" ]; then
  echo "usage: bash collect_context.sh <theme-dir>   例: bash collect_context.sh architectures/10" >&2
  exit 1
fi

THEME_DIR="${THEME_DIR%/}"

hr() { printf '\n========== %s ==========\n' "$1"; }

dump_file() {
  local f="$1"
  local total
  total=$(wc -l < "$f" | tr -d ' ')
  printf '\n----- %s (%s lines) -----\n' "$f" "$total"
  head -n "$MAX_LINES" "$f"
  if [ "$total" -gt "$MAX_LINES" ]; then
    printf '\n[... %s 行を切り詰めました。全文が必要なら %s を直接 Read してください ...]\n' \
      "$((total - MAX_LINES))" "$f"
  fi
}

# 除外パターン: 生成物・状態ファイル
is_noise() {
  case "$1" in
    */.terraform/*|*.tfstate|*.tfstate.backup|*.terraform.lock.hcl) return 0 ;;
    */node_modules/*|*/.venv/*|*/__pycache__/*) return 0 ;;
    */.DS_Store|*skills-lock.json) return 0 ;;
    *) return 1 ;;
  esac
}

hr "THEME: $THEME_DIR"

hr "FILE TREE"
find "$THEME_DIR" -type f | while read -r f; do
  is_noise "$f" && continue
  printf '%s\n' "$f"
done | sort

hr "IaC ($IAC_GLOB / main)"
find "$THEME_DIR" -maxdepth 2 -name "$IAC_GLOB" | sort | while read -r f; do
  is_noise "$f" && continue
  case "$f" in */modules/*) continue ;; esac
  dump_file "$f"
done

hr "IaC ($IAC_GLOB / modules)"
find "$THEME_DIR" -path '*/modules/*' -name "$IAC_GLOB" | sort | while read -r f; do
  is_noise "$f" && continue
  dump_file "$f"
done

hr "DOCS (README / ROADMAP など)"
docs=$(find "$THEME_DIR" -name '*.md' | sort)
handwritten=0
for f in $docs; do
  is_noise "$f" && continue
  # terraform-docs の自動生成物は学習の軸を含まないので存在だけ知らせる
  case "$f" in
    *README_TERRAFORM_DOCS.md) printf '\n----- %s (自動生成: 中身は省略) -----\n' "$f"; continue ;;
  esac
  dump_file "$f"
  handwritten=$((handwritten + 1))
done
if [ "$handwritten" -eq 0 ]; then
  echo ""
  echo "(このテーマには手書きの Markdown ドキュメントがありません。"
  echo " 学習の軸はコードと git 履歴から読み取り、必要ならユーザーに意図を確認すること)"
fi

hr "その他の素材 (html / sql / py / sh / json など)"
find "$THEME_DIR" -type f \
  \( -name '*.html' -o -name '*.sql' -o -name '*.py' -o -name '*.sh' -o -name '*.js' -o -name '*.yaml' -o -name '*.yml' \) \
  | sort | while read -r f; do
  is_noise "$f" && continue
  dump_file "$f"
done

hr "GIT LOG (このテーマに触れたコミット)"
git log --oneline --no-merges -- "$THEME_DIR" 2>/dev/null | head -n 40 \
  || echo "(git 履歴を取得できませんでした)"

hr "GIT STATUS (未コミットの変更 = 進行中の作業)"
git status --porcelain -- "$THEME_DIR" 2>/dev/null | head -n 40

hr "SIBLING THEMES (前後のテーマ: 関連リンクの候補)"
ls -1 "$(dirname "$THEME_DIR")" 2>/dev/null

hr "END"
