namespace GastricCancerDetection.Domain.Entities.Analysis;

public class AnalysisRun
{
    public int RunId { get; set; }
    public int PanelId { get; set; }
    public int ModelVersionId { get; set; }
    public RiskModelVersion? ModelVersion { get; set; }
    public DateTime RunDate { get; set; }
    public int? TriggeredByUserId { get; set; }
    public string? PipelineVersion { get; set; }
    public int HealthyCount { get; set; }
    public int UnhealthyCount { get; set; }
    public string? Notes { get; set; }

    /// <summary>وضعیت اجرای تحلیل — ref.ProcessingStatusTypes</summary>
    public byte StatusId { get; set; }

    public ICollection<GeneComparisonResult> GeneResults { get; set; } = new List<GeneComparisonResult>();
    public ICollection<SubjectRiskResult> SubjectResults { get; set; } = new List<SubjectRiskResult>();
}
