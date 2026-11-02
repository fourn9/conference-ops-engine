---
description: .failure-inbox/ で 3 回以上観測した失敗パターンを failure-patterns.md に昇格
argument-hint: <pattern-id>
---

# /promote-pattern <pattern-id>

`.failure-inbox/` 内の観測ログを `failure-patterns.md` に昇格する。

## いつ呼ぶか

- `.failure-inbox/` 内に同じ `pattern_id` が 3 件以上溜まっている
- そのパターンに具体的な対処法が見えてきた

## いつ呼ばないか

- 観測 1〜2 回（まだ偶発の可能性）
- 対処が「気をつける」しか書けない（具体化されていない）

## 引数

- `<pattern-id>` — `.failure-inbox/` エントリの frontmatter `pattern_id`、または自然言語指定

## 実行手順

1. `.failure-inbox/*.md` を Read で全件読む
2. 指定 `pattern_id` に該当するエントリを集め observed_count を数える
3. **3 件未満なら中止**し「まだ N 件です。閾値は 3 件」と伝える
4. 3 件以上なら `failure-patterns.md` 末尾を読み、次番号 #N+1 を決定
5. `failure-patterns.md` 末尾に追記：

```markdown
## #N+1: <パターン名>

**症状**: どう現れるか

**原因仮説**: なぜ起きるか

**対処**: 検出時に何をするか

**関連**: skills/・decisions/ 等へのリンク

**First observed**: YYYY-MM-DD
**Last observed**: YYYY-MM-DD
**Observed count**: N
```

6. 昇格元の `.failure-inbox/` ファイルに frontmatter `promoted_to: "failure-patterns.md#N+1"` と `status: promoted` を設定（**削除しない**）
7. ユーザーに差分を提示し、承認後に確定
8. 関連スキルに「`failure-patterns.md #N+1` を参照」と追記する提案を行う

## 関連

- `.failure-inbox/README.md` — inbox の運用ルール
- `CLAUDE.md` §自律的学習プロトコル
