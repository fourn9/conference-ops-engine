// 登壇候補ディープリサーチ（Claude Code 完結・公開版の方法論）
//
// 使い方（Workflow ツールから起動）:
//   Workflow({ name: "speaker-deep-research", args: {
//     today: "YYYY-MM-DD",                       // 必須（スクリプト内で Date は使えない）
//     angles: [{ theme: "2-5", key: "2-5-a", prompt: "..." }, ...],  // 必須：探索角度（テーマ×角度）
//     gateFRules: { "2-5": "ゲートF: ...のみ採用。...は不採用。" },   // 必須：テーマ別ゲートF判別ルール
//     excluded: ["既出・v1既採用の氏名", ...],   // 必須：除外リスト（既出名簿を必ず含めること）
//     cap: 10                                    // 任意：テーマごとの検証上限（既定10）
//   }})
//
// 角度 prompt の書き方は conference/02-speakers/research-brief.md の
// 「本リサーチが対象とする小テーマ」「◯✗例」を圧縮して渡す。
// 結果は { themes: {テーマ: 検証済み候補[]}, searched_sources, dropped } で返る。
// 呼び出し側（メインセッション）が確定/保留リストに整形し
// conference/02-speakers/ に直接書き込む（実行メモ・既出フラグ付き）。

export const meta = {
  name: 'speaker-deep-research',
  description: '登壇候補ディープリサーチ：テーマ×角度の並列探索 → 候補別ゲート検証（G8/G9/ゲートF/R/優先度）',
  whenToUse: '02-speakers のリサーチプロンプト（採否ハードゲート付き）を Claude Code で実行するとき',
  phases: [
    { title: 'Search', detail: 'テーマ×探索角度ごとに並列Web探索（経路A/B）' },
    { title: 'Verify', detail: '候補ごとにURL実在・当事者性・ゲートF・在籍・優先度を検証' },
  ],
}

// args は呼び出し系によっては JSON 文字列で渡る場合があるため正規化する
let ARGS
try {
  ARGS = (args && typeof args === 'string') ? JSON.parse(args) : (args || {})
} catch (e) {
  throw new Error('args の JSON 解析に失敗（文字列で渡す場合は正しい JSON にすること）: ' + e.message)
}
if (!ARGS.today || !ARGS.angles || !ARGS.gateFRules || !ARGS.excluded) {
  throw new Error('args に today / angles / gateFRules / excluded が必要（ファイル冒頭の使い方コメント参照）')
}
if (!Array.isArray(ARGS.angles) || !ARGS.angles.length || !Array.isArray(ARGS.excluded) || !ARGS.excluded.every(n => typeof n === 'string')) throw new Error('angles and excluded must be arrays')
if (typeof ARGS.today !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(ARGS.today)) throw new Error('today must be YYYY-MM-DD')
if (!ARGS.gateFRules || typeof ARGS.gateFRules !== 'object' || ARGS.angles.some(a => !a || !a.theme || !a.key || !a.prompt || typeof ARGS.gateFRules[a.theme] !== 'string')) throw new Error('Every angle needs theme, key, prompt and gateFRules[theme]')
const TODAY = ARGS.today
const EXCLUDED = ARGS.excluded.map(n => n.trim()).filter(Boolean)
const CAP = ARGS.cap ?? 10
if (!Number.isInteger(CAP) || CAP < 1 || CAP > 100) throw new Error('cap must be an integer between 1 and 100')
const PRIORITY_RULES = ARGS.priorityRules || '主催者固有の基準は未設定。priority=B、priority_reason=未評価とする'
const SINCE = ARGS.since || TODAY.slice(0, 4) + '-01-01'
const SCOPE_RULES = ARGS.scopeRules || '指定テーマの実務経験を本人発信から確認できる人を対象とする'
const ANGLES = ARGS.angles
const GATE_F_RULES = ARGS.gateFRules
const THEMES = [...new Set(ANGLES.map(a => a.theme))]

const CANDIDATES_SCHEMA = {
  type: 'object',
  properties: {
    candidates: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string', description: '氏名（日本語表記）' },
          company: { type: 'string' },
          role: { type: 'string' },
          url: { type: 'string', description: '本人発信記事/スライドのURL（実アクセス確認済みのみ）' },
          title: { type: 'string', description: '記事/登壇タイトル' },
          date: { type: 'string', description: '公開日 YYYY-MM' },
          evidence_quote: { type: 'string', description: '小テーマ該当部分の本文引用（1-3行）' },
          theme_fit: { type: 'string', description: 'どの対象小テーマ要素に対応するか' },
          source_type: { type: 'string', description: '企業技術ブログ/個人ブログ/登壇スライド/動画/書籍/Podcast' },
        },
        required: ['name','company','url','title','date','evidence_quote','theme_fit'],
      },
    },
    searched_sources: { type: 'array', items: { type: 'string' }, description: '実行した検索クエリ・走査したソース一覧' },
  },
  required: ['candidates','searched_sources'],
}

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    company_current: { type: 'string', description: '調査日時点の現所属（確認できた範囲）' },
    role_current: { type: 'string' },
    employment_evidence: { type: 'string', description: '在籍確認の根拠と確認日／確認不能ならその旨' },
    url_ok: { type: 'boolean', description: 'URLが実在し本文を確認できたか' },
    author_match: { type: 'boolean', description: '記事の発言者が候補者本人と一致するか' },
    g8_type: { type: 'string', description: 'a=当事者発信 / b=第一人者 / NG' },
    gate_f: { type: 'string', description: '採用/不採用 とその判別カテゴリ' },
    gate_f_reason: { type: 'string' },
    article_date: { type: 'string' },
    scale_insight: { type: 'string', description: '事業規模インサイト（記事内の具体値。なければ「記載なし」）' },
    priority_reason: { type: 'string', description: '指定された優先度基準の根拠。未設定なら未評価' },
    priority: { type: 'string', description: 'A/B/C' },
    ai_context: { type: 'string', description: 'AI文脈/非AI文脈 等' },
    verdict: { type: 'string', description: '確定/保留/不採用' },
    verdict_reason: { type: 'string' },
    recommend_reason: { type: 'string', description: '登壇推薦理由（40-60字）。不採用なら空でよい' },
    summary: { type: 'string', description: '記事内容の要約（40-60字・本人が何を設計判断したか）' },
  },
  required: ['name','company_current','url_ok','author_match','g8_type','gate_f','gate_f_reason','article_date','priority_reason','priority','ai_context','verdict','verdict_reason'],
}

const COMMON_FINDER_RULES = `
共通ルール（厳守）:
- 対象範囲: ${SCOPE_RULES}
- 記事・登壇の対象期間: ${SINCE} 以降。
- 必ずWebFetchで記事本文を開き、著者名・該当箇所の引用を確認してから候補に含める。スニペットだけで採用しない。
- 実在しない人物・記事・URLの創作は重大違反。確認できないものは含めない。
- 概念解説・入門記事・業界トレンドまとめは除外。「私たちは〜を設計した」という当事者発信、または書籍・標準化実績のある第一人者の独自フレームワーク提示のみ。
- 対象の規模・地域・職種は指定された対象範囲に従う。指定がなければ推測で制限しない。
- 以下の人物は既出のため除外: ${EXCLUDED.join('、')}
- 最大8名まで。質を優先し、確認できた候補のみ返す。
- 探索したクエリとソースをsearched_sourcesに必ず記録する。
返答は最終的にStructuredOutputツールで返すこと。`

phase('Search')
log(`${ANGLES.length}角度の並列探索を開始（${THEMES.length}テーマ）`)

const searchResults = await parallel(ANGLES.map(a => () =>
  agent(a.prompt + COMMON_FINDER_RULES, { label: `find:${a.key}`, phase: 'Search', schema: CANDIDATES_SCHEMA })
    .then(r => r ? ({ ...r, theme: a.theme, key: a.key }) : null)
))

const valid = searchResults.filter(Boolean)
const allSources = valid.flatMap(r => r.searched_sources || [])

// グローバル重複排除（同一人物は最初のテーマに割当）＋除外リスト適用
const seen = new Set(EXCLUDED.map(n => n.replace(/\s/g, '')))
const byTheme = Object.fromEntries(THEMES.map(t => [t, []]))
for (const r of valid) {
  for (const c of (r.candidates || [])) {
    const nameKey = (c.name || '').replace(/\s/g, '')
    if (!nameKey || seen.has(nameKey)) continue
    if (EXCLUDED.some(ex => nameKey.includes(ex.replace(/\s/g, '')))) continue
    seen.add(nameKey)
    byTheme[r.theme].push(c)
  }
}
log('候補抽出: ' + THEMES.map(t => `${t}=${byTheme[t].length}名`).join(' / '))

phase('Verify')
const verifyTheme = async (theme) => {
  const list = byTheme[theme].slice(0, CAP)
  if (byTheme[theme].length > CAP) log(`${theme}: ${byTheme[theme].length}名中、上位${CAP}名のみ検証（残りは未検証として返却）`)
  const results = await parallel(list.map(c => () =>
    agent(`以下の登壇候補を検証せよ。本日: ${TODAY}。

候補: ${c.name}（${c.company}・${c.role || '役職不明'}）
記事: ${c.title}（${c.date}）
URL: ${c.url}
引用: ${c.evidence_quote}
テーマ適合主張: ${c.theme_fit}

検証タスク（全て実施）:
1. URLにWebFetchでアクセスし、実在・著者一致・引用の正確性を確認（url_ok / author_match）。アクセス不能なら検索で同記事を探し、見つからなければurl_ok=false。
2. G8判定: (a)自社プロダクトの当事者発信（「私たちは」等の自社体験＋本人の設計判断）か、(b)第一人者（書籍/標準化実績＋独自フレームワーク提示）か、NG（トレンド解説・他社事例まとめ・概念解説）か。
3. ${GATE_F_RULES[theme]}
4. 在籍確認: Web検索で${TODAY.slice(0,4)}年時点の現所属を確認（公式X・企業メンバー紹介・直近登壇プロフィール等）。退職・異動があれば現所属に更新。
5. 優先度: ${PRIORITY_RULES}。priority_reason に根拠を記録する。基準や証拠が不明なら priority=B、未評価と明記。
6. 記事内の事業規模インサイト（ユーザー数・ID数・データ量・運用年数等の具体値）を抽出。なければ「記載なし」。
7. verdict判定: url_ok && author_match && G8(a|b) && ゲートF採用 && 記事${SINCE}以降 → 「確定」。本人発信の裏取りが不完全だが取り組みは実在 → 「保留」。それ以外 → 「不採用」。
   判定は厳格に。不確実なら確定にしない。創作・推測での補完は禁止。
結果はStructuredOutputで返す。`, { label: `verify:${theme}:${c.name}`, phase: 'Verify', schema: VERIFY_SCHEMA })
      .then(v => v ? ({ ...v, orig: c }) : null)
  ))
  return results.filter(Boolean)
}

const verified = await parallel(THEMES.map(t => () => verifyTheme(t)))
const themesOut = Object.fromEntries(THEMES.map((t, i) => [t, verified[i] || []]))

const count = (arr, k) => (arr || []).filter(x => x.verdict === k).length
log('検証完了: ' + THEMES.map(t => `${t} 確定${count(themesOut[t],'確定')}/保留${count(themesOut[t],'保留')}`).join(' | '))

return {
  themes: themesOut,
  searched_sources: allSources,
  dropped: Object.fromEntries(THEMES.map(t => [t, byTheme[t].slice(CAP).map(c => `${c.name}（${c.company}）`)])),
}
