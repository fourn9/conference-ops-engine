---
description: agent 作成物の昇格・統合・アーカイブを dry-run で提案
argument-hint: [--apply]
---

# /curate [--apply]

`created_by: agent` のファイルを横断的に整理する。
**デフォルトは dry-run**。実際の変更には `--apply` が必要。

## いつ呼ぶか

- `.claude/curator-state.json > last_run` が 14 日以上前
- `skills/experimental/` が肥大化してきた
- `decisions-log.md` が長くなって重複が増えてきた
- ユーザーから明示的に呼ばれた

## いつ呼ばないか

- セッション開始直後（先にユーザーの作業を進める）
- ユーザーが進行中タスクを抱えている最中

## 引数

- なし（デフォルト dry-run）
- `--apply` — 提案を確定し、ファイルを移動・統合する

## 実行手順

### Step 1: 列挙

frontmatter を読んで全列挙：

- `skills/experimental/**/skill.md`
- `skills/stable/**/skill.md`
- `skills/archived/**/skill.md`
- `decisions/*.md`（`created_by: agent` のもの）
- `.failure-inbox/*.md`
- `decisions-log.md`（直近エントリのトピックを解析）

> `.claude/skills/` のネイティブ・ドメインスキルは human/pinned 扱い。curate の対象外。

### Step 2: 4 種の判定

#### a) 昇格候補（experimental → stable）
- `created_by: agent` / `pinned: false` / `usage_count >= 3` / `patches_needed == 0` / `status: experimental`

#### b) アーカイブ候補（stable → archived）
- `created_by: agent` / `pinned: false` / `last_used` が 90 日以上前 / `usage_count <= 1`

#### c) 重複統合候補（decisions-log.md 内）
- 同じトピックを扱う 3 件以上のエントリ（セマンティック判断）→ `/draft-adr` で ADR 化を提案。**自動マージはしない**

#### d) failure-pattern 昇格候補
- `.failure-inbox/` 内で同じ `pattern_id` が 3 件以上かつ未昇格 → `/promote-pattern` 起動を提案

### Step 3: 差分提示（dry-run）

```markdown
## /curate dry-run — YYYY-MM-DD

### 昇格候補（experimental → stable）N 件
- `skills/experimental/X/skill.md` (usage_count: 4, patches_needed: 0)

### アーカイブ候補（stable → archived）M 件
- `skills/stable/Y/skill.md` (last_used: 2026-02-01, usage_count: 0)

### decisions-log.md 重複統合候補 K 件
- 「XXX」が 5 件 → `/draft-adr` 候補

### failure-pattern 昇格候補 L 件
- `pattern_id: same-company-cluster` を 4 回観測 → `/promote-pattern same-company-cluster`

`/curate --apply` で確定します。個別に拒否する場合は項目を指定してください。
```

### Step 4: --apply の場合

1. 昇格：`skills/experimental/X/` → `skills/stable/X/` に `git mv`、frontmatter `status: stable`, `last_used: today`
2. アーカイブ：`skills/stable/Y/` → `skills/archived/Y/` に `git mv`、frontmatter `status: archived`
3. 重複統合：自動マージしない。提案のみ
4. failure-pattern：`/promote-pattern` を別途呼ぶよう促す
5. `.claude/curator-state.json` の `last_run` を today、`last_actions`（5 件まで）にサマリを追記

### Step 5: 不変条件

- `created_by: human` のファイルは絶対に移動・編集しない
- `pinned: true` のファイルは絶対に移動・編集しない
- **削除はしない。常に move のみ**

## 関連

- `CLAUDE.md` §自律的学習プロトコル
- `.claude/curator-state.json` — 最終実行日・直近アクション
