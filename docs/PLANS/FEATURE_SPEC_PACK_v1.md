> Authority: SPEC (Level 2, Binding)
> Canonical: YES (for these new features)
> Owner: Human Authority (金子優)
> Date: 2026-02-16
> Scope: New features only (Citation Tree / 3D Map / Auto Harvester / R&D Intel / Drive Collector / Market Proposal)
> Dependency: docs/MASTER_SPEC.md, docs/SPEC_AUTHORITY.md, docs/BUNDLE_CONTRACT.md, docs/DoD.md

# FEATURE SPEC PACK v1 — Citation Tree / 3D Paper Map / Auto Harvester / R&D Intel / Drive Collector / Market Proposal

## 0. 最重要原則（このSPECの前提）
- 既存の **BUNDLE_CONTRACT（必須10ファイル）** を絶対に壊さない。
- 追加成果物は `logs/runs/{run_id}/artifacts/` に置く（必須10ファイルとは分離）。
- **status == "success" ⇔ gate_passed == true** を維持する。
- 収集の自動化は可能。ただし **Human Authority を空文化する自動承認はしない**。
  - 自動化は「収集まで」。解析・結論生成・採用判断はゲートと承認の枠内で行う。

## 1. Feature A：Citation Tree（参考文献の樹形図）
### 1.1 目的
論文Aの参考文献（第1階層）と、その参考文献の参考文献（第2階層）を樹状に可視化し、
論文Aの立ち位置・必要性・ストーリーを理解可能にする。

### 1.2 入力（Inputs）
- paper_id: DOI / PMID / arXiv_id / internal_id のいずれか
- depth: 1 or 2（デフォルト2）
- max_refs_per_node: int（デフォルト50）
- dedup_strategy: "doi_first" | "title_year_author_fallback"
- source_priority: ["openalex", "crossref", "semantic_scholar", "pdf_ref_parse"]（上から優先）

### 1.3 出力（Outputs）
必須10ファイルに加え、以下を artifacts に出す：
- artifacts/citation_tree.nodes.jsonl
  - node: {node_id, title, year, venue, ids:{doi,pmid,arxiv}, level, inbound_cites, score_optional}
- artifacts/citation_tree.edges.jsonl
  - edge: {from_node_id, to_node_id, type:"cites"}
- artifacts/citation_tree.mmd
  - Mermaid graph（巨大な場合は分割して複数ファイル可）
- artifacts/citation_tree.summary.md
  - (a) hub nodes（中心性上位）
  - (b) cluster rough interpretation（粗いクラスタ説明）
  - (c) story gaps（欠けていそうな前提領域候補）

### 1.4 ルール（Rules）
- depth=2は爆発しやすいので、max_refs_per_node を必ず強制する。
- 参照のID解決率（resolved_reference_rate）を audit.json に書く。
- 取得ソースと件数を run.json または audit.json に記録する。

### 1.5 テスト（DoD）
- DOIあり/なしでも node_id が安定する（dedup_strategyが機能する）
- depth=2でノード数が上限制御される
- 取得元が落ちても graceful degradation（縮退してもRunが監査可能）

## 2. Feature B：3D Paper Map（論文A中心の3次元配置）
### 2.1 目的
論文Aを中心（0,0,0に相当）として、関連論文10〜50本を3D空間に配置し、
“関連の構造”を視覚的に把握できるようにする（UI表示も含む）。

### 2.2 入力（Inputs）
- paper_id
- k_neighbors: 10〜50
- embedding_model: 既存のSentenceTransformer系（モデル名とversion固定）
- reduction: "umap" | "tsne"
- seed: int（必須。再現性のため固定）
- neighbor_sources:
  - semantic: embedding cosine
  - citation: 可能なら共引用/書誌結合
  - fusion: RRF等（パラメータ固定）

### 2.3 出力（Outputs）
- artifacts/paper_map.points.json
  - {paper_id, title, year, x,y,z, score, cluster_id, distance_to_center}
- artifacts/paper_map.config.json
  - {embedding_model, reduction, seed, params}
- artifacts/paper_map.html
  - 単体で開ける可視化（オフライン閲覧可能が望ましい）
- artifacts/paper_map.summary.md
  - クラスタ解釈、近傍TopN、外れ値（なぜ外れ値か）

### 2.4 ルール（Rules）
- seed固定で、同一入力は同等の配置を再現できること（許容誤差はSPEC内で定義）。
- 埋め込み欠損時はfallbackし、必ず “低信頼” フラグを出す。

### 2.5 テスト（DoD）
- 同一paper_idで2回実行して座標がほぼ一致
- k=10/50の両方で破綻しない
- fallback時に “低信頼” が明示される

## 3. Feature C：Auto Harvester（自動収集：PubMed等を監視してOA中心に収集）
### 3.1 目的
ユーザーがアクティブに動かなくても、設定した条件に従い、API制限内で自動的にOA論文を収集する。
監視→リスト化→キュー→順次収集→保存を自動で回す。

### 3.2 入力（Inputs）
- harvest_config.yaml（新規・ただし本タスクでは作らない：別タスク）
  - sources: pubmed/arxiv/crossref/openalex 等
  - watch_interval_minutes
  - query_terms / mesh_terms / journals / authors
  - max_per_day（API・規約順守）
  - oa_only: true/false（デフォルトtrue）
  - storage_paths（data/harvest 等）
- mode:
  - "monitor_only" | "monitor_and_fetch" | "fetch_from_list"

### 3.3 出力（Outputs）
永続（data）：
- data/harvest/seen_ids.jsonl
- data/harvest/queue.jsonl
- data/harvest/errors.jsonl
- data/harvest/metrics.json
Run artifacts：
- artifacts/harvest_run_summary.md（今回何を検知し、何を取得し、何が失敗したか）

### 3.4 ルール（Rules）
- レート制限：token bucket + exponential backoff（429/5xx）
- 重複排除：doi優先、なければtitle/year/authorで近似
- 収集は自動でよいが、解析や結論生成は gate と承認の枠内で行う（Human Authority保持）
- OAでないものは無理に取らない（規約違反回避）。理由を記録して終了。

### 3.5 テスト（DoD）
- 中断→再開で二重取得しない
- API停止でも監視ループが死なず次回復帰
- OAでない場合は理由が残る

## 4. Feature D：R&D Intel（arXiv＋開発情報の監視→改善提案）
### 4.1 目的
arXiv等の最新動向を定期監視し、JARVISの機構・パイプラインの上位互換になり得るアイデアを抽出し、
根拠付きでアップグレード提案する。

### 4.2 入力（Inputs）
- rd_intel_config.yaml（新規・ただし本タスクでは作らない：別タスク）
  - arxiv_categories
  - keywords
  - interval_hours
  - allowed_sources（規約順守の手段のみ：RSS/公式API等）

### 4.3 出力（Outputs）
- artifacts/rd_intel.digest.md（要約）
- artifacts/rd_intel.candidates.json（候補：効果、依存、リスク）
- artifacts/rd_intel.recommendations.md（採用優先度と理由）
- （可能なら）PoCの検証結果：検証できない場合は「できない理由」を明記（推測禁止）

### 4.4 採用/不採用基準（Rules）
- 採用：KPIで測れる改善で、MASTER_SPEC（監査・契約）を壊さない
- 不採用：ブラックボックス化／規約違反前提／再現性が落ちる

### 4.5 テスト（DoD）
- 参照ソースが明示されている（根拠なし断言なし）
- “検証した/していない”が区別されている

## 5. Feature E：Drive Collector（PDF＋BibTeXを自動収集してGoogle Driveへ格納）
### 5.1 目的
指定した雑誌・分子名・クエリで論文を収集し、PDFとBibTeXを自動取得してGoogle Drive指定フォルダへ格納する。

### 5.2 入力（Inputs）
- collector_config.yaml（新規・ただし本タスクでは作らない：別タスク）

### 5.3 出力（Outputs）
Drive構造（固定）：
- DriveRoot/{topic}/{year}/{paper_id}/paper.pdf
- DriveRoot/{topic}/{year}/{paper_id}/citation.bib
- DriveRoot/{topic}/{year}/{paper_id}/meta.json

### 5.4 ルール（Rules）
- OA判定：Unpaywall/PMC優先
- PDF未取得でもBibTeXとメタは保存（理由記録）
- 二重格納禁止（paper_id解決とalias管理）

### 5.5 テスト（DoD）
- 中断→再開で重複格納しない
- フォルダ命名が安定（aliasで追跡）

## 6. Feature F：Market Proposal（データ資産でニッチアプリ案を提案）
### 6.1 目的
収集した論文・メタデータを資産として、市場調査を挟みつつ作るべきアプリ/サイト案を提案する。

### 6.2 入力（Inputs）
- market_config.yaml（新規・ただし本タスクでは作らない：別タスク）

### 6.3 出力（Outputs）
- artifacts/product_ideas.deck.md
- artifacts/product_ideas.json
- artifacts/product_ideas.sources.md

### 6.4 ルール（Rules）
- 断言は必ず根拠（論文＋市場データ＋競合分析）を伴う
- 推測の場合は推測と明記

### 6.5 テスト（DoD）
- 参照ソースが明示されている
- 競合と差別化が説明されている

## 7. このSPEC PackのDoD
- 本ファイルが docs/PLANS/FEATURE_SPEC_PACK_v1.md に存在
- 各Featureに Inputs/Outputs/Rules/DoD が揃っている
- BUNDLE_CONTRACT（必須10ファイル）と矛盾しない
- 自動化が Human Authority を空文化しない
