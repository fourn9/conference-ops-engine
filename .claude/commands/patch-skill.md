---
description: 使用中に発見したスキルの古さ・誤り・抜けをその場で修正
argument-hint: <skill-path>
---

# /patch-skill <skill-path>

スキルを使っている最中に気づいた不備を、**待たずに**直す。

## いつ呼ぶか

- スキルの手順を実行していて、ステップが古い・足りない・誤っていることに気づいた
- 既知の落とし穴に新しく追加すべきものがある
- 関連リンクが切れている

## いつ呼ばないか

- 不備の確証がない（→ `/record-learning` に「このスキルは古い可能性がある」と書く）
- 大幅な改修（→ `/draft-skill` で代替スキルを起草し、元を `status: deprecated` にする）

## 引数

- `<skill-path>` — 例:
  - `skills/stable/<name>/skill.md`（自律学習レイヤーのスキル）
  - `.claude/skills/<name>/SKILL.md`（ネイティブ・ドメインスキル）

## 実行手順

1. 対象スキルの frontmatter を確認
2. **`created_by: human` かつ `pinned: true` の場合は中止**し、代わりに `decisions-log.md` に
   「`<skill-path>` に以下の不備が見つかった: ...」と `/record-learning` で記録
   （`.claude/skills/` のネイティブスキルは原則 human/pinned 扱い。修正提案は出すが直接編集は確認後）
3. それ以外なら、修正内容の差分を Edit で適用
4. frontmatter があれば更新：`last_used: YYYY-MM-DD`、`patches_needed: +1`
5. スキル末尾の `## 変更履歴`（無ければ作る）に `- YYYY-MM-DD (agent): <修正サマリ>` を追記
6. ユーザーに差分を提示し、**承認後**に確定

## 関連

- `CLAUDE.md` §自律的学習プロトコル（patch on discovery）
- `/curate` — `patches_needed` の多いスキルは見直し候補として提示
