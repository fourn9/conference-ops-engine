#!/usr/bin/env bash
# /recall 用。journal/ をキーワード検索する（INDEX → エントリ本文 → 生 transcript 案内）。
set -u

KW="${1:-}"
ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
JOURNAL="$ROOT/journal"

if [ -z "$KW" ]; then
  echo "usage: journal-search.sh <keyword>"
  exit 1
fi
if [ ! -f "$JOURNAL/INDEX.md" ]; then
  echo "journal/INDEX.md がありません（journal 未整備）"
  exit 1
fi

echo "=== INDEX ヒット（セッション一覧） ==="
grep -Fi -- "$KW" "$JOURNAL/INDEX.md" || echo "(なし)"

echo ""
echo "=== エントリ本文ヒット（前後2行付き・最大80行） ==="
grep -rFin -C2 --include='*.md' --exclude='INDEX.md' --exclude='README.md' -- "$KW" "$JOURNAL" 2>/dev/null | head -80 || echo "(なし)"

echo ""
echo "=== それでも足りない場合（生 transcript 検索・重い。ユーザー確認後に実行） ==="
printf '検索対象は CLAUDE_TRANSCRIPT_DIR で指定した、このプロジェクトの transcript のみです。\n'
exit 0
