using System;
using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using StrataRisk.GUI.Models;

namespace StrataRisk.GUI.Services
{
    public class PythonBridgeService
    {
        private readonly string _engineExePath;
        private readonly string _fallbackPythonExe;
        private readonly string _fallbackScriptPath;
        private readonly string _configPath;
        private readonly string _outputDir;

        public PythonBridgeService(
            string engineExePath,
            string fallbackPythonExe,
            string fallbackScriptPath,
            string configPath,
            string outputDir)
        {
            _engineExePath = engineExePath;
            _fallbackPythonExe = fallbackPythonExe;
            _fallbackScriptPath = fallbackScriptPath;
            _configPath = configPath;
            _outputDir = outputDir;
        }

        public async Task<(HandshakeResponse Handshake, ScreeningPayload? Payload)> ExecuteScreenerAsync()
        {
            bool useCompiledEngine = File.Exists(_engineExePath);
            string fileName;
            string arguments;
            string workingDir;

            if (useCompiledEngine)
            {
                fileName = _engineExePath;
                arguments = $"--config \"{_configPath}\" --output \"{_outputDir}\" --json-handshake";
                workingDir = Path.GetDirectoryName(_engineExePath)!;
            }
            else
            {
                if (!File.Exists(_fallbackPythonExe))
                    throw new FileNotFoundException($"Neither compiled engine nor Python interpreter was found.");
                if (!File.Exists(_fallbackScriptPath))
                    throw new FileNotFoundException($"Backend script not found at: {_fallbackScriptPath}");

                fileName = _fallbackPythonExe;
                arguments = $"\"{_fallbackScriptPath}\" --config \"{_configPath}\" --output \"{_outputDir}\" --json-handshake";
                workingDir = Path.GetDirectoryName(_fallbackScriptPath)!;
            }

            var startInfo = new ProcessStartInfo
            {
                FileName = fileName,
                Arguments = arguments,
                WorkingDirectory = workingDir,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = new Process { StartInfo = startInfo };
            process.Start();

            string stdout = await process.StandardOutput.ReadToEndAsync();
            string stderr = await process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();

            if (string.IsNullOrWhiteSpace(stdout))
            {
                throw new InvalidOperationException(
                    $"Engine process exited (Code {process.ExitCode}) with no handshake output.\nSTDERR: {stderr}");
            }

            var lines = stdout.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
            string jsonLine = lines[^1];

            var handshake = JsonSerializer.Deserialize<HandshakeResponse>(jsonLine)
                ?? throw new InvalidOperationException("Failed to deserialize engine JSON handshake.");

            if (handshake.Status != "SUCCESS" || handshake.Files == null)
            {
                return (handshake, null);
            }

            if (!File.Exists(handshake.Files.LatestJson))
            {
                throw new FileNotFoundException($"Output JSON missing at: {handshake.Files.LatestJson}");
            }

            string resultsJson = await File.ReadAllTextAsync(handshake.Files.LatestJson);
            var payload = JsonSerializer.Deserialize<ScreeningPayload>(resultsJson);

            return (handshake, payload);
        }
    }
}
