namespace GastricCancerDetection.Application.Interfaces;

public record ExtractedVariantRaw(
    string Chromosome,
    long Position,
    string RefAllele,
    string AltAllele,
    string? GeneSymbol,
    string Zygosity,
    double? Quality,
    int? ReadDepth,
    double? AlleleFraction);

public interface IPythonRunnerService
{
    /// <summary>
    /// اسکریپت Python (analyze_vcf.py) را روی یک فایل VCF اجرا می‌کند و لیست جهش‌های
    /// یافت‌شده در محدوده‌ی ژن‌های پنل هدف را برمی‌گرداند (خروجی JSON پردازش‌شده).
    /// </summary>
    Task<List<ExtractedVariantRaw>> ExtractVariantsAsync(string vcfFilePath, IReadOnlyList<string> targetGeneSymbols, CancellationToken ct = default);
}
