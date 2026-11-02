---
description: フック不発・過去分の transcript を一括ジャーナル化する（dry-run→確認→実行）
argument-hint: [--days N | --all]
---

# /journal-backfill [--days N | --all]

`CLAUDE_TRANSCRIPT_DIR` に明示した、このプロジェクトの未ジャーナルの transcript を洗い出し、まとめてジャーナル化する。
クラッシュで SessionEnd が不発だった分や、仕組み導入前の過去セッションの回収に使う。

## 動作

1. `CLAUDE_TRANSCRIPT_DIR` を設定し、`bash .claude/scripts/journal-backfill.sh [--days N | --all]` を **dry-run** で実行
2. 件数・各セッションの実ユーザーターン数を提示し、コスト目安（1セッションあたり haiku 1回・
   入力上限6万字）を添えて実行可否を確認する（安全装置: 課金を伴う一括処理）
3. 承認済みの範囲でjournalを有効化し、`--run` を付けて実行。有効化手順は `journal/README.md`。進捗は `journal/.capture.log` で追える
4. 完了後、生成件数と trivial スキップ件数を報告する

## 引数

- `--days N` — 直近 N 日分のみ（既定 14）
- `--all` — 残存する全 transcript

## 注意

- 実行は直列（1件ずつ）。件数が多いときは時間がかかる旨を先に伝える
- 既にジャーナル済み（INDEX に session id あり）のものは自動でスキップされる
