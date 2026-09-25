using System.Diagnostics;
using System.Text.Json;
using GastricCancerDetection.Application.Interfaces;
using Microsoft.Extensions.Options;
using Microsoft.Extensions.Logging;

namespace GastricCancerDetection.Infrastructure.Services;

/// <summary>
/// پایتون و دات‌نت با شبکه به هم وصل نمی‌شوند؛ این سرویس اسکریپت پایتون را مثل یک
/// برنامه‌ی خط‌فرمان (Process) با Arguments مشخص اجرا می‌کند و خروجی JSON آن را از
/// stdout می‌خواند. مسیر Python و اسکریپت از appsettings.json (بخش Storage) خوانده می‌شود.
/// </summary>
public class PythonRunnerService : IPythonRunnerService
{
    private readonly StorageOptions _options;
    private readonly ILogger<PythonRunnerService> _logger;

    public PythonRunnerService(IOptions<StorageOptions> options, ILogger<PythonRunnerService> logger)
    {
        _options = options.Value;
        _logger = logger;
    }

    public async Task<List<ExtractedVariantRaw>> ExtractVariantsAsync(
        string vcfFilePath, IReadOnlyList<string> targetGeneSymbols, CancellationToken ct = default)
    {
        if (!File.Exists(vcfFilePath))
            throw new FileNotFoundException("فایل VCF روی دیسک پیدا نشد.", vcfFilePath);

        var genesArg = string.Join(",", targetGeneSymbols);

        var psi = new ProcessStartInfo
        {
            FileName = _options.PythonExecutablePath,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };
        psi.ArgumentList.Add(_options.PythonScriptPath);
        psi.ArgumentList.Add("--vcf");
        psi.ArgumentList.Add(vcfFilePath);
        psi.ArgumentList.Add("--genes");
        psi.ArgumentList.Add(genesArg);

        using var process = new Process { StartInfo = psi };
        process.Start();

        var stdOutTask = process.StandardOutput.ReadToEndAsync(ct);
        var stdErrTask = process.StandardError.ReadToEndAsync(ct);
        await process.WaitForExitAsync(ct);

        var stdOut = await stdOutTask;
        var stdErr = await stdErrTask;

        if (process.ExitCode != 0)
        {
            _logger.LogError("خطای اسکریپت Python برای فایل {File}: {Error}", vcfFilePath, stdErr);
            throw new InvalidOperationException($"اجرای اسکریپت تحلیل پایتون شکست خورد: {stdErr}");
        }

        if (!string.IsNullOrWhiteSpace(stdErr))
            _logger.LogWarning("هشدار از اسکریپت Python: {Warning}", stdErr);

        var result = JsonSerializer.Deserialize<PythonOutputEnvelope>(stdOut, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });

        if (result is null || !result.Success)
            throw new InvalidOperationException($"اسکریپت تحلیل خروجی نامعتبر داد: {result?.ErrorMessage}");

        return result.Variants.Select(v => new ExtractedVariantRaw(
            v.Chromosome, v.Position, v.RefAllele, v.AltAllele, v.GeneSymbol,
            v.Zygosity, v.Quality, v.ReadDepth, v.AlleleFraction)).ToList();
    }

    private class PythonOutputEnvelope
    {
        public bool Success { get; set; }
        public string? ErrorMessage { get; set; }
        public List<PythonVariantRecord> Variants { get; set; } = new();
    }

    private class PythonVariantRecord
    {
        public string Chromosome { get; set; } = null!;
        public long Position { get; set; }
        public string RefAllele { get; set; } = null!;
        public string AltAllele { get; set; } = null!;
        public string? GeneSymbol { get; set; }
        public string Zygosity { get; set; } = "Unknown";
        public double? Quality { get; set; }
        public int? ReadDepth { get; set; }
        public double? AlleleFraction { get; set; }
    }
}
