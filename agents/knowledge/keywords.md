# Keyword Reference for Query Interpretation

These are the concepts the QueryInterpreterAgent must recognize and extract from a natural language query. Each entry describes what natural language expressions map to a structured filter field in `QuerySpec`.

---

## Geographic Scope
**Description:** Terms identifying a geographic area of interest — a UN region, a commonly-used subregion, a country name, or an ISO3 code. Subregions are informal and must be resolved to a list of country ISO3 codes with a note that the boundary is approximate.

**Examples a user might write:**
- "in Sub-Saharan Africa", "across Africa", "in the Middle East and North Africa", "in Asia"
- "in the Sahel", "in the Horn of Africa", "in the Great Lakes region", "across Southeast Asia"
- "in Sudan", "in DRC", "in Yemen", "in Haiti", "in SDN" (ISO3)
- "globally", "worldwide" (no geographic filter applied)

**Resolution note:** If a subregion term is ambiguous (e.g. "the Sahel" has no agreed boundary), list the countries assumed and flag `interpretation_confidence: "medium"`.

---

## Humanitarian Sector
**Description:** Terms identifying one or more humanitarian sectors from the OCHA/HNO taxonomy. Maps to sector-level filtering of HNO and HRP data.

**Examples a user might write:**
- "food crises", "food insecurity", "hunger", "acute malnutrition" → Food Security
- "health emergencies", "disease outbreaks", "medical needs" → Health
- "shelter gaps", "housing needs", "displacement shelter" → Shelter
- "water and sanitation", "WASH", "clean water access" → WASH
- "protection concerns", "gender-based violence", "GBV", "child protection" → Protection
- "education gaps", "schools destroyed", "out-of-school children" → Education
- "malnutrition", "wasting", "stunting", "nutrition crisis" → Nutrition
- No sector term present → no sector filter applied (all sectors included)

---

## Crisis Type
**Description:** Terms identifying the nature or cause of the humanitarian crisis.

**Examples a user might write:**
- "conflict", "war", "armed conflict", "fighting", "insecurity" → Conflict
- "earthquake", "flood", "cyclone", "drought", "natural disaster" → Natural Disaster
- "displacement", "refugees", "IDPs", "forced displacement" → Displacement
- "mixed crisis", "complex emergency" → Mixed
- No crisis type term present → no type filter applied

---

## Scale of Need (People in Need floor)
**Description:** Terms expressing a minimum threshold of documented humanitarian need — sets `min_people_in_need` in `QuerySpec`. If no figure is given, infer a reasonable threshold from qualitative terms.

**Examples a user might write:**
- "large-scale crises", "major emergencies", "significant need" → infer ≥500,000 PIN
- "massive crises", "the worst situations" → infer ≥1,000,000 PIN
- "affecting more than 2 million people", "over 500,000 in need" → extract number directly
- "all crises" or no scale term → no minimum PIN filter

---

## Funding Gap Severity (coverage ratio ceiling)
**Description:** Terms expressing how underfunded the crisis must be — sets `max_coverage_ratio` in `QuerySpec`. Maps to the ratio of funded amount to requested/targeted amount.

**Examples a user might write:**
- "underfunded", "poorly funded", "funding gaps" → infer ≤40% coverage
- "severely underfunded", "critical funding gap", "almost no funding" → infer ≤15% coverage
- "less than 20% funded", "below 30% coverage", "funded under 10%" → extract percentage directly
- "the most overlooked", "most neglected" → infer ≤25% coverage
- No gap term present → no coverage ceiling applied

---

## Time Period
**Description:** Terms anchoring the analysis to a specific year or range — sets `year_range` in `QuerySpec`. Relative terms must be resolved to absolute years using the current date (2026-04-18).

**Examples a user might write:**
- "in 2024", "for 2023" → single year
- "over the past three years", "since 2022", "from 2021 to 2024" → year range
- "recent", "current", "latest" → most recent available year in dataset
- "historically", "over time", "multi-year" → broadest available range
- No time term present → default to most recent available data

---

## HRP Status
**Description:** Terms referencing whether a formal Humanitarian Response Plan, Flash Appeal, or no plan is in place for a crisis.

**Examples a user might write:**
- "with active response plans", "HRP countries", "with formal HRPs" → Active HRP only
- "with flash appeals", "emergency appeals" → Flash Appeal only
- "without response plans", "no HRP", "off the radar", "unplanned crises" → No HRP
- No HRP term present → all statuses included

---

## Structural / Chronic Neglect
**Description:** Terms expressing interest in crises that have been underfunded consistently over multiple years, not just at a single point in time — sets `structural_neglect_only: true` in `QuerySpec`.

**Examples a user might write:**
- "chronically neglected", "consistently underfunded", "forgotten crises"
- "structurally overlooked", "long-term funding gaps", "year after year"
- "not just recently", "historically underfunded", "persistent gaps"
- No such term present → structural neglect filter not applied (all crises included)
