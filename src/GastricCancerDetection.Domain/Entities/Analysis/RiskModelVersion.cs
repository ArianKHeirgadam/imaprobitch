namespace GastricCancerDetection.Domain.Entities.Analysis;

public class RiskModelVersion
{
    public int ModelVersionId { get; set; }
    public string VersionName { get; set; } = null!;
    public string? Description { get; set; }
    public string StatisticalMethod { get; set; } = "Fisher_Exact_Test";
    public string? ScoringFormula { get; set; }
    public int? ValidatedByUserId { get; set; }
    public string? ValidationNotes { get; set; }

    /// <summary>فقط مدل‌های تأییدشده می‌توانند در اجرای واقعی تحلیل استفاده شوند</summary>
    public bool IsApprovedForUse { get; set; }
    public DateTime CreatedAt { get; set; }
}
