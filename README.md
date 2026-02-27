# Tax Auction Project (Sacramento POC)

This repository now includes an implementation-focused POC for ingesting Sacramento County tax sale data.

## What is implemented
- Scrapes the Sacramento tax sale page (`TaxSale.aspx`).
- Discovers linked artifacts (PDF/CSV/XLS/XLSX/HTML links).
- Stores timestamped raw page snapshots and downloaded artifacts.
- Extracts listing candidates from HTML tables (best-effort APN + bid + address parsing).
- Persists snapshots, artifacts, listings, and listing lifecycle change events in SQLite.
- Emits listing lifecycle status:
  - `newly_listed`
  - `removed_since_last_snapshot`
  - `still_listed`

## Quickstart
```bash
PYTHONPATH=src python scripts/run_sacramento_snapshot.py
```

Optional flags:
```bash
python scripts/run_sacramento_snapshot.py \
  --db-path data/tax_auction.db \
  --artifact-root data/raw \
  --base-url https://finance.saccounty.gov/Tax/Pages/TaxSale.aspx
```

## Output
The script prints a JSON summary, for example:
```json
{
  "snapshot_id": 1,
  "artifacts_discovered": 42,
  "listings_extracted": 125,
  "change_events_emitted": 125
}
```

## Notes
- The HTML listing parser is intentionally generic; Sacramento-specific parsing rules can be added as the next step.
- Enrichment (flood, zoning, permits, valuation, WTP) is not yet implemented in code but can build on the stored APN snapshot history.
