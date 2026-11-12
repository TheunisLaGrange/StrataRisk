import json
from pathlib import Path
from typing import Any, Dict, List
import yfinance as yf


def load_target_config(config_path: Path) -> Dict[str, Any]:
    """Loads watchlist and screening thresholds from target.json."""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file missing at: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "watchlist" not in data or not isinstance(data["watchlist"], list):
        raise ValueError("Invalid target.json: 'watchlist' list is missing or malformed.")

    return data


def fetch_single_ticker(symbol: str, period: str = "1y", interval: str = "1d") -> Dict[str, Any]:
    """Fetches historical prices and balance sheet fundamentals for a single ticker."""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval)

    if hist.empty:
        raise ValueError(f"No historical price data returned for '{symbol}'.")

    info = ticker.info or {}

    return {
        "symbol": symbol.upper(),
        "name": info.get("shortName", symbol.upper()),
        "sector": info.get("sector", "Unknown"),
        "industry": info.get("industry", "Unknown"),
        "current_price": float(hist["Close"].iloc[-1]),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        "market_cap": info.get("marketCap"),
        "trailing_pe": info.get("trailingPE"),
        "peg_ratio": info.get("pegRatio"),
        "roe": info.get("returnOnEquity"),
        "total_cash": info.get("totalCash"),
        "total_debt": info.get("totalDebt"),
        "free_cash_flow": info.get("freeCashflow"),
        "history": hist
    }


def fetch_all_market_data(config_path: Path) -> Dict[str, Any]:
    """
    Executes batch retrieval for all tickers in target.json.
    Returns a structured handshake payload with records and explicit error logs.
    """
    try:
        config = load_target_config(config_path)
    except Exception as exc:
        return {
            "status": "ERROR",
            "module": "data_import.fetcher",
            "message": str(exc),
            "records": [],
            "errors": [str(exc)]
        }

    watchlist: List[str] = config.get("watchlist", [])
    period: str = config.get("history_period", "1y")
    interval: str = config.get("history_interval", "1d")

    records: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    for symbol in watchlist:
        try:
            record = fetch_single_ticker(symbol, period=period, interval=interval)
            records.append(record)
        except Exception as exc:
            errors.append({"symbol": symbol, "error": str(exc)})

    status = "SUCCESS" if records else "ERROR"

    return {
        "status": status,
        "module": "data_import.fetcher",
        "config": config,
        "fetched_count": len(records),
        "failed_count": len(errors),
        "records": records,
        "errors": errors
    }


if __name__ == "__main__":
    # Standalone verification test
    base_dir = Path(__file__).resolve().parent.parent
    default_config = base_dir / "config" / "target.json"

    print(f"[INFO] Testing fetcher with config: {default_config}")
    result = fetch_all_market_data(default_config)

    print(f"[HANDSHAKE {result['status']}] Fetched: {result.get('fetched_count', 0)} | Failed: {result.get('failed_count', 0)}")
    if result.get("errors"):
        for err in result["errors"]:
            print(f"  [WARN] {err}")

    input("\n[Fetcher Test Concluded] Press Enter to exit...")
