from typing import Any


def fetch_stock_listing(market: str) -> list[dict[str, Any]]:
    import os

    import certifi

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

    import FinanceDataReader as fdr

    frame = fdr.StockListing(market)
    return frame.to_dict(orient="records")
