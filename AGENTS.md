# Conference Ops Engine

カンファレンスの企画・運営を支援する公開実装。個別イベントの実データはこのリポジトリの管理対象にしない。

- workflow本体は `.claude/workflows/`。agentへの役割・プロンプト・JSON schemaはその中に定義されている。
- タスク手順は `.claude/skills/*/SKILL.md`、呼び出しラッパーは `.claude/commands/`。
- 対話記録の処理は `.claude/scripts/journal-*`。
- 動作確認は `node --test tests/*.test.mjs` と `python3 -m unittest discover -s tests -p 'test_*.py'`。
- 生成物、個人メモ、実在者の記録、接続先ID、認証情報は `local/` または別の非公開イベントワークスペースに保存する。
- 実際の送信・共有・契約や最終選定は、利用者がその操作を依頼した範囲で行う。下書きや調査結果から送信許可を推測しない。
- ユーザーから既に依頼・承認されている編集や公開を、スキル内の一般的な確認手順だけを理由に再確認しない。
- 公開ファイルを変更するときは `python3 scripts/check-publication.py` で公開対象を確認する。

初期の説明用デモは実装と混同しないよう削除済み。現在の主要ファイルは元の運用コードから公開不可情報を除いたもの。公開時の変更点は `docs/source-map.md` を参照。
