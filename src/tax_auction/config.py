from pathlib import Path

BASE_URL = "https://finance.saccounty.gov/Tax/Pages/TaxSale.aspx"
DEFAULT_DB_PATH = Path("data/tax_auction.db")
DEFAULT_ARTIFACT_ROOT = Path("data/raw")
USER_AGENT = "TaxAuctionPOC/0.1 (+https://example.local)"
REQUEST_TIMEOUT_SECONDS = 30
