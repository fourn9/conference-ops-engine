#!/usr/bin/env bash
# journal-capture.sh / journal-backfill.sh から呼ばれるワーカー。
# 抽出（journal-extract.py）→ 要約（claude -p・haiku）→ journal/ 書込＋INDEX 追記。
# 失敗しても常に exit 0（呼び出し元をブロックしない）。ログは呼び出し元が .capture.log に集約。
set -u

SESSION_ID="${1:?session_id}"
TRANSCRIPT="${2:?transcript_path}"
ROOT="${3:?repo_root}"
SCRIPTS="$ROOT/.claude/scripts"
JOURNAL="$ROOT/journal"

# Public distribution: summarization is opt-in; generated journals stay local.
[ -f "$ROOT/local/journal-enabled" ] || [ "${CONFERENCE_JOURNAL_ENABLED:-}" = "1" ] || exit 0
case "$SESSION_ID" in *[!a-zA-Z0-9-]*|"") echo "invalid session id"; exit 1 ;; esac
ID8="${SESSION_ID:0:8}"
mkdir -p "$JOURNAL"
grep -Fqs -- "$SESSION_ID" "$JOURNAL/INDEX.md" 2>/dev/null && exit 0
STAMP="$(date '+%Y-%m-%d %H:%M:%S')"
echo "[$STAMP] start session=$ID8 transcript=$TRANSCRIPT generator=${JOURNAL_GENERATOR:-auto}"

# エントリ時刻は transcript の mtime から決定的に取る（macOS: date -r <file>）
MTIME_DATE="$(python3 -c 'import datetime,os,sys; print(datetime.datetime.fromtimestamp(os.path.getmtime(sys.argv[1])).strftime("%Y-%m-%d"))' "$TRANSCRIPT")"
MTIME_HHMM="$(python3 -c 'import datetime,os,sys; print(datetime.datetime.fromtimestamp(os.path.getmtime(sys.argv[1])).strftime("%H%M"))' "$TRANSCRIPT")"
YEAR="${MTIME_DATE%%-*}"

TMPD="$(mktemp -d)" || exit 0
LOCKED=0
cleanup() {
  rm -rf "$TMPD"
  [ "$LOCKED" = "1" ] && rmdir "$JOURNAL/.lock" 2>/dev/null
  return 0
}
trap cleanup EXIT

lock() {
  local n=0
  while ! mkdir "$JOURNAL/.lock" 2>/dev/null; do
    n=$((n + 1))
    if [ "$n" -gt 50 ]; then
      echo "[warn] journal index lock busy; retry later"
      return 1
    fi
    sleep 0.2
  done
  LOCKED=1
}
unlock() {
  rmdir "$JOURNAL/.lock" 2>/dev/null || true
  LOCKED=0
}

append_index() {
  # $1 = INDEX 行。ロック下で冪等追記
  if lock; then
    grep -Fqs -- "$SESSION_ID" "$JOURNAL/INDEX.md" || printf '%s\n' "$1" >> "$JOURNAL/INDEX.md"
    unlock
  fi
}

# --- 抽出 ---
EXTRACT="$TMPD/dialogue.txt"
python3 "$SCRIPTS/journal-extract.py" "$TRANSCRIPT" > "$EXTRACT"
RC=$?
CWD_META="$(sed -n '1s/.* cwd=\(.*\) branch=.*/\1/p' "$EXTRACT")"
BRANCH="$(sed -n '1s/.* branch=\(.*\) user_turns=.*/\1/p' "$EXTRACT")"

if [ "$RC" = "3" ]; then
  append_index "$MTIME_DATE | $SESSION_ID | (trivial, skipped) | - | -"
  echo "[$STAMP] trivial skip $ID8"
  exit 0
fi
if [ "$RC" != "0" ]; then
  echo "[$STAMP] extract failed rc=$RC session=$ID8"
  exit 0
fi

# --- 要約（headless claude・ツールなし・stdin→stdout のみ） ---
MODEL="${CLAUDE_JOURNAL_MODEL:-haiku}"
SUMMARY="$TMPD/summary.md"
(
  cd "$TMPD" && \
  CLAUDE_JOURNAL_SUMMARIZER=1 claude -p "$(cat "$SCRIPTS/journal-prompt.md")" \
    --model "$MODEL" --tools "" --strict-mcp-config --mcp-config '{"mcpServers":{}}' --settings '{"disableAllHooks":true}' --setting-sources "" --disable-slash-commands --no-session-persistence < "$EXTRACT" > "$SUMMARY" 2> "$TMPD/claude.err"
)
SUMMARY_RC=$?
if [ "$SUMMARY_RC" != "0" ] || [ ! -s "$SUMMARY" ]; then
  echo "[$STAMP] summarizer empty session=$ID8: $(tail -3 "$TMPD/claude.err" 2>/dev/null | tr '\n' ' ')"
  exit 0
fi

# --- パース（フォーマット崩れは全文を本文にフォールバック） ---
SLUG="$(sed -n 's/^SLUG:[[:space:]]*//p' "$SUMMARY" | head -1 | tr -cd 'a-z0-9-' | cut -c1-40)"
[ -z "$SLUG" ] && SLUG="session"
TITLE="$(sed -n 's/^TITLE:[[:space:]]*//p' "$SUMMARY" | head -1 | tr -d '|')"
INDEXINFO="$(sed -n 's/^INDEX:[[:space:]]*//p' "$SUMMARY" | head -1)"
BODY="$(sed '1,/^---$/d' "$SUMMARY")"
[ -z "$BODY" ] && BODY="$(cat "$SUMMARY")"

# --- 書込 ---
ENTRY_DIR="$JOURNAL/$YEAR"
mkdir -p "$ENTRY_DIR"
ENTRY="$ENTRY_DIR/${MTIME_DATE}_${MTIME_HHMM}_${SESSION_ID}_${SLUG}.md"
{
  echo "---"
  echo "session_id: $SESSION_ID"
  echo "date: $MTIME_DATE"
  echo "cwd: ${CWD_META:-unknown}"
  echo "branch: ${BRANCH:-unknown}"
  echo "created_by: agent"
  echo "generator: ${JOURNAL_GENERATOR:-auto}"
  echo "status: raw"
  echo "pinned: false"
  echo "---"
  echo
  echo "# ${TITLE:-セッション記録 $ID8}"
  echo
  printf '%s\n' "$BODY"
} > "$ENTRY"

REL="journal/$YEAR/$(basename "$ENTRY")"
append_index "$MTIME_DATE | $SESSION_ID | ${TITLE:-(要約形式エラー・本文フォールバック)} | ${INDEXINFO:--} | $REL"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] done $REL"
exit 0
