# Conference Ops

プロジェクトの前提は `AGENTS.md` を参照する。

## 調査と最終判断

`methodology/conference-planning-framework.md` と `methodology/insight-gates.md` に従い、出典・不確実性・ヒアリングとのつながりを残す。候補の根拠確認と、登壇の承諾・最終採用を混ぜない。

## 設定と保存先

`docs/configuration.md` を参照。イベントデータは `conference/`、調査ノートは `local/vault/`。これらの実データを公開リポジトリにコミットしない。

## Workflow

`Workflow` APIがある環境ではスキル記載の呼び出しを使う。ない環境では `scripts/run-workflow.mjs` を使う。`docs/workflows.md` に入力・agent契約・実行例がある。実調査は `--live` を指定したときだけモデルを呼ぶ。

## ジャーナル

SessionStartは既存journalの索引と申し送りを読む。SessionEndの自動要約は `local/journal-enabled` が存在するときだけ動く。要約モデルに対話本文を渡すため、有効化は利用者が選ぶ。生成されたjournalはローカル専用。

## 自律的学習プロトコル

観察した学びは `decisions-log.md`、再利用候補は `skills/experimental/`、設計判断は `decisions/`、一時的な失敗は `.failure-inbox/` に分ける。詳細は `methodology/autonomous-learning-protocol.md`。`/reflect-session` と `/curate` の提案を、確定したルールとして自動適用しない。
