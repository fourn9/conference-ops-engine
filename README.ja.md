# Conference Ops Engine

技術カンファレンスの企画・運営に使うworkflow、agentの指示、スキル、イベント用ワークスペース。 [English](README.md)

共通エンジンとイベント運営用の2つのプロジェクトから、公開可能な実装を1つにまとめています。実際の調査プロンプト、JSON schema、並列処理、文書生成、セッション記録、更新配布の仕組みを含みます。個別イベントの記録や接続情報は含めていません。

## 仕組みとコード

| 機能 | 処理 | 実装 |
|---|---|---|
| 登壇候補調査 | テーマ×角度で並列探索 → 重複・既出除外 → 上限適用 → 候補ごとに出典・本人性・テーマ適合を検証 | [speaker-deep-research.js](.claude/workflows/speaker-deep-research.js) |
| 企画マトリクス | 規模×目的を公式事業情報から調査 → 職種×目的を当事者発信と採否ゲートで調査 | [conference-matrix.js](.claude/workflows/conference-matrix.js) |
| 業務スキル | 登壇依頼、スポンサー対応、趣意書、メール、告知、報告、振り返り | [16個のSKILL.md](.claude/skills) / [呼び出しコマンド](.claude/commands) |
| 趣意書生成 | Google Doc複製 → 5か所の空欄を末尾から置換 → 箇条書き化 → 氏名・所属の置換 | [fill_prospectus.py](.claude/skills/speaker-prospectus/fill_prospectus.py) |
| セッション記録 | 対話抽出 → 要約 → journal/index保存 → 次回の申し送り・検索 | [hooks](.claude/settings.json) / [scripts](.claude/scripts) |
| イベントごとの導入 | 12領域のフォルダ雛形と、バージョン固定の共通資産同期 | [イベント雛形](templates/_instance) / [同期処理](scripts/sync-engine.sh) |

agentはworkflow内の `agent(prompt, { label, phase, schema })` に定義しています。独立した `.claude/agents` フォルダは元の構成にもありません。探索agent・検証agentの役割、プロンプト、入出力の構造をコードで確認できます。

## ローカルで動かす

Node.js 22+。補助処理にはPython 3.9+、Bash、Gitを使います。次の実行は認証・パッケージ追加・モデル呼び出し不要です。

```sh
node scripts/run-workflow.mjs speaker-deep-research --input examples/speaker-research.args.json --fixture examples/speaker-research.responses.json
node scripts/run-workflow.mjs conference-matrix --input examples/matrix.args.json --fixture examples/matrix.responses.json
```

元のworkflow本体に、明示的な架空の応答データを渡して処理を確認します。モデルの調査精度を示すものではありません。実調査の入口も同梱していますが、Claude Codeの認証と利用者自身の入力・予算設定が必要です。[実行手順と制約](docs/workflows.md)

## イベントで使う

```sh
cp -R templates/_instance ../my-conference
cd ../my-conference
bash scripts/sync-engine.sh --dry-run
bash scripts/sync-engine.sh
```

`conference/event.md` を編集し、必要な外部ツールを接続します。同期対象は共通エンジンの管理パスで、イベント本文・個人設定・journalは保持します。実務データを入れるイベント用リポジトリは非公開で管理してください。[設定](docs/configuration.md)

```sh
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check-publication.py
```

[元実装との対応・公開時の変更](docs/source-map.md) / [企画手順](methodology/conference-planning-framework.md) / [journal](journal/README.md) / [趣意書](docs/google-docs.md) / [公開範囲](PUBLICATION.md)
