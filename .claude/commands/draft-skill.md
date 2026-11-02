---
description: 反復可能な手順をスキルとして skills/experimental/ に骨格生成
argument-hint: <skill-name>
---

# /draft-skill <skill-name>

`skills/experimental/<skill-name>/skill.md` に新規スキルの骨格を作る。

> 注：本リポには 2 系統のスキルがある。
> - `.claude/skills/` … Claude Code ネイティブの呼び出し可能スキル（sponsor-ops 等、人間作成・de facto stable）。**ここには起草しない。**
> - `skills/{experimental,stable,archived}/` … 本自律学習レイヤーが管理するライフサイクル付きスキル。**起草先はここ。**

## いつ呼ぶか

- 5+ ツール呼び出しを伴う複雑なタスクを完遂した
- そのタスクが**今後も繰り返し発生しそう**と判断した
- 既存スキル・methodology では捕捉できていない

## いつ呼ばないか

- 一回限りの作業
- 既存スキルの軽微な変種（→ `/patch-skill` で元スキルを拡張）
- まだ手順が固まっていない（→ `/record-learning` で観察を残す）

## 引数

- `<skill-name>` — kebab-case-slug。例: `speaker-shortlist-dedup`

## 実行手順

1. `skills/experimental/<skill-name>/` を作成
2. `skills/experimental/<skill-name>/skill.md` を以下で作成：

```markdown
---
name: <skill-name>
description: <一行、100 字以内>
phase: <該当フェーズ または cross-phase>
prerequisites: []
estimated_time: <例: 30min>
created_by: agent
created_at: YYYY-MM-DD
last_used: YYYY-MM-DD
usage_count: 0
status: experimental
pinned: false
patches_needed: 0
---

# <スキル名>

## 目的
<1-2 文>

## いつ使うか
<どんな状況で呼ばれるべきか>

## 前提
<入力として必要なもの・Memory.md の状態など>

## 手順
1. <ステップ 1>
2. <ステップ 2>

## 出力
<成果物の形式・保存先>

## Exit Criteria（終了条件）
- [ ] <検証 1>
- [ ] <検証 2>

## 既知の落とし穴
- <あれば>

## 関連
- `failure-patterns.md` #N
- `decisions/NNNN-*.md`
```

3. ユーザーに「`skills/experimental/<skill-name>/skill.md` を起草しました。`/curate` で usage_count>=3 かつ patches_needed==0 が確認されたら `skills/stable/` への昇格を提案します」と伝える

## 関連

- `skills/README.md` — ライフサイクル（experimental → stable → archived）
- `CLAUDE.md` §自律的学習プロトコル（プロベナンス frontmatter）
- `/curate` — 昇格判定
