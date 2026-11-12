using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Windows;
using StrataRisk.GUI.Models;
using StrataRisk.GUI.Services;

namespace StrataRisk.GUI
{
    public partial class MainWindow : Window
    {
        private readonly PythonBridgeService _bridgeService;
        private string? _latestHtmlChartPath;

        public MainWindow()
        {
            InitializeComponent();

            string baseDir = AppContext.BaseDirectory;
            string releaseRoot = Path.GetFullPath(Path.Combine(baseDir, ".."));

            // 1. Check decoupled Release_Build layout (GUI_App\ -> ..\Backend_Engine\ & ..\Shared_Data\)
            string releaseEngine = Path.Combine(releaseRoot, "Backend_Engine", "StrataRisk.Engine.exe");
            string releaseSharedData = Path.Combine(releaseRoot, "Shared_Data");

            string compiledEngine;
            string configPath;
            string outputDir;

            if (File.Exists(releaseEngine) && Directory.Exists(releaseSharedData))
            {
                compiledEngine = releaseEngine;
                configPath = Path.Combine(releaseSharedData, "config", "target.json");
                outputDir = Path.Combine(releaseSharedData, "output");
            }
            else
            {
                // 2. Development fallback when running inside 03_CSharp_GUI
                string devRoot = @"C:\PC Programming\Python\src\AI\Agent\02_Python_Source\StrataRisk\02_Python_Backend";
                compiledEngine = Path.Combine(baseDir, "StrataRisk.Engine", "StrataRisk.Engine.exe");
                configPath = Path.Combine(devRoot, "config", "target.json");
                outputDir = Path.Combine(devRoot, "data", "output");
            }

            string pythonExe = @"C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe";
            string scriptPath = @"C:\PC Programming\Python\src\AI\Agent\02_Python_Source\StrataRisk\02_Python_Backend\main.py";

            _bridgeService = new PythonBridgeService(
                compiledEngine,
                pythonExe,
                scriptPath,
                configPath,
                outputDir);
        }


        private async void BtnRunScan_Click(object sender, RoutedEventArgs e)
        {
            BtnRunScan.IsEnabled = false;
            BtnOpenCharts.IsEnabled = false;
            TxtStatus.Text = "[RUNNING] Invoking StrataRisk screening engine... Please wait.";

            try
            {
                var (handshake, payload) = await _bridgeService.ExecuteScreenerAsync();

                if (handshake.Status != "SUCCESS" || payload == null)
                {
                    TxtStatus.Text = $"[ERROR] Stage '{handshake.Stage}': {handshake.Message}";
                    MessageBox.Show(handshake.Message, "StrataRisk Pipeline Error", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }

                GridResults.ItemsSource = payload.Results;
                TxtTotalScreened.Text = payload.RecordCount.ToString();
                TxtDefensiveCount.Text = payload.Results.Count(r => r.RiskTier == "DEFENSIVE").ToString();
                TxtLastRun.Text = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

                _latestHtmlChartPath = handshake.Files?.HtmlCharts;
                BtnOpenCharts.IsEnabled = !string.IsNullOrWhiteSpace(_latestHtmlChartPath) && File.Exists(_latestHtmlChartPath);

                TxtStatus.Text = $"[HANDSHAKE OK] {handshake.Message}";
            }
            catch (Exception ex)
            {
                TxtStatus.Text = $"[CRITICAL ERROR] {ex.Message}";
                MessageBox.Show(ex.Message, "Execution Failure", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                BtnRunScan.IsEnabled = true;
            }
        }

        private void BtnOpenCharts_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(_latestHtmlChartPath) || !File.Exists(_latestHtmlChartPath))
            {
                MessageBox.Show("HTML chart file was not found.", "Missing File", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            Process.Start(new ProcessStartInfo
            {
                FileName = _latestHtmlChartPath,
                UseShellExecute = true
            });
        }
    }
}
