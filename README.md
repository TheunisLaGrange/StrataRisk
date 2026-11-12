# 🛡️ StrataRisk

StrataRisk is a market-screening and financial risk-analysis platform featuring a Python backend engine and a .NET C# WPF desktop interface.

## 📦 Standalone Download (No Python or .NET Required)

Download the release archive from the project's [Releases](https://github.com) page to run the Windows GUI and execute backend screenings.

## ⚙️ Architecture Overview

* **`01_Automation_Scripts/`**: PowerShell scripts for compiling the backend and packaging the GUI.
* **`02_Python_Backend/`**: Python pipeline handling data import, risk processing, and exports.
* **`03_CSharp_GUI/`**: .NET desktop application interfacing with the backend via local files.

## 🚀 Quick Start

* **Python Setup**: Initialize the virtual environment and install dependencies in `02_Python_Backend`.
* **CLI Screening**: Execute `main.py` with your target configuration and output paths.
* **Build Release**: Run the PowerShell automation script in `01_Automation_Scripts` to package the standalone application.

## 📄 License

Licensed under the MIT License. See `LICENSE` for details.
