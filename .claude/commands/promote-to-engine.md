---
name: promote-to-engine
description: インスタンス（カンファリポ）で実証した汎用資産を conference-ops-engine へ昇華する。基準6項目を検証 → 固有名詞を抜く → engine に PR を作成。判断は engine の PR レビュー（G2）に集約。
disable-model-invocation: true
---

# /promote-to-engine — インスタンス資産を engine へ昇華（半自動）

カンファリポ（インスタンス）で「良い」と分かったスキル・失敗パターン・方法論・テンプレを、
中央 `conference-ops-engine` に PR で上げるコマンド。**配管は自動、採否判断は人間が engine の PR で**。

引数: 昇華したい候補ファイル/ディレクトリのパス（インスタンス相対）。例:
```
/promote-to-engine skills/experimental/foo
/promote-to-engine .failure-inbox/2026-xx-yy-some-pattern.md
```

## 二段ゲート

- **G1 候補化**: 各 PO がインスタンス内で frontmatter `promote_candidate: true` を付けるだけ（軽い）。
- **G2 採用（このコマンド〜PR）**: 基準を検証し、通れば engine へ PR。merge 判断は メンテナによるレビュー。

## 採用基準（全項目を満たさなければ PR を作らない）

候補を読み、次の6項目を**1つずつ判定**して結果を表示する。1つでも NG なら**中止し、不足理由を提示**する。

1. **再現性**: 2回以上実使用 ／ または 2カンファ・2 PO で有効だった（一発ネタは却下）
2. **汎用性**: カンファ固有名詞（登壇者・スポンサー・企業・日付・イベント名）を抜いても成立する
3. **非重複**: engine に同等物がない（あれば新規ではなく `/patch-skill` で改修を促し中止）
4. **安定性**: frontmatter が `stable`、直近で改稿が止まっている（流動中は上げない）
5. **安全性**: 外部送信・金銭・通知を含むなら安全レビュー済み
6. **理由が1行で書ける**: 「なぜ engine 行きか」を言語化できる

## 手順

1. **基準検証**: 上記6項目を判定 → NG なら中止＋理由。
2. **engine を用意**: `ENGINE_REPO`（env）か既定パスの engine チェックアウトを使う。無ければ
   `git clone <engine-url>` を一時ディレクトリに行い、`git checkout -b promote/<slug>` する。
3. **固有名詞を抜く**: 登壇者・スポンサー・企業名・日付・イベント固有表現を一般化する
   （例「対象イベントの候補者」→「データ基盤テーマの当事者登壇者」）。抜いて成立しなければ G2 で却下。
4. **frontmatter を engine 用に整形**: `created_by`, `status: stable`, `pinned: false`,
   `promoted_from: <instance>/<path>`, `promoted_at: <date>` を付与（`promote_candidate` は除去）。
5. **配置**: 種類別に置く。
   - スキル → `engine/.claude/skills/<name>/`
   - 失敗パターン → `engine/failure-patterns.md` に追記（無ければ新規）
   - 方法論・判断 → `engine/decisions/NNNN-<slug>.md`（ADR）
   - テンプレ → `engine/templates/`
6. **PR 作成**: `gh pr create` で engine へ。タイトル `promote: <slug>`、本文に基準6項目の判定結果と
   「なぜ engine 行きか」を載せる。
7. **報告**: 作成した PR URL を表示。**merge はしない**（メンテナによるレビュー待ち）。
8. merge 後、各インスタンスは `scripts/sync-engine.sh <new-tag>` で取り込む。重複した instance 側
   `skills/experimental/<name>` は削除しドリフトを防ぐ。

## 安全装置

- 基準6項目のいずれかが NG なら**PRを作らない**（採否は G2 に集約）。
- engine の保護対象（`.claude/skills` 等）は メンテナによるレビュー必須。
- 固有名詞・PII を engine に持ち込まない（汎用化が前提）。
