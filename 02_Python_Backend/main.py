import sys
from pathlib import Path
import argparse
import json
import sys
from pathlib import Path

from data_import.fetcher import fetch_all_market_data
from exporting.logger import export_all_outputs
from processing.screener import screen_all_records

from exporting.db_exporter import export_sqlite_db

def emit_handshake(payload: dict, json_only: bool) -> None:
    """Outputs final structured handshake for C# stdout parsing or console view."""
    if json_only:
        print(json.dumps(payload))
    else:
        print(f"\n[HANDSHAKE {payload['status']}] {payload.get('message', '')}")
        print(json.dumps(payload, indent=2))


def run_pipeline(config_path: Path, output_dir: Path) -> dict:
    """Executes fetch -> screen -> export pipeline with explicit stage checks."""
    # Stage 1: Import
    fetch_res = fetch_all_market_data(config_path)
    if fetch_res["status"] != "SUCCESS":
        return {
            "status": "ERROR",
            "stage": "data_import",
            "message": fetch_res.get("message", "Failed to fetch market data."),
            "errors": fetch_res.get("errors", []),
        }

    # Stage 2: Process
    thresholds = fetch_res["config"].get("thresholds", {})
    screen_res = screen_all_records(fetch_res["records"], thresholds)
    if screen_res["status"] != "SUCCESS":
        return {
            "status": "ERROR",
            "stage": "processing",
            "message": "Screening failed for all fetched records.",
            "errors": screen_res.get("errors", []),
        }

    # Stage 3: Export
    export_res = export_all_outputs(
        screen_res["results"], fetch_res["records"], output_dir
    )
    if export_res["status"] != "SUCCESS":
        return {
            "status": "ERROR",
            "stage": "exporting",
            "message": export_res.get("message", "Failed to export results."),
        }

    db_path = export_sqlite_db(screen_res["results"], output_dir)
    export_res["files"]["sqlite_db"] = db_path

    return {
        "status": "SUCCESS",
        "message": f"Screened {screen_res['processed_count']} tickers successfully.",
        "processed_count": screen_res["processed_count"],
        "failed_count": fetch_res["failed_count"] + screen_res["failed_count"],
        "files": export_res["files"],
        "warnings": fetch_res.get("errors", []) + screen_res.get("errors", []),
    }


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="StrataRisk Screening Pipeline")
    parser.add_argument(
        "--config",
        type=Path,
        default=base_dir / "config" / "target.json",
        help="Path to target.json configuration file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=base_dir / "data" / "output",
        help="Directory for exported JSON, CSV, and HTML files",
    )
    parser.add_argument(
        "--json-handshake",
        action="store_true",
        help="Emit single-line JSON handshake for C# GUI integration",
    )
    args = parser.parse_args()

    result = run_pipeline(args.config, args.output)
    emit_handshake(result, args.json_handshake)

    if result["status"] != "SUCCESS":
        sys.exit(1)

    if not args.json_handshake:
        input("\n[StrataRisk Pipeline Concluded] Press Enter to exit...")


if __name__ == "__main__":
    main()
