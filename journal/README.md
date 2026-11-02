# Session journal

元実装の抽出→要約→索引→想起の流れを保った、ローカル専用の対話記録。

1. `.claude/settings.json` のSessionEndが `journal-capture.sh` を呼ぶ。
2. 有効化済みの場合、`journal-worker.sh` がバックグラウンドで動く。
3. `journal-extract.py` がユーザーとassistantのテキストを抽出する。ツール結果・thinking・sidechainは含めない。
4. `journal-prompt.md` と抽出結果を、ツールを無効化した `claude -p` に渡す。
5. `journal/YYYY/` の記録と `INDEX.md` を生成する。
6. 次のSessionStartで `journal-recall.sh` が索引と申し送りを表示する。

## 有効化

```bash
mkdir -p local
touch local/journal-enabled
```

無効化は `local/journal-enabled` を削除する。手動の一時実行では `CONFERENCE_JOURNAL_ENABLED=1` も使用できる。要約はClaudeの認証・モデル利用を伴い、対話本文がモデルへ送られる。プロンプトの機密除外指示は完全な匿名化を保証しない。生成物は `.gitignore` の対象で公開しない。

## 記録の区別

依頼／経緯／決定（確定）／検討したが未決・棄却／結果・成果物／申し送りを分ける。ユーザーの明示的な判断を確認できない案は未決にする。モデルによる分類なので、重要な判断は元の会話で確認する。

`journal/` はセッションの記録、`decisions-log.md` は再利用する学び、`decisions/` は設計判断、`Memory.md` は現在の状態を保存する。

## 検索と回収

```bash
bash .claude/scripts/journal-search.sh migration
export CLAUDE_TRANSCRIPT_DIR='/path/to/this-project-transcripts'
bash .claude/scripts/journal-backfill.sh --days 14
# 対象を確認してから --run を付ける。既定は一覧表示のみ。
```

全プロジェクトのログは自動探索しない。Claudeのtranscript形式は内部形式に依存するため、形式変更時は抽出器の検証が必要。モデルを使わない抽出・保存・検索のテストは `tests/test_journal.py` にある。
