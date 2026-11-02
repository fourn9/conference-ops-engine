---
name: speaker-deep-research
description: 確定済みの登壇テーマを自然文で受け、テーマ×角度の並列ディープリサーチ（speaker-deep-research Workflow）を回して確定/保留候補を出典付きで出す。THEME を受け取り PREFLIGHT 確認→args組立→Workflow起動→md+tsv整形。
---

# speaker-deep-research（登壇候補ディープリサーチ）

確定済みの登壇テーマに対して、当事者発信に絞った登壇候補を並列探索＋ゲート検証で集めるスキル。
探索の実体は `.claude/workflows/speaker-deep-research.js`（Workflow）。本スキルはそれを駆動する
オーケストレータ。考え方の正典は `methodology/conference-planning-framework.md`。

## パラメータ（メソッドコール）

| パラメータ | 説明 | 既定 |
|---|---|---|
| THEME | 確定済みの登壇テーマ（自然文。例「認証認可・ゼロトラストの実装当事者」） | 必須 |
| EXCLUDED | 既出名簿（過去採用済み氏名の配列） | 任意。OUTDIR に過去結果があれば読む／無ければ空 |
| OUTDIR | 出力先 | `<event>/02-speakers/` |

未指定は実行前に確認する。テーマが未確定なら探索に入らず、先にテーマを固める。

## 実行手順

### Step 1: PREFLIGHT 確認ゲート（必須・停止点／`methodology/conference-planning-framework.md`）
探索を始める前に、次の4点を提示して確認する。1つでも未確定なら探索より先に固める。
1. **テーマ確定**：THEME が1つに絞れているか（複数なら分割）
2. **コアターゲット近接**：そのテーマがイベントのコアターゲット／近接領域に合うか
3. **既出名簿**：EXCLUDED（過去採用済み）を渡す。OUTDIR に過去の `speaker-candidates.*` があれば氏名を吸い上げて既定に含める
4. **ゲート判別ルール**：そのテーマで「採用／不採用」をどう分けるか（当事者発信か解説か、隣接職種の扱い等）を1〜2行で言語化

承認が出るまで Workflow を起動しない。

### Step 2: args 組立（確認付き）
THEME から以下を組み立て、提案内容を確認してから起動する。
- `angles`：テーマに対する探索角度を2〜4本。各 `{ theme, key, prompt }`。
  - `theme` は THEME を表す短い識別子（例 `"authz"`）。`key` は角度識別子（例 `"authz-a"`）。
  - `prompt` は「本リサーチが対象とする小テーマ」＋「◯例／✗例」を圧縮して書く（誰の・どの発信を採るか）。
  - 角度は探索経路を変えて重複を減らす（例：A=企業技術ブログ／登壇スライド、B=個人発信／Podcast/書籍）。
- `gateFRules`：`{ <theme>: "ゲートF: …のみ採用。…は不採用。" }`。Step 1-④ の判別を Workflow 用に明文化。
- `excluded`：Step 1-③ の既出名簿。
- `today`：本日 `YYYY-MM-DD`。

### Step 3: Workflow 起動
確認済みの args で既存 Workflow を起動する:

```js
Workflow({ name: "speaker-deep-research", args: {
  today: "<本日 YYYY-MM-DD>",
  angles: [<確認済み angles>],
  gateFRules: { <theme>: "<判別ルール>" },
  excluded: [<既出名簿>],
}})
```

### Step 4: 返り値を md+tsv に整形して出力
返り値 `{ themes, searched_sources, dropped }` を OUTDIR に書き出す:
- `speaker-candidates.md` … テーマ別に **確定／保留** リスト。各候補は氏名・所属・推薦理由（40-60字）・根拠引用・URL・優先度の判断根拠・priority(A/B/C)。
- `speaker-candidates.tsv` … 名簿のタブ区切り（氏名 / 所属 / テーマ / priority / verdict / URL）。

各ファイル冒頭に実行メモを必ず付す:
- 実行系（speaker-deep-research workflow・本日日付）
- 検証範囲の上限（cap・未検証として返った候補は dropped に出る）
- 既出フラグ（EXCLUDED で除外した氏名の扱い）
- searched_sources（実行した検索クエリ・走査ソース）

### Step 5: 完了報告
テーマ別の確定／保留件数と dropped（未検証候補）を報告し、出力ファイルのパスを示す。

## メモ
- 当事者性判定（G8：当事者発信か解説・伝聞か）・採否ハードゲートの正典は `methodology/conference-planning-framework.md`。本スキルに重複コピーしない。
- 選定記録（確定後の意思決定ログ）は `methodology/conference-planning-framework.md` の `02-speakers/_selection/` 運用に従う（本スキルの範囲外）。
- local/vault に依存しない。出力は必ずローカル OUTDIR。
- 公開版 Workflow を利用する（探索・検証ロジックは Workflow 側が正）。

`Workflow` ツールがない環境では `docs/workflows.md` の同梱ランナーを利用する。確定は根拠を確認した候補の状態であり、登壇承諾や最終選定ではない。

接続先・保存先の共通設定は `docs/configuration.md` を参照。既にユーザーが明示した条件は再確認せず、その範囲で進める。
