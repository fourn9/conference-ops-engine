#!/usr/bin/env bash
# 過去 transcript の一括ジャーナル化。既定は dry-run（一覧と件数のみ）。--run で実行。
# 使い方: journal-backfill.sh [--days N | --all] [--run]
set -u

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SCRIPTS="$ROOT/.claude/scripts"
JOURNAL="$ROOT/journal"

DAYS=14
RUN=0
ALL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --days) [ "$#" -ge 2 ] || { echo "--days requires a number"; exit 1; }; DAYS="$2"; shift 2 ;;
    --all) ALL=1; shift ;;
    --run) RUN=1; shift ;;
    *) echo "unknown argument: $1"; exit 1 ;;
  esac
done

case "$DAYS" in *[!0-9]*|"") echo "--days requires a positive integer"; exit 1 ;; esac
[ "$DAYS" -gt 0 ] || exit 1
[ -d "$JOURNAL" ] || { echo "journal/ がありません"; exit 1; }

FOUND=0
TODO=0
: "${CLAUDE_TRANSCRIPT_DIR:?Set CLAUDE_TRANSCRIPT_DIR to the current project transcript directory}"
for dir in "$CLAUDE_TRANSCRIPT_DIR"; do
  [ -d "$dir" ] || continue
  for f in "$dir"/*.jsonl; do
    [ -f "$f" ] || continue
    if [ "$ALL" != "1" ]; then
      [ -n "$(find "$f" -mtime -"$DAYS" 2>/dev/null)" ] || continue
    fi
    SID="$(basename "$f" .jsonl)"
    ID8="${SID:0:8}"
    FOUND=$((FOUND + 1))
    grep -Fqs -- "$SID" "$JOURNAL/INDEX.md" 2>/dev/null && continue
    TODO=$((TODO + 1))
    TURNS="$(python3 "$SCRIPTS/journal-extract.py" "$f" 2>/dev/null | sed -n '1s/.*user_turns=\([0-9]*\).*/\1/p')"
    if [ "$RUN" = "1" ]; then
      echo ">> capture $ID8 (user_turns=${TURNS:-?}) $f"
      JOURNAL_GENERATOR=backfill bash "$SCRIPTS/journal-worker.sh" "$SID" "$f" "$ROOT" >> "$JOURNAL/.capture.log" 2>&1
    else
      echo "would-capture | $ID8 | user_turns=${TURNS:-?} | $(date -r "$f" '+%Y-%m-%d' 2>/dev/null) | $f"
    fi
  done
done

echo "---"
MODE="dry-run"
[ "$RUN" = "1" ] && MODE="run"
echo "transcripts=$FOUND / 未ジャーナル=$TODO / mode=$MODE"
exit 0
