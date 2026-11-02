# 自律的学習プロトコル — 実行ガイド

> `CLAUDE.md` §自律的学習プロトコルの詳細版。具体例と判断基準を含む。
> CLAUDE.md は宣言、こちらは「迷ったとき何を見るか」のリファレンス。
> 設計の出自は public 雛形 conference_planning_v2（hermes-agent の四層構造を Claude Code プリミティブに再構成）。本リポ（event-workspace）の既存資産に寄せて適応した版。

## 0. 本リポでの構成（適応版）

| hermes / v2 の層 | 本リポでの実装 |
|---|---|
| 指示注入（CLAUDE.md §C） | `CLAUDE.md` §自律的学習プロトコル |
| 書き込み口（7 コマンド） | `.claude/commands/`（record-learning / draft-skill / draft-adr / promote-pattern / patch-skill / curate / reflect-session） |
| キュレータ | `/curate` + `.claude/settings.json` の SessionStart/Stop フック |
| 状態ストア（LEARNINGS/MEMORY/USER…） | `decisions-log.md`（学習ログ）／`local/vault/Memory.md`＋`conference/Memory.md`（事実・状態）／`USER.md`（人物像）／`skills/{experimental,stable,archived}/`／`decisions/`／`.failure-inbox/`＋`failure-patterns.md` |

v2 との主な違い：`LEARNINGS.md` を新設せず既存 `decisions-log.md` を学習ログ層に流用、`MEMORY.md` を新設せず `local/vault/Memory.md` を正とする、既存 `.claude/skills/` のネイティブスキルは触らず新規 `skills/` にライフサイクルを置く。

## 1. 「保存に値する」を判断する 3 つの問い

1. **同じ気付きを次回も役立てたいか？** No → 保存しない（一時状態）
2. **これは観察か、命令か？** 観察（「X を好む」）→ 書ける／命令（「常に X せよ」）→ 書き直すか書かない
3. **これは事実か、推測か？** 事実 → 書ける／推測 → `[推測]` を付けるか書かない

3 つすべて Yes（または事実）でなければ保存しない。

## 2. 書き込み先の選び方

| 観察したもの | 書き込み先 | コマンド |
|---|---|---|
| 「ユーザーは X を好む」（人物像） | `USER.md` | 直接 Edit |
| 「この領域では Y が規約・確定事項」 | `local/vault/Memory.md` / `conference/Memory.md` | 直接 Edit |
| 「Z という気付き」（時系列の学び） | `decisions-log.md` | `/record-learning` |
| 「W という反復可能な手順」 | `skills/experimental/` | `/draft-skill <name>` |
| 「V という重い判断」 | `decisions/` | `/draft-adr <topic>` |
| 「U という失敗パターン」（初回〜2 回目） | `.failure-inbox/` | 直接 Write |
| 「U という失敗パターン」（3 回目以降） | `failure-patterns.md` | `/promote-pattern` |
| 「既存スキルの不備」 | 該当スキル | `/patch-skill <path>` |

## 3. anti-noise ルール — 書いてはいけないもの

絶対に書かない：PR/Issue/commit SHA、「X を修正」「Y を出した」等の取引的記録、一時状態（途中経過・TODO）、推測の事実化、ユーザーへのネガティブ評価、機密（パスワード・API キー・内部 URL・公開許諾のない個人名）。

## 4. declarative > imperative

| ✗ imperative | ✓ declarative |
|---|---|
| 「常に簡潔に応答せよ」 | 「ユーザーは簡潔な応答を好む」 |
| 「登壇者は必ず当事者発信で選べ」 | 「当事者発信ソースの採用率が高い（`methodology/conference-planning-framework.md`）」 |

ルールを書くな、観察を書け。ルールは agent が観察から推論する。

## 5. Patch on discovery

スキル使用中に古さ・誤りに気づいたら、待たずにその場で `/patch-skill`。
ただし `created_by: human` かつ `pinned: true`（`.claude/skills/` のネイティブスキル含む）は直接編集せず、`/record-learning` で「このスキルは古い可能性がある」と記録し、修正提案を出して承認を待つ。

## 6. /curate の閾値（デフォルト）

- 昇格：`usage_count >= 3 && patches_needed == 0`
- アーカイブ：`last_used > 90 日 && usage_count <= 1`
- failure-pattern 昇格：同 `pattern_id` が `.failure-inbox/` に 3 件以上
- 周期提案：`.claude/curator-state.json > last_run` から 14 日以上経過

3 イベント分回して経験データが溜まったら見直す。

## 7. トラブルシューティング

- **agent が何も保存しない** → §1 の 3 つの問いを通したか。通っても動かなければ明示的に「`/record-learning` で保存して」と指示。
- **保存しすぎる** → §3 を読み直し、`/curate` で重複統合候補を確認。
- **`/curate` の提案が信頼できない** → 候補スキルを Read。`created_by: agent` は品質ゲート未通過。信頼できないものは `pinned: true` にする。

## 8. 関連

- `CLAUDE.md` §自律的学習プロトコル（宣言）
- `.claude/commands/`（各書き込み口）
- `templates/_instance/skills/README.md`（スキルライフサイクル）
- `templates/_instance/.failure-inbox/README.md`（失敗パターン inbox）
