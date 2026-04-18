# Briefing Note Generator — Agent Architecture Plan

## Context

OCHA hackathon challenge: build a system that ranks humanitarian crises by the gap between documented need and available funding, and generates briefing notes for coordinators. The system must handle politically sensitive data representing real people in vulnerable situations. The core design constraint — stated explicitly in both `challenge.md` and `workshop_notes.md` — is **not to be overconfident**: outputs must be decision support tools, not automated decision-makers.

The user also wants a filter/keyword UI so coordinators can focus on specific regions, sectors, or crisis types before running the analysis.

---

## Architecture: Six-Agent Linear Pipeline

### Agent 1: `QueryInterpreterAgent`
- **Model:** `claude-haiku-4-5` (low cost, high throughput)
- **Input:** raw NL query string + UI filter state
- **Output:** `QuerySpec` (Pydantic) — structured criteria with `interpretation_confidence` + `interpretation_notes`
- **Uncertainty:** ambiguous terms (e.g. "Sahel") emit `confidence: "medium"` and a plain-English note shown in the briefing header

### Agent 2: `DataIngestorAgent`
- **Model:** none — pure Python
- **Input:** `QuerySpec`, paths to 5 CSV datasets
- **Output:** `IngestedDataset` — list of `CrisisRecord` objects + `DataQualityReport`
- **Uncertainty:** every `CrisisRecord` has a `data_flags: [str]` field — non-optional, carries caveats like "HNO data is 3 years old" or "No formal HRP on file"

### Agent 3: `GapScoringAgent`
- **Model:** none — pure Python (`pandas`, `numpy`)
- **Input:** `IngestedDataset`
- **Output:** `ScoredCrisisList` — ranked crises with `gap_score`, `coverage_ratio`, `score_confidence` (HIGH/MEDIUM/LOW), and `score_caveats`
- **Gap score formula:** `(1 - coverage_ratio) * log_pin_weight`; crises without HRP ranked separately; bare numbers never emitted — always paired with confidence tier
- **Bonus:** `structural_neglect_flag` set when underfunded for 3+ consecutive years

### Agent 4: `ContextEnrichmentAgent`
- **Model:** `claude-sonnet-4-6` with `web_search` tool
- **Input:** top-N `ScoredCrisis` records (default 5)
- **Output:** `EnrichedContext` per crisis — IPC phase, UNHCR displacement, media visibility, donor concentration, prior-year coverage ratios
- **Uncertainty:** system prompt bans inference; every figure requires source URL + publication date; missing figures return `null` with explanation; `enrichment_caveats` is non-optional
- **Runs in parallel** via `asyncio.gather()` — one API call per crisis

### Agent 5: `BriefingNoteWriterAgent`
- **Model:** `claude-opus-4-7` with `thinking: {"type": "adaptive"}`, streaming enabled
- **Input:** `ScoredCrisisList` + `EnrichedContext` list + `QuerySpec` + `DataQualityReport`
- **Output:** `BriefingNote` — executive summary, ranked table (with confidence column), top-3 narratives, methodology disclosure, limitations list (minimum 3, enforced)
- **Banned phrases in system prompt:** "the data shows", bare percentages, "X country is underfunded" without qualifier
- **Required constructions:** "available data from [source, year] suggests...", "approximately [range]", confidence level on every gap score

### Agents 6a–6c: Review Panel (run in parallel via `asyncio.gather()`)

Three independent reviewers, each with a narrow focus and extended thinking enabled. They run simultaneously on the same draft and cannot see each other's outputs — independence is the mechanism that catches what a single reviewer would rationalize away.

**6a. `FactCheckReviewAgent`**
- **Model:** `claude-sonnet-4-6` with `thinking: {"type": "enabled", "budget_tokens": 5000}`
- **Focus:** Hallucination and fabrication — does every figure in the note actually appear in `ScoredCrisisList` or `EnrichedContext`? Does any country, statistic, or source citation appear that wasn't in the input data?
- **Checklist:** (1) cross-reference every numeric claim against input data, (2) flag any source URL not present in `EnrichedContext`, (3) flag any country name not in `ScoredCrisisList`, (4) flag any claim using language stronger than the underlying enrichment confidence level permits

**6b. `ConfidenceCalibrationReviewAgent`**
- **Model:** `claude-sonnet-4-6` with `thinking: {"type": "enabled", "budget_tokens": 5000}`
- **Focus:** Language-level overconfidence — does any prose claim a higher certainty than the `score_confidence` or `enrichment_confidence` of the underlying record?
- **Checklist:** (1) scan for banned phrases ("the data shows", "X is underfunded"), (2) verify every coverage ratio has a confidence qualifier, (3) verify LOW-confidence records are described with appropriately hedged language, (4) check the executive summary explicitly names the most significant data limitation

**6c. `CompletenessReviewAgent`**
- **Model:** `claude-sonnet-4-6` with `thinking: {"type": "enabled", "budget_tokens": 3000}`
- **Focus:** Structural completeness — are all required sections present and all propagated flags surfaced?
- **Checklist:** (1) all mandatory sections present, (2) every `data_flag` from input `CrisisRecord` objects appears somewhere in limitations or caveats, (3) limitations list has ≥3 items, (4) `decision_support_note` present and unmodified, (5) no-HRP crises listed separately

### Agent 6d: `ReviewAggregatorAgent`
- **Model:** none — pure Python
- **Input:** three `ReviewResult` objects
- **Output:** single merged `AggregatedReview` — union of all `issues_found` across reviewers, deduplicated by location + description; overall `passed` is `True` only if all three reviewers pass
- **Logic:** `blocking` issues from any single reviewer block the note; `warning` issues are surfaced but do not block

### Orchestrator (no LLM)
```
QueryInterpreter → DataIngestor → GapScorer → ContextEnrichment (parallel) →
BriefingWriter → [6a, 6b, 6c in parallel] → ReviewAggregator →
    passed? → Final Output
    failed? → BriefingWriter (with merged issues, 1 retry max) →
              [6a, 6b, 6c in parallel] → ReviewAggregator →
              passed? → Final Output
              failed? → Final Output + issues appended to limitations
```
- Inserts mandatory `DECISION SUPPORT NOTICE` block as a Python string constant — not written by any LLM, not modifiable
- Caps review loop at 1 retry; on second failure, appends all `issues_found` to the limitations section with label "Automated review identified unresolved issues"
- Logs full pipeline run with timestamps, token usage per agent, per-reviewer pass/fail

---

## Filter and Keyword System

A **multi-dimensional facet selector** (not a free-text search box) in the Streamlit sidebar:

| Dimension | Type |
|---|---|
| Region / Subregion / Country | Multi-select (cascading) |
| Sector | Multi-select (OCHA taxonomy) |
| Crisis Type | Single-select |
| Minimum People in Need | Slider (0–50M+) |
| Max Coverage Ratio | Slider ("show crises funded below X%") |
| Year Range | Range slider |
| HRP Status | Multi-select (Active / Flash Appeal / No HRP / Unknown) |
| Structural Neglect Only | Toggle |

A natural-language text input sits above the panel. The `QueryInterpreterAgent` maps it to filter state and shows its interpretation visibly before running:

> "Interpreted as: Sector = Food Security; Subregion = Sahel (Chad, Mali, Niger, ...); Coverage < 30%. **Confidence: medium.** Note: 'Sahel' boundary is approximate. Edit filters to adjust."

Active filter state is serialized into the briefing note header for reproducibility.

---

## Confidence Propagation

A shared `Confidence` enum (HIGH / MEDIUM / LOW — no CERTAIN or VERY_HIGH) propagates through all agents:

- Stale HNO (>18 months) → `score_confidence: LOW` regardless of funding data quality
- Only pledged (not disbursed) funding available → `MEDIUM`
- All data current and complete → `HIGH`

The ranked table in the UI shows a **Confidence** column and a **Key Caveat** column — both non-optional. Null caveat renders as "No significant limitations identified."

---

## Tech Stack

| Component | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | HDX/OCHA datasets are CSV/Excel; pandas native |
| LLM SDK | `anthropic` (direct) | No LangChain; full control for auditability |
| Data models | `pydantic` v2 | Validated inter-agent handoffs; ValidationError on bad data |
| Data processing | `pandas`, `numpy` | Gap scoring, normalization |
| Async | `asyncio` | Parallel enrichment calls |
| UI | Streamlit | No frontend overhead; sidebar filters + dataframe + markdown native |
| Logging | `structlog` | Structured audit trail per pipeline run |
| Prompt caching | `cache_control: {"type": "ephemeral"}` on all system prompts | Stable long prompts — significant cost saving on repeated runs |

---

## Directory Structure

```
src/
  models/          # QuerySpec, CrisisRecord, BriefingNote, Confidence enum
  data/            # loaders.py, validators.py, normalizers.py, gap_scoring.py (no LLM)
  prompts/         # system prompts as Python strings (reviewable, versionable)
  orchestrator.py
agents/
  query_interpreter.py
  data_ingestor.py
  gap_scorer.py
  context_enrichment.py
  briefing_writer.py
  fact_check_review.py
  confidence_calibration_review.py
  completeness_review.py
  review_aggregator.py        # pure Python, merges three ReviewResults
app.py             # Streamlit entrypoint
data/              # raw CSVs (gitignored)
outputs/           # generated notes (gitignored)
tests/
  test_gap_scoring.py
  test_data_ingestor.py
  test_query_interpreter.py
  fixtures/        # small synthetic test datasets
requirements.txt
.env.example
METHODOLOGY.md
```

---

## Briefing Note Structure (enforced by orchestrator)

1. **Header:** query applied + filter state snapshot + data vintage notice
2. **Query interpretation note** (if confidence < HIGH)
3. **Executive summary** (LLM-written; must name most significant data limitation)
4. **Ranked crisis table** — columns: Rank, Country, PIN (est.), Coverage, Confidence, Key Caveat
5. **No-HRP crises list** (separate, not ranked against HRP crises)
6. **Top-3 crisis narratives** (LLM-written; each must cite source, year, confidence, and what the score doesn't capture)
7. **Methodology disclosure** (150 words, plain English)
8. **Known limitations** (minimum 3, enforced by `CompletenessReviewAgent`)
9. **Data sources** (structured list with declared limitations)
10. **DECISION SUPPORT NOTICE** (Python constant, inserted by orchestrator, not LLM)

---

## Build Sequence

**Phase 1 — Data foundation (no LLM, fully testable offline):**
`src/models/` → `src/data/loaders.py` → validators/normalizers → `agents/data_ingestor.py` → `src/data/gap_scoring.py` → `agents/gap_scorer.py` → `tests/`

**Phase 2 — LLM integration:**
`src/prompts/` (write all prompts first) → `agents/query_interpreter.py` → `agents/context_enrichment.py` → `agents/briefing_writer.py` → `agents/fact_check_review.py` + `agents/confidence_calibration_review.py` + `agents/completeness_review.py` → `agents/review_aggregator.py`

**Phase 3 — Orchestration and UI:**
`src/orchestrator.py` → `app.py` → `METHODOLOGY.md`

---

## Verification

1. Run `tests/test_gap_scoring.py` against synthetic fixtures — validate ranking correctness and confidence tier assignment before any API calls
2. Run `agents/data_ingestor.py` against real HDX CSV downloads — verify `data_flags` are generated correctly for stale/missing records
3. Run full pipeline in `--no-enrichment` mode (offline) — verify briefing note renders with graceful degradation
4. Run full pipeline with enrichment — verify `DECISION SUPPORT NOTICE` is present and unmodified in output
5. Manually review a generated note: confirm no bare percentages, all claims have source citations, limitations section has ≥3 items
