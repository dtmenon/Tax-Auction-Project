# Sacramento County Tax Sale Intelligence System Plan (Proof of Concept)

## 1) Objective
Build a proof-of-concept (POC) platform that continuously gathers and analyzes tax-sale opportunities for Sacramento County, starting from the official county tax sale page:

- https://finance.saccounty.gov/Tax/Pages/TaxSale.aspx

The system should:
1. Track auction inventory over time (new listings, removed listings, sold/withdrawn indicators).
2. Enrich each parcel with external risk/cost data (flood, zoning, permits, liens, etc.).
3. Estimate all-in acquisition cost and expected upside.
4. Generate a data-driven “maximum willingness to pay” (WTP) recommendation per property.
5. Be designed so additional counties can be plugged in later.

---

## 2) Scope and assumptions (POC)
### In-scope (Sacramento only)
- Scrape and monitor county sale page plus linked documents.
- Parse listed properties and maintain daily snapshots.
- Detect listing lifecycle changes:
  - `newly_listed`
  - `still_listed`
  - `removed_since_last_snapshot`
- Enrich parcel with core risk/cost signals from public data sources.
- Produce a scoring + WTP model and ranked candidate list.
- Expose results via API and basic dashboard.

### Out-of-scope (for first iteration)
- Fully automated bidding execution.
- Title report procurement automation from paid providers.
- Nationwide expansion implementation (design for it, implement later).

### Key assumptions
- Public pages/documents can be accessed programmatically under site terms and robots policies.
- Parcel identifiers (APN) are available directly or inferable via documents.
- Some high-value data (e.g., detailed liens/title defects) may initially require manual review flags.

---

## 3) High-level architecture
Use a modular pipeline so county-specific logic is isolated.

1. **Source adapters (county plugin layer)**
   - `SacramentoAdapter` for website + document parsing.
   - Future adapters: `CountyXAdapter`, `CountyYAdapter`.

2. **Ingestion + snapshot service**
   - Scheduled crawler (daily + pre-auction burst cadence).
   - Raw artifact storage (HTML/PDF/CSV files) with timestamping.
   - Structured extraction to normalized property records.

3. **Change detection service**
   - Compares current snapshot vs previous.
   - Emits property status events (new, removed, updated).

4. **Enrichment service**
   - APN geocoding and parcel normalization.
   - Flood zone, zoning/land use, permit history, assessed value, sale comps, neighborhood indicators.

5. **Underwriting engine**
   - Cost stack computation (tax debt, penalties, cleanup, rehab assumptions, holding costs).
   - Exit value estimation (ARV / resale / rental valuation).
   - WTP output under configurable target returns.

6. **Storage + API + dashboard**
   - Relational DB for entities and history.
   - API for querying deals and risk factors.
   - Dashboard for analysts: watchlist, alerts, and downloadable reports.

---

## 4) Data model (core entities)
### `county`
- `id`, `name`, `state`, `timezone`

### `auction_event`
- `id`, `county_id`, `event_name`, `auction_date_start`, `auction_date_end`, `source_url`

### `auction_snapshot`
- `id`, `auction_event_id`, `captured_at`, `raw_artifact_path`, `hash`

### `property_listing`
- `id`, `snapshot_id`, `apn`, `situs_address`, `city`, `state`, `zip`, `minimum_bid`, `status`

### `listing_change_event`
- `id`, `apn`, `change_type`, `previous_snapshot_id`, `current_snapshot_id`, `detected_at`

### `property_enrichment`
- `id`, `apn`, `lat`, `lng`, `flood_zone`, `zoning_code`, `permit_count_5y`, `assessed_value`, `last_sale_price`, `hoa_flag`, `environmental_flag`, `enriched_at`

### `underwriting_result`
- `id`, `apn`, `total_known_debt`, `estimated_rehab_cost`, `holding_cost_estimate`, `exit_value_estimate`, `target_margin_pct`, `max_wtp`, `confidence_score`, `generated_at`

---

## 5) Scraping + document discovery workflow
1. Crawl base page `TaxSale.aspx` and identify links to:
   - property lists (HTML tables, CSV, Excel, PDF),
   - notices and terms,
   - schedule updates and cancellation/withdrawal notices.
2. Download all linked artifacts and store immutable copies.
3. Parse each artifact with format-specific extractors:
   - HTML parser,
   - PDF table extraction,
   - CSV/XLSX ingestion.
4. Normalize fields (APN formatting, addresses, bid values).
5. Run deduplication and identity resolution by APN + address similarity.
6. Save snapshot and emit lifecycle diffs against prior snapshot.

---

## 6) Property risk and cost evaluation framework
For each APN, evaluate categories that impact acquisition decision:

1. **Debt & obligations**
   - Delinquent taxes/penalties listed.
   - Potential senior liens or municipal obligations (flag unknowns).

2. **Physical & regulatory risk**
   - Flood zone/FEMA risk tier.
   - Zoning and allowable use conflicts.
   - Open/closed permits and code violations.
   - Environmental hazard overlays where available.

3. **Marketability & valuation**
   - Neighborhood comps (recent sales).
   - Liquidity indicators (days on market in area).
   - Rent potential (if hold strategy).

4. **Cost stack modeling**
   - Acquisition (bid + fees).
   - Carrying costs (interest, insurance, taxes during hold).
   - Rehab/cleanup assumptions by property type/condition proxies.
   - Disposition costs (broker, closing).

5. **WTP computation**
   - `max_wtp = conservative_exit_value - total_costs - required_profit_buffer`
   - Produce scenario bands: base / downside / severe downside.

---

## 7) Suggested tech stack
- **Scraping/orchestration**: Python + Playwright/Requests + BeautifulSoup + pdfplumber/tabula.
- **Workflow scheduler**: Prefect or Airflow (start with cron + simple worker for POC).
- **Storage**:
  - PostgreSQL (normalized entities + event history),
  - Object storage (S3-compatible) for raw artifacts.
- **API**: FastAPI.
- **UI**: Lightweight React or internal Streamlit dashboard for POC.
- **Analytics/modeling**: Python notebooks + feature pipelines; later move to production service.

---

## 8) Expansion-ready county plugin strategy
Define a county adapter interface:

- `discover_sources()`
- `fetch_artifacts()`
- `extract_listings()`
- `extract_auction_metadata()`
- `normalize_fields()`

Only adapter-specific parsing should vary by county; downstream enrichment, underwriting, and reporting remain shared.

---

## 9) 6-phase implementation roadmap
### Phase 0 (Week 1): Foundation
- Repo scaffolding, DB schema, artifact store, config management.
- Sacramento adapter skeleton + one successful crawl.

### Phase 1 (Weeks 1–2): Reliable listing ingestion
- Daily snapshot job and parser for primary listing source.
- Change detection for newly listed/removed properties.
- Basic QA checks and alerting.

### Phase 2 (Weeks 2–4): Enrichment MVP
- APN normalization and geocoding.
- Flood + zoning + permit endpoints integrated.
- Confidence flags for missing/ambiguous data.

### Phase 3 (Weeks 4–5): Underwriting + WTP
- Deterministic cost model and configurable assumptions.
- WTP output with scenario analysis.
- Ranked opportunity list.

### Phase 4 (Weeks 5–6): Analyst dashboard
- Search/filter by risk and expected margin.
- Property detail page with provenance to source artifacts.
- Export CSV/report.

### Phase 5 (Week 7+): Hardening + next county
- Monitoring, retries, parser drift detection.
- Introduce second county adapter to validate reusability.

---

## 10) Success metrics (POC)
1. **Coverage**: ≥95% of listed parcels captured from county source artifacts.
2. **Timeliness**: snapshot-to-dashboard latency <2 hours.
3. **Change detection quality**: precision/recall >90% for listed vs removed transitions.
4. **Underwriting usefulness**: analyst acceptance on top-ranked opportunities (qualitative + backtest).
5. **Scalability readiness**: onboard a second county in <2 weeks with adapter-only changes.

---

## 11) Key risks and mitigations
- **Parser breakage from website changes**
  - Mitigation: raw artifact versioning + parser tests + schema drift alerts.
- **Incomplete lien/title visibility**
  - Mitigation: explicit “manual review required” risk gates before bid recommendation.
- **Data quality mismatch across sources**
  - Mitigation: confidence scoring and provenance tracking per field.
- **Legal/compliance constraints**
  - Mitigation: review robots/ToS and keep request rate polite and auditable.

---

## 12) Immediate next steps (actionable)
1. Build Sacramento source inventory (all URLs, file types, update cadence).
2. Implement first crawler that captures and stores raw artifacts daily.
3. Implement parser for parcel list and APN normalization.
4. Ship first change-detection report: new vs removed listings.
5. Add 2–3 enrichment signals (flood, zoning, permits).
6. Produce first-pass WTP calculator with conservative assumptions.
7. Review 20 historical properties manually to calibrate model assumptions.
