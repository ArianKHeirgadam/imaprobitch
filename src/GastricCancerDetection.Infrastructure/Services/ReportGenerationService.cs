using ClosedXML.Excel;
using GastricCancerDetection.Application.DTOs;
using GastricCancerDetection.Application.Interfaces;
using GastricCancerDetection.Domain.Entities.Analysis;
using GastricCancerDetection.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;

namespace GastricCancerDetection.Infrastructure.Services;

public class ReportGenerationService : IReportService
{
    private readonly ApplicationDbContext _db;
    private readonly IAnalysisService _analysisService;
    private readonly StorageOptions _options;

    public ReportGenerationService(ApplicationDbContext db, IAnalysisService analysisService, IOptions<StorageOptions> options)
    {
        _db = db;
        _analysisService = analysisService;
        _options = options.Value;
        QuestPDF.Settings.License = LicenseType.Community;
    }

    public async Task<GeneratedReportDto> GenerateAsync(int runId, ReportFormat format, int? generatedByUserId, CancellationToken ct = default)
    {
        var result = await _analysisService.GetRunResultAsync(runId, ct)
            ?? throw new InvalidOperationException($"اجرای تحلیل با شناسه {runId} پیدا نشد.");

        Directory.CreateDirectory(_options.ReportsRoot);
        var fileName = $"GastricCancerReport_Run{runId}_{DateTime.UtcNow:yyyyMMddHHmmss}.{(format == ReportFormat.Excel ? "xlsx" : "pdf")}";
        var fullPath = Path.Combine(_options.ReportsRoot, fileName);

        if (format == ReportFormat.Excel)
            GenerateExcel(result, fullPath);
        else
            GeneratePdf(result, fullPath);

        var entity = new GeneratedReport
        {
            RunId = runId,
            ReportFormat = format.ToString(),
            FilePath = fullPath,
            GeneratedByUserId = generatedByUserId
        };
        _db.GeneratedReports.Add(entity);
        await _db.SaveChangesAsync(ct);

        return new GeneratedReportDto(entity.ReportId, runId, entity.ReportFormat, fullPath);
    }

    public async Task<(byte[] Content, string ContentType, string FileName)?> GetReportFileAsync(int reportId, CancellationToken ct = default)
    {
        var report = await _db.GeneratedReports.AsNoTracking().FirstOrDefaultAsync(x => x.ReportId == reportId, ct);
        if (report is null || report.FilePath is null || !File.Exists(report.FilePath)) return null;

        var bytes = await File.ReadAllBytesAsync(report.FilePath, ct);
        var contentType = report.ReportFormat == "Excel"
            ? "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            : "application/pdf";

        return (bytes, contentType, Path.GetFileName(report.FilePath));
    }

    /// <summary>
    /// از روی نتایج مقایسه‌ی ژن‌ها و ریسک افراد، یک متن تفسیری خودکار می‌سازد
    /// که در انتهای هر دو نوع گزارش (PDF و Excel) درج می‌شود.
    /// </summary>
    private static string Ltr(object value) => $"\u200E{value}\u200E";

    private static string BuildInterpretationText(AnalysisRunResultDto result)
    {
        var sb = new System.Text.StringBuilder();

        var riskyGenes = result.GeneResults
            .Where(g => g.GeneRiskScore > 0)
            .OrderByDescending(g => g.GeneRiskScore)
            .ToList();

        if (riskyGenes.Any())
        {
            var geneNames = string.Join("، ", riskyGenes.Select(g => Ltr(g.GeneSymbol)));
            sb.AppendLine($"در این تحلیل، ژن(های) {geneNames} به‌عنوان عامل(های) مؤثر در تفاوت ریسک بین گروه‌های سالم و ناسالم شناسایی شد(ند).");
        }
        else
        {
            sb.AppendLine("در این تحلیل، هیچ ژنی با امتیاز ریسک قابل‌توجه بین دو گروه شناسایی نشد.");
        }

        foreach (var s in result.SubjectResults.Where(s => s.RiskCategory == "High"))
        {
            var genesPart = string.IsNullOrWhiteSpace(s.ContributingGenes)
                ? "."
                : $"، عمدتاً به‌دلیل واریانت(های) شناسایی‌شده در ژن(های) {Ltr(s.ContributingGenes)}.";
            sb.AppendLine($"فرد {Ltr(s.SubjectCode)} با امتیاز ریسک کل {Ltr(Math.Round(s.TotalRiskScore, 2))} در دسته‌ی ریسک «بالا» قرار گرفت{genesPart}");
        }

        foreach (var s in result.SubjectResults.Where(s => s.RiskCategory == "Low"))
        {
            sb.AppendLine($"فرد {Ltr(s.SubjectCode)} با امتیاز ریسک کل {Ltr(Math.Round(s.TotalRiskScore, 2))} در دسته‌ی ریسک «پایین» قرار گرفت.");
        }

        sb.AppendLine();
        sb.AppendLine("این گزارش صرفاً بر پایه‌ی مقایسه‌ی آماری فراوانی واریانت‌ها در ژن‌های هدف تولید شده و جایگزین تشخیص بالینی تخصصی نیست.");

        return sb.ToString();
    }

    private static void GenerateExcel(AnalysisRunResultDto result, string path)
    {
        using var workbook = new XLWorkbook();

        var summary = workbook.Worksheets.Add("خلاصه اجرا");
        summary.RightToLeft = true;
        summary.Cell(1, 1).Value = "گزارش غربالگری ریسک زودهنگام سرطان معده";
        summary.Cell(1, 1).Style.Font.Bold = true;
        summary.Cell(1, 1).Style.Font.FontSize = 14;
        summary.Cell(3, 1).Value = "شناسه اجرا"; summary.Cell(3, 2).Value = result.RunId;
        summary.Cell(4, 1).Value = "تاریخ اجرا"; summary.Cell(4, 2).Value = result.RunDate.ToString("yyyy-MM-dd HH:mm");
        summary.Cell(5, 1).Value = "تعداد افراد سالم"; summary.Cell(5, 2).Value = result.HealthyCount;
        summary.Cell(6, 1).Value = "تعداد افراد ناسالم"; summary.Cell(6, 2).Value = result.UnhealthyCount;
        summary.Cell(7, 1).Value = "وضعیت"; summary.Cell(7, 2).Value = result.Status;
        summary.Columns().AdjustToContents();

        var genesSheet = workbook.Worksheets.Add("مقایسه ژن‌ها");
        genesSheet.RightToLeft = true;
        string[] geneHeaders = { "ژن", "فراوانی در سالم", "فراوانی در ناسالم", "P-Value", "Odds Ratio", "امتیاز ریسک ژن" };
        for (int i = 0; i < geneHeaders.Length; i++)
        {
            genesSheet.Cell(1, i + 1).Value = geneHeaders[i];
            genesSheet.Cell(1, i + 1).Style.Font.Bold = true;
        }
        int row = 2;
        foreach (var g in result.GeneResults.OrderByDescending(x => x.GeneRiskScore))
        {
            genesSheet.Cell(row, 1).Value = g.GeneSymbol;
            genesSheet.Cell(row, 2).Value = Math.Round(g.HealthyVariantFreq, 4);
            genesSheet.Cell(row, 3).Value = Math.Round(g.UnhealthyVariantFreq, 4);
            genesSheet.Cell(row, 4).Value = g.PValue.HasValue ? Math.Round(g.PValue.Value, 6).ToString() : "-";
            genesSheet.Cell(row, 5).Value = g.OddsRatio.HasValue ? Math.Round(g.OddsRatio.Value, 4).ToString() : "-";
            genesSheet.Cell(row, 6).Value = Math.Round(g.GeneRiskScore, 4);
            row++;
        }
        genesSheet.Columns().AdjustToContents();

        var subjectsSheet = workbook.Worksheets.Add("نتایج افراد");
        subjectsSheet.RightToLeft = true;
        string[] subjectHeaders = { "کد فرد", "گروه", "امتیاز ریسک کل", "دسته ریسک", "ژن‌های مؤثر" };
        for (int i = 0; i < subjectHeaders.Length; i++)
        {
            subjectsSheet.Cell(1, i + 1).Value = subjectHeaders[i];
            subjectsSheet.Cell(1, i + 1).Style.Font.Bold = true;
        }
        row = 2;
        foreach (var s in result.SubjectResults)
        {
            subjectsSheet.Cell(row, 1).Value = s.SubjectCode;
            subjectsSheet.Cell(row, 2).Value = s.IsHealthy ? "سالم" : "ناسالم";
            subjectsSheet.Cell(row, 3).Value = Math.Round(s.TotalRiskScore, 4);
            subjectsSheet.Cell(row, 4).Value = s.RiskCategory;
            subjectsSheet.Cell(row, 5).Value = s.ContributingGenes ?? "-";
            row++;
        }
        subjectsSheet.Columns().AdjustToContents();

        // --- شیت جدید: تفسیر و نتیجه‌گیری خودکار ---
        var interpretationSheet = workbook.Worksheets.Add("تفسیر و نتیجه‌گیری");
        interpretationSheet.RightToLeft = true;
        interpretationSheet.Cell(1, 1).Value = "تفسیر و نتیجه‌گیری";
        interpretationSheet.Cell(1, 1).Style.Font.Bold = true;
        interpretationSheet.Cell(1, 1).Style.Font.FontSize = 14;

        var lines = BuildInterpretationText(result).Split('\n', StringSplitOptions.RemoveEmptyEntries);
        int interpRow = 3;
        foreach (var line in lines)
        {
            interpretationSheet.Cell(interpRow, 1).Value = line.Trim();
            interpretationSheet.Cell(interpRow, 1).Style.Alignment.WrapText = true;
            interpRow++;
        }
        interpretationSheet.Column(1).Width = 100;

        workbook.SaveAs(path);
    }

    private static void GeneratePdf(AnalysisRunResultDto result, string path)
    {
        Document.Create(container =>
        {
            container.Page(page =>
            {
                page.Size(PageSizes.A4);
                page.Margin(30);
                page.ContentFromRightToLeft(); // فعال‌سازی چیدمان راست‌به‌چپ برای کل صفحه
                page.DefaultTextStyle(x => x.FontSize(10));

                page.Header().Column(col =>
                {
                    col.Item().Text("گزارش غربالگری ریسک زودهنگام سرطان معده").FontSize(16).Bold();
                    col.Item().Text($"شناسه اجرا: {result.RunId}   |   تاریخ: {result.RunDate:yyyy-MM-dd HH:mm}   |   وضعیت: {result.Status}");
                    col.Item().Text($"تعداد سالم: {result.HealthyCount}   |   تعداد ناسالم: {result.UnhealthyCount}");
                    col.Item().PaddingBottom(10).LineHorizontal(1);
                });

                page.Content().Column(col =>
                {
                    col.Item().Text("مقایسه‌ی ژن‌ها").Bold().FontSize(12);
                    col.Item().Table(table =>
                    {
                        table.ColumnsDefinition(c =>
                        {
                            c.RelativeColumn(2); c.RelativeColumn(2); c.RelativeColumn(2);
                            c.RelativeColumn(2); c.RelativeColumn(2); c.RelativeColumn(2);
                        });
                        table.Header(h =>
                        {
                            foreach (var text in new[] { "ژن", "فراوانی سالم", "فراوانی ناسالم", "P-Value", "Odds Ratio", "امتیاز ریسک" })
                                h.Cell().Border(1).Padding(3).Text(text).Bold();
                        });
                        foreach (var g in result.GeneResults.OrderByDescending(x => x.GeneRiskScore))
                        {
                            table.Cell().Border(1).Padding(3).Text(g.GeneSymbol);
                            table.Cell().Border(1).Padding(3).Text(Math.Round(g.HealthyVariantFreq, 4).ToString());
                            table.Cell().Border(1).Padding(3).Text(Math.Round(g.UnhealthyVariantFreq, 4).ToString());
                            table.Cell().Border(1).Padding(3).Text(g.PValue.HasValue ? Math.Round(g.PValue.Value, 6).ToString() : "-");
                            table.Cell().Border(1).Padding(3).Text(g.OddsRatio.HasValue ? Math.Round(g.OddsRatio.Value, 4).ToString() : "-");
                            table.Cell().Border(1).Padding(3).Text(Math.Round(g.GeneRiskScore, 4).ToString());
                        }
                    });

                    col.Item().PaddingTop(15).Text("نتایج ریسک افراد").Bold().FontSize(12);
                    col.Item().Table(table =>
                    {
                        table.ColumnsDefinition(c =>
                        {
                            c.RelativeColumn(2); c.RelativeColumn(1.5f); c.RelativeColumn(1.5f);
                            c.RelativeColumn(1.5f); c.RelativeColumn(3);
                        });
                        table.Header(h =>
                        {
                            foreach (var text in new[] { "کد فرد", "گروه", "امتیاز ریسک", "دسته ریسک", "ژن‌های مؤثر" })
                                h.Cell().Border(1).Padding(3).Text(text).Bold();
                        });
                        foreach (var s in result.SubjectResults)
                        {
                            table.Cell().Border(1).Padding(3).Text(s.SubjectCode);
                            table.Cell().Border(1).Padding(3).Text(s.IsHealthy ? "سالم" : "ناسالم");
                            table.Cell().Border(1).Padding(3).Text(Math.Round(s.TotalRiskScore, 4).ToString());
                            table.Cell().Border(1).Padding(3).Text(s.RiskCategory);
                            table.Cell().Border(1).Padding(3).Text(s.ContributingGenes ?? "-");
                        }
                    });

                    // --- بخش جدید: تفسیر و نتیجه‌گیری خودکار ---
                    col.Item().PaddingTop(15).Text("تفسیر و نتیجه‌گیری").Bold().FontSize(12);
                    col.Item().PaddingTop(3).Text(BuildInterpretationText(result));
                });

                page.Footer().AlignCenter().Text(x =>
                {
                    x.Span("این گزارش صرفاً برای اهداف پژوهشی است و جایگزین تشخیص بالینی نیست. ").FontSize(8);
                });
            });
        }).GeneratePdf(path);
    }
}