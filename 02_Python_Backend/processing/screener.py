from typing import Any, Dict, List
import numpy as np
import pandas as pd


def calculate_technical_indicators(history: pd.DataFrame | None) -> Dict[str, Any]:
    """Computes 50-day EMA, 200-day SMA, and trend alignment from price history."""
    if history is None or history.empty or "Close" not in history.columns:
        raise ValueError("Historical DataFrame is missing 'Close' prices.")

    close_series = history["Close"].astype(float)
    current_price = float(close_series.iloc[-1])

    ema_50 = float(close_series.ewm(span=50, adjust=False).mean().iloc[-1])
    sma_200 = (
        float(close_series.rolling(window=200).mean().iloc[-1])
        if len(close_series) >= 200
        else float(close_series.mean())
    )

    above_ema_50 = current_price > ema_50
    above_sma_200 = current_price > sma_200
    golden_alignment = above_ema_50 and (ema_50 > sma_200)

    if golden_alignment:
        trend_signal = "BULLISH"
    elif above_sma_200:
        trend_signal = "NEUTRAL_UP"
    else:
        trend_signal = "BEARISH"

    return {
        "ema_50": round(ema_50, 2),
        "sma_200": round(sma_200, 2),
        "above_ema_50": above_ema_50,
        "above_sma_200": above_sma_200,
        "trend_signal": trend_signal,
    }


def calculate_balance_sheet_metrics(record: Dict[str, Any]) -> Dict[str, Any]:
    """Computes Net Cash, Cash-to-Debt ratio, and Free Cash Flow Yield."""
    cash = record.get("total_cash")
    debt = record.get("total_debt")
    fcf = record.get("free_cash_flow")
    market_cap = record.get("market_cap")

    safe_cash = float(cash) if cash is not None else 0.0
    safe_debt = float(debt) if debt is not None else 0.0
    net_cash = safe_cash - safe_debt

    if safe_debt > 0:
        cash_to_debt = round(safe_cash / safe_debt, 2)
    elif safe_cash > 0:
        cash_to_debt = 99.99  # Effectively debt-free with positive cash
    else:
        cash_to_debt = 0.0

    if fcf is not None and market_cap and market_cap > 0:
        fcf_yield = round(float(fcf) / float(market_cap), 4)
    else:
        fcf_yield = None

    return {
        "total_cash": safe_cash,
        "total_debt": safe_debt,
        "net_cash": net_cash,
        "cash_to_debt": cash_to_debt,
        "free_cash_flow": float(fcf) if fcf is not None else None,
        "fcf_yield": fcf_yield,
        "fcf_yield_pct": round(fcf_yield * 100, 2) if fcf_yield is not None else None,
    }


def compute_stress_test(
    bs_metrics: Dict[str, Any],
    tech_metrics: Dict[str, Any],
    record: Dict[str, Any],
    thresholds: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Scores balance sheet & liquidity resilience (0-100) and flags liquidity risks.
    """
    score = 0
    flags: List[str] = []

    cash_to_debt = bs_metrics["cash_to_debt"]
    fcf_yield = bs_metrics["fcf_yield"]
    net_cash = bs_metrics["net_cash"]
    roe = record.get("roe")
    trailing_pe = record.get("trailing_pe")

    min_c2d = float(thresholds.get("min_cash_to_debt", 0.50))
    min_fcf = float(thresholds.get("min_fcf_yield", 0.02))
    min_roe = float(thresholds.get("min_roe", 0.12))
    max_pe = float(thresholds.get("max_trailing_pe", 35.0))

    # 1. Solvency / Cash-to-Debt Buffer (35 pts)
    if cash_to_debt >= 1.0:
        score += 35
    elif cash_to_debt >= min_c2d:
        score += 20
    else:
        flags.append("LOW_CASH_TO_DEBT")

    # 2. Free Cash Flow Generation (25 pts)
    if fcf_yield is not None and fcf_yield >= min_fcf:
        score += 25
    elif fcf_yield is not None and fcf_yield > 0:
        score += 12
    else:
        flags.append("WEAK_OR_NEGATIVE_FCF")

    # 3. Net Cash Cushion (15 pts)
    if net_cash > 0:
        score += 15

    # 4. Capital Efficiency / ROE (15 pts)
    if roe is not None and float(roe) >= min_roe:
        score += 15
    elif roe is None or float(roe) <= 0:
        flags.append("LOW_ROE")

    # 5. Valuation & Trend Discipline (10 pts)
    if trailing_pe is not None and 0 < float(trailing_pe) <= max_pe:
        score += 5
    if tech_metrics["above_sma_200"]:
        score += 5

    # Risk Classification
    if score >= 75 and "LOW_CASH_TO_DEBT" not in flags:
        risk_tier = "DEFENSIVE"
    elif score >= 45:
        risk_tier = "MODERATE"
    else:
        risk_tier = "HIGH_RISK"

    passed_screen = (
        risk_tier != "HIGH_RISK"
        and (trailing_pe is None or float(trailing_pe) <= max_pe)
    )

    return {
        "stress_score": score,
        "risk_tier": risk_tier,
        "passed_screen": passed_screen,
        "risk_flags": flags,
    }


def screen_all_records(
    records: List[Dict[str, Any]], thresholds: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Processes all fetched ticker records, ranks by Cash-to-Debt and Stress Score,
    and returns a structured handshake dictionary.
    """
    processed: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    for rec in records:
        symbol = rec.get("symbol", "UNKNOWN")
        try:
            tech = calculate_technical_indicators(rec.get("history"))
            bs = calculate_balance_sheet_metrics(rec)
            stress = compute_stress_test(bs, tech, rec, thresholds)

            # Build serializable summary record (excluding raw DataFrame)
            clean_record = {
                "symbol": symbol,
                "name": rec.get("name", symbol),
                "sector": rec.get("sector", "Unknown"),
                "current_price": round(float(rec["current_price"]), 2),
                "trailing_pe": round(float(rec["trailing_pe"]), 2)
                if rec.get("trailing_pe") is not None
                else None,
                "peg_ratio": round(float(rec["peg_ratio"]), 2)
                if rec.get("peg_ratio") is not None
                else None,
                "roe_pct": round(float(rec["roe"]) * 100, 2)
                if rec.get("roe") is not None
                else None,
                "ema_50": tech["ema_50"],
                "sma_200": tech["sma_200"],
                "trend_signal": tech["trend_signal"],
                "cash_to_debt": bs["cash_to_debt"],
                "net_cash": bs["net_cash"],
                "fcf_yield_pct": bs["fcf_yield_pct"],
                "stress_score": stress["stress_score"],
                "risk_tier": stress["risk_tier"],
                "passed_screen": stress["passed_screen"],
                "risk_flags": stress["risk_flags"],
            }
            processed.append(clean_record)
        except Exception as exc:
            errors.append({"symbol": symbol, "error": str(exc)})

    # Rank highest balance sheet health and stress score first
    processed.sort(
        key=lambda x: (x["stress_score"], x["cash_to_debt"]), reverse=True
    )

    status = "SUCCESS" if processed else "ERROR"

    return {
        "status": status,
        "module": "processing.screener",
        "processed_count": len(processed),
        "failed_count": len(errors),
        "results": processed,
        "errors": errors,
    }


if __name__ == "__main__":
    # Standalone synthetic test so screener.py can be verified independently
    dates = pd.date_range(end=pd.Timestamp.today(), periods=220, freq="B")
    synthetic_prices = np.linspace(120, 165, 220)
    mock_hist = pd.DataFrame({"Close": synthetic_prices}, index=dates)

    mock_records = [
        {
            "symbol": "TEST_STRONG",
            "name": "Strong Balance Sheet Corp",
            "sector": "Technology",
            "current_price": 165.0,
            "trailing_pe": 22.5,
            "peg_ratio": 1.4,
            "roe": 0.24,
            "total_cash": 50_000_000_000,
            "total_debt": 15_000_000_000,
            "free_cash_flow": 18_000_000_000,
            "market_cap": 400_000_000_000,
            "history": mock_hist,
        },
        {
            "symbol": "TEST_WEAK",
            "name": "Leveraged Liquidity Inc",
            "sector": "Industrials",
            "current_price": 165.0,
            "trailing_pe": 42.0,
            "peg_ratio": 2.8,
            "roe": 0.06,
            "total_cash": 1_000_000_000,
            "total_debt": 12_000_000_000,
            "free_cash_flow": -500_000_000,
            "market_cap": 30_000_000_000,
            "history": mock_hist,
        },
    ]

    sample_thresholds = {
        "max_trailing_pe": 35.0,
        "min_roe": 0.12,
        "min_cash_to_debt": 0.50,
        "min_fcf_yield": 0.02,
    }

    output = screen_all_records(mock_records, sample_thresholds)
    print(f"[HANDSHAKE {output['status']}] Screened: {output['processed_count']} records")
    for item in output["results"]:
        print(
            f"  -> {item['symbol']}: Score={item['stress_score']} | "
            f"Tier={item['risk_tier']} | C2D={item['cash_to_debt']} | Flags={item['risk_flags']}"
        )

    input("\n[Screener Test Concluded] Press Enter to exit...")
