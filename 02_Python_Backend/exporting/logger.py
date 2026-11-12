import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd


def export_csv_and_json(
    results: List[Dict[str, Any]], output_dir: Path
) -> Dict[str, str]:
    """Saves screened equity results to timestamped and latest CSV/JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    latest_json_path = output_dir / "latest_screening_results.json"
    latest_csv_path = output_dir / "latest_screening_results.csv"
    archive_csv_path = output_dir / f"stratarisk_run_{timestamp}.csv"

    flat_rows = []
    for row in results:
        copy_row = dict(row)
        copy_row["risk_flags"] = ";".join(row.get("risk_flags", [])) or "NONE"
        flat_rows.append(copy_row)

    df = pd.DataFrame(flat_rows)
    df.to_csv(latest_csv_path, index=False, encoding="utf-8")
    df.to_csv(archive_csv_path, index=False, encoding="utf-8")

    payload = {
        "generated_at": datetime.now().isoformat(),
        "record_count": len(results),
        "results": results,
    }
    with open(latest_json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return {
        "latest_json": str(latest_json_path),
        "latest_csv": str(latest_csv_path),
        "archive_csv": str(archive_csv_path),
    }


def _build_svg_polyline(values: List[float], min_val: float, max_val: float, width: int, height: int, pad: int) -> str:
    """Converts a price series into normalized SVG polyline coordinates."""
    n = len(values)
    if n < 2:
        return ""
    span_x = width - (2 * pad)
    span_y = height - (2 * pad)
    val_range = (max_val - min_val) if (max_val - min_val) > 0 else 1.0

    points = []
    for i, val in enumerate(values):
        x = pad + (i / (n - 1)) * span_x
        y = pad + span_y - ((val - min_val) / val_range) * span_y
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def generate_html_trend_charts(
    raw_records: List[Dict[str, Any]], output_dir: Path
) -> str:
    """
    Generates a 100% self-contained HTML report with native SVG trend lines
    (Close Price, 50 EMA, 200 SMA) — requires zero external CDN/internet scripts.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    chart_path = output_dir / "stratarisk_trend_charts.html"

    width, height, pad = 980, 240, 32
    chart_blocks: List[str] = []

    for idx, rec in enumerate(raw_records):
        hist: pd.DataFrame | None = rec.get("history")
        if hist is None or hist.empty or "Close" not in hist.columns:
            continue

        symbol = rec.get("symbol", f"TICKER_{idx}")
        name = rec.get("name", symbol)
        close_s = hist["Close"].astype(float)
        ema_50 = close_s.ewm(span=50, adjust=False).mean()
        sma_200 = close_s.rolling(window=200, min_periods=1).mean()

        close_vals = close_s.tolist()
        ema_vals = ema_50.tolist()
        sma_vals = sma_200.tolist()

        all_vals = close_vals + ema_vals + sma_vals
        min_v, max_v = min(all_vals), max(all_vals)
        mid_v = (min_v + max_v) / 2.0

        start_date = hist.index[0].strftime("%Y-%m-%d")
        end_date = hist.index[-1].strftime("%Y-%m-%d")

        pts_close = _build_svg_polyline(close_vals, min_v, max_v, width, height, pad)
        pts_ema = _build_svg_polyline(ema_vals, min_v, max_v, width, height, pad)
        pts_sma = _build_svg_polyline(sma_vals, min_v, max_v, width, height, pad)

        chart_blocks.append(
            f"""
            <div class="card">
                <div class="card-header">
                    <h2>{symbol} — {name}</h2>
                    <div class="legend">
                        <span class="dot close"></span> Close (${close_vals[-1]:.2f})
                        <span class="dot ema"></span> 50 EMA (${ema_vals[-1]:.2f})
                        <span class="dot sma"></span> 200 SMA (${sma_vals[-1]:.2f})
                    </div>
                </div>
                <svg viewBox="0 0 {width} {height}" class="chart-svg">
                    <line x1="{pad}" y1="{pad}" x2="{width - pad}" y2="{pad}" stroke="#334155" stroke-dasharray="4"/>
                    <line x1="{pad}" y1="{height / 2:.1f}" x2="{width - pad}" y2="{height / 2:.1f}" stroke="#334155" stroke-dasharray="4"/>
                    <line x1="{pad}" y1="{height - pad}" x2="{width - pad}" y2="{height - pad}" stroke="#334155"/>

                    <text x="4" y="{pad + 4}" fill="#94a3b8" font-size="11">${max_v:.2f}</text>
                    <text x="4" y="{(height / 2) + 4:.1f}" fill="#94a3b8" font-size="11">${mid_v:.2f}</text>
                    <text x="4" y="{height - pad}" fill="#94a3b8" font-size="11">${min_v:.2f}</text>

                    <text x="{pad}" y="{height - 8}" fill="#94a3b8" font-size="11">{start_date}</text>
                    <text x="{width - pad - 65}" y="{height - 8}" fill="#94a3b8" font-size="11">{end_date}</text>

                    <polyline fill="none" stroke="#f43f5e" stroke-width="2" points="{pts_sma}"/>
                    <polyline fill="none" stroke="#f59e0b" stroke-width="2" points="{pts_ema}"/>
                    <polyline fill="none" stroke="#38bdf8" stroke-width="2.5" points="{pts_close}"/>
                </svg>
            </div>
            """
        )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>StrataRisk — Technical Trend Lines</title>
    <style>
        body {{ background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', sans-serif; margin: 24px; }}
        h1 {{ color: #38bdf8; margin-bottom: 6px; }}
        p.sub {{ color: #94a3b8; margin-top: 0; margin-bottom: 24px; }}
        .card {{ background: #1e293b; border-radius: 14px; padding: 20px; margin-bottom: 22px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
        .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 10px; }}
        .card h2 {{ margin: 0; font-size: 1.1rem; color: #e2e8f0; }}
        .legend {{ font-size: 0.85rem; color: #cbd5e1; display: flex; align-items: center; gap: 12px; }}
        .dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; }}
        .dot.close {{ background: #38bdf8; }}
        .dot.ema {{ background: #f59e0b; }}
        .dot.sma {{ background: #f43f5e; }}
        .chart-svg {{ width: 100%; height: auto; display: block; }}
    </style>
</head>
<body>
    <h1>StrataRisk Trend & Moving Average Analysis</h1>
    <p class="sub">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Self-Contained Offline Vector Report</p>
    {''.join(chart_blocks)}
</body>
</html>
"""
    with open(chart_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return str(chart_path)


def export_all_outputs(
    screened_results: List[Dict[str, Any]],
    raw_records: List[Dict[str, Any]],
    output_dir: Path,
) -> Dict[str, Any]:
    """Coordinates CSV/JSON data logging and HTML chart generation."""
    try:
        if not screened_results:
            raise ValueError("No screened results available to export.")

        file_paths = export_csv_and_json(screened_results, output_dir)
        html_chart_path = generate_html_trend_charts(raw_records, output_dir)
        file_paths["html_charts"] = html_chart_path

        return {
            "status": "SUCCESS",
            "module": "exporting.logger",
            "files": file_paths,
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "module": "exporting.logger",
            "message": str(exc),
            "files": {},
        }
