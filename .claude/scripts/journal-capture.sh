#!/usr/bin/env bash
# SessionEnd フック入口。ガード判定だけして即デタッチし、決してセッション終了をブロックしない。
# 実処理は journal-worker.sh（nohup で切り離し）。正典: journal/README.md・公開版の方法論。
set -u

# 再帰ガード：要約用 headless claude の SessionEnd では何もしない
[ -n "${CLAUDE_JOURNAL_SUMMARIZER:-}" ] && exit 0

INPUT="$(cat 2>/dev/null || true)"
ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SCRIPTS="$ROOT/.claude/scripts"
JOURNAL="$ROOT/journal"

# Public distribution: summarization is opt-in; generated journals stay local.
[ -f "$ROOT/local/journal-enabled" ] || [ "${CONFERENCE_JOURNAL_ENABLED:-}" = "1" ] || exit 0

# journal レイヤーが無いリポジトリでは何もしない
[ -d "$JOURNAL" ] || exit 0
[ -f "$SCRIPTS/journal-worker.sh" ] || exit 0

PARSED="$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
sid = (d.get("session_id") or "").replace("\n", "")
tp = (d.get("transcript_path") or "").replace("\n", "")
print(sid)
print(tp)
' 2>/dev/null)" || exit 0

SESSION_ID="$(printf '%s' "$PARSED" | sed -n 1p)"
TRANSCRIPT="$(printf '%s' "$PARSED" | sed -n 2p)"

[ -z "$SESSION_ID" ] && exit 0
[ -f "${TRANSCRIPT:-/nonexistent}" ] || exit 0

# 冪等：SessionEnd は clear / logout / exit で複数回発火しうる
ID8="${SESSION_ID:0:8}"
grep -Fqs -- "$SESSION_ID" "$JOURNAL/INDEX.md" && exit 0

nohup bash "$SCRIPTS/journal-worker.sh" "$SESSION_ID" "$TRANSCRIPT" "$ROOT" \
  >> "$JOURNAL/.capture.log" 2>&1 &
disown
exit 0
