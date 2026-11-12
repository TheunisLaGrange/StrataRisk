# StrataRisk

StrataRisk is a decoupled market-screening and risk-analysis platform featuring a standalone Python data engine and a C# WPF desktop interface. The two subsystems operate independently and communicate strictly through a local CSV and JSON file bridge.

## Standalone Download (No Python or .NET Required)

1. Download **`StrataRisk-v1.0.0-win-x64.zip`** from the **[Releases](https://github.com)** page.
2. Extract the archive to any folder on Windows (x64).
3. Double-click **`GUI_App\StrataRisk.GUI.exe`** to launch the desktop interface.
4. Click **Run Scan**—the GUI automatically invokes **`Backend_Engine\StrataRisk.Engine.exe`** and reads results via **`Shared_Data\output\latest_screening_results.csv`**.

## Architecture Overview

* **`01_Automation_Scripts/`**: PowerShell build automation (`build_release.ps1`) that compiles the Python engine via Nuitka and publishes the C# GUI as standalone executables.
* **`02_Python_Backend/`**: Modular Python screening pipeline (`data_import`, `processing`, `exporting`, `diagnostics`) that fetches market data, evaluates risk thresholds, and exports CSV, JSON, SQLite, and HTML trend reports.
* **`03_CSharp_GUI/`**: .NET 10 Windows desktop application (`StrataRisk.GUI`) that triggers the backend via `PythonBridgeService` and visualizes screening results.

## Quick Start

### 1. Python Backend Setup
```bash
cd 02_Python_Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run a Screening Pass (CLI)
```bash
python main.py --config config/target.json --output data/output
```

### 3. Build Decoupled Standalone Release
Run the release builder from `01_Automation_Scripts/` to generate `Release_Build/` containing `Backend_Engine/`, `GUI_App/`, and `Shared_Data/`:
```powershell
powershell -ExecutionPolicy Bypass -File .\01_Automation_Scripts\build_release.ps1
```
