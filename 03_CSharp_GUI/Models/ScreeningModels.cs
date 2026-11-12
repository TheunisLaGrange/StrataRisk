using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace StrataRisk.GUI.Models
{
    public class HandshakeResponse
    {
        [JsonPropertyName("status")]
        public string Status { get; set; } = string.Empty;

        [JsonPropertyName("stage")]
        public string? Stage { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; } = string.Empty;

        [JsonPropertyName("processed_count")]
        public int ProcessedCount { get; set; }

        [JsonPropertyName("failed_count")]
        public int FailedCount { get; set; }

        [JsonPropertyName("files")]
        public OutputFiles? Files { get; set; }
    }

    public class OutputFiles
    {
        [JsonPropertyName("latest_json")]
        public string LatestJson { get; set; } = string.Empty;

        [JsonPropertyName("latest_csv")]
        public string LatestCsv { get; set; } = string.Empty;

        [JsonPropertyName("html_charts")]
        public string HtmlCharts { get; set; } = string.Empty;
    }

    public class ScreeningPayload
    {
        [JsonPropertyName("generated_at")]
        public string GeneratedAt { get; set; } = string.Empty;

        [JsonPropertyName("record_count")]
        public int RecordCount { get; set; }

        [JsonPropertyName("results")]
        public List<EquityResult> Results { get; set; } = new();
    }

    public class EquityResult
    {
        [JsonPropertyName("symbol")]
        public string Symbol { get; set; } = string.Empty;

        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("sector")]
        public string Sector { get; set; } = string.Empty;

        [JsonPropertyName("current_price")]
        public double CurrentPrice { get; set; }

        [JsonPropertyName("trailing_pe")]
        public double? TrailingPe { get; set; }

        [JsonPropertyName("peg_ratio")]
        public double? PegRatio { get; set; }

        [JsonPropertyName("roe_pct")]
        public double? RoePct { get; set; }

        [JsonPropertyName("ema_50")]
        public double Ema50 { get; set; }

        [JsonPropertyName("sma_200")]
        public double Sma200 { get; set; }

        [JsonPropertyName("trend_signal")]
        public string TrendSignal { get; set; } = string.Empty;

        [JsonPropertyName("cash_to_debt")]
        public double CashToDebt { get; set; }

        [JsonPropertyName("fcf_yield_pct")]
        public double? FcfYieldPct { get; set; }

        [JsonPropertyName("stress_score")]
        public int StressScore { get; set; }

        [JsonPropertyName("risk_tier")]
        public string RiskTier { get; set; } = string.Empty;

        [JsonPropertyName("risk_flags")]
        public List<string> RiskFlags { get; set; } = new();

        public string RiskFlagsDisplay => RiskFlags.Count > 0 ? string.Join(", ", RiskFlags) : "NONE";
    }
}
