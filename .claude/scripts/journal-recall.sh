#!/usr/bin/env bash
# SessionStart フック。stdout がそのままコンテキストに注入される。
# 直近セッションの INDEX＋申し送りを見せ、従来の自律学習リマインダーも維持する。
set -u

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
JOURNAL="$ROOT/journal"

REMINDER="--- [自律学習] セッション開始時にやること: (1) local/vault/Memory.md と conference/Memory.md を読む (2) USER.md を読む (3) decisions-log.md の直近エントリを読む (4) .claude/curator-state.json の last_run が14日以上前なら /curate を一度だけ提案。過去セッションの経緯・棄却理由が必要なときは /recall <keyword> で journal/ を検索する ---"

if [ ! -f "$JOURNAL/INDEX.md" ]; then
  echo "$REMINDER"
  exit 0
fi

echo "--- [session-journal] 直近セッション（journal/INDEX.md より。詳細はパス先を読む） ---"
grep -v "(trivial, skipped)" "$JOURNAL/INDEX.md" 2>/dev/null | grep -v '^#' | grep -v '^[[:space:]]*$' | tail -n 7

echo "--- [session-journal] 直近の申し送り ---"
grep -v "(trivial, skipped)" "$JOURNAL/INDEX.md" 2>/dev/null | grep -v '^#' | grep -v '^[[:space:]]*$' | tail -n 2 | \
  awk -F'|' '{gsub(/^[ \t]+|[ \t\r]+$/, "", $NF); print $NF}' | \
  while IFS= read -r rel; do
    entry="$ROOT/$rel"
    [ -f "$entry" ] || continue
    echo "▼ $rel"
    awk '/^## 申し送り/{f=1; next} /^## /{f=0} f' "$entry" | grep -v '^[[:space:]]*$' | head -10
  done

echo "$REMINDER"
exit 0
