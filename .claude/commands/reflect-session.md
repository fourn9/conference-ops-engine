---
description: セッション終了時の自己振り返り。保存すべき学びを発掘して各コマンドを連鎖呼出する
---

# /reflect-session

セッションを閉じる前に、保存すべきことが残っていないかを自問する。

## いつ呼ばれるか

- `Stop` フックから実行を提案（フック自体はリマインダーのみ）（`.claude/settings.json` 参照）
- ユーザーから明示的に呼ばれた

## 実行手順

このセッションの会話履歴を振り返り、順に自問する：

1. **非自明な発見はあったか？** → `/record-learning`（decisions-log.md）を提案
2. **反復可能な手順を完遂したか？**（5+ ツール呼び出し＋再発しそう）→ `/draft-skill <name>` を提案
3. **重い判断を行ったか？**（同じ判断 2 回目／不可逆）→ `/draft-adr <topic>` を提案
4. **失敗・ハマりパターンを観測したか？** → `.failure-inbox/YYYY-MM-DD-<slug>.md` に追記。同 pattern_id が 3 件溜まっていれば `/promote-pattern` を提案
5. **既存スキルの不備に気づいたか？** → `/patch-skill`（pinned なら `/record-learning` に記録）
6. **ユーザーの好み・規約・環境を学んだか？** → `USER.md` または `local/vault/Memory.md` への追記を提案（declarative で）
7. **curator 周期チェック** → `.claude/curator-state.json > last_run` が 14 日以上前なら「次回起動時に `/curate` を提案します」と報告
8. **Memory.md 書き戻し** → 確定事項・次にやることがあれば `local/vault/Memory.md` と `conference/Memory.md` の更新を提案（CLAUDE.md「セッション終了時」ルール）

## 出力フォーマット

```markdown
## /reflect-session — YYYY-MM-DD

### 保存すべきもの
- [ ] 学び: 「X について Y を発見」→ `/record-learning` を実行しますか？
- [ ] スキル化: 「Z の手順」→ `/draft-skill z-procedure` を実行しますか？
- [ ] ADR 候補: 「W の選択」→ `/draft-adr w-decision` を実行しますか？
- [ ] Memory 更新: 確定事項 N 件 → Memory.md に書き戻しますか？

### 保存しなくて良いもの
- 単なる作業ログ／まだ確証のない仮説
```

各項目はユーザーの承認を得てから実行する。**自動保存はしない。常に提案 → 確認。**

## anti-noise の自己チェック

提案前に確認：PR#/Issue#/SHA を含めていないか／取引的記録になっていないか／推測を事実化していないか／ネガティブ評価になっていないか。該当すれば提案しない。

## 関連

- `CLAUDE.md` §自律的学習プロトコル（セッション終了時の自問）
- `/record-learning`, `/draft-skill`, `/draft-adr`, `/promote-pattern`, `/patch-skill`, `/curate`
