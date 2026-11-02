---
description: 重い判断を ADR として decisions/ に起草する
argument-hint: <topic-slug>
---

# /draft-adr <topic-slug>

`decisions/NNNN-<topic-slug>.md` に領域ADRの骨格を作る。

## いつ呼ぶか

- 同じ判断を 2 回繰り返した（型の発見）
- 不可逆な選択を行った（後で変更が高コスト）
- 新しい技術選定・運用フロー変更・スポンサープラン設計・登壇者対応の標準フロー
- `decisions-log.md` に同じ気付きが 3 回以上出てきた

## いつ呼ばないか

- 軽い気付き → `/record-learning`（decisions-log.md）で十分
- すでに反復手順として固まっている → `/draft-skill`
- 一時的な判断（次回見直す予定）→ `decisions-log.md`

## 引数

- `<topic-slug>` — kebab-case-slug。例: `sponsor-plan-design`

## 実行手順

1. `ls decisions/*.md` で既存 ADR の最大番号 NNNN を確認（領域内で連番。既存が無ければ 0001）
2. `decisions/NNNN+1-<topic-slug>.md` を以下で作成（既存ADRのヘッダ書式＋プロベナンス frontmatter）：

```markdown
---
name: NNNN-<topic-slug>
description: <一行、100 字以内>
created_by: agent
created_at: YYYY-MM-DD
last_used: YYYY-MM-DD
usage_count: 0
status: experimental
pinned: false
adr_status: Proposed
---

# ADR-NNNN: <タイトル>

- **Status**: Proposed（Proposed | Accepted | Superseded | Deprecated）
- **Date**: YYYY-MM-DD
- **Deciders**: <ユーザー名 / agent / 双方>
- **Tags**: <カンマ区切り>

## Context（背景・問題）

<なぜこの判断が必要になったか。背景・制約・関係者>

## Decision（決定）

<何を決めたか。1-3 文で明確に>

## Alternatives Considered（検討した代替案）

- **A**: ...
- **B**: ...
- **C（採用）**: ...

## Consequences（影響）

<得られるもの／失うもの／今後発生する作業>

## References

- `decisions-log.md` YYYY-MM-DD エントリ
- `failure-patterns.md` #N
- 関連 ADR: NNNN-*
```

3. `decisions/README.md` の「ADR インデックス」に 1 行追加
4. ユーザーに「ADR-NNNN を起草しました（status: Proposed）。レビューをお願いします」と伝える
5. **Accepted への昇格はユーザー判断**。agent は Proposed までしか書かない。承認後に `adr_status: Accepted` へ更新

## 関連

- `decisions/README.md` — 領域ADRインデックス
- 横断ADRは `../decisions/` 側（番号体系は分離）
- `CLAUDE.md` §自律的学習プロトコル
