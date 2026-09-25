namespace GastricCancerDetection.Domain.Entities.Analysis;

public class GeneratedReport
{
    public int ReportId { get; set; }
    public int RunId { get; set; }
    public string ReportFormat { get; set; } = null!; // Excel | PDF
    public string? FilePath { get; set; }
    public int? GeneratedByUserId { get; set; }
    public DateTime GeneratedAt { get; set; }
}
