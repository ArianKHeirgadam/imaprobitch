namespace GastricCancerDetection.Domain.Entities.Analysis;

public class SubjectRiskResult
{
    public long ResultId { get; set; }
    public int RunId { get; set; }
    public int SubjectId { get; set; }
    public int? SampleId { get; set; }
    public double TotalRiskScore { get; set; }

    /// <summary>Low/Medium/High/Critical — ref.RiskCategoryTypes</summary>
    public byte RiskCategoryId { get; set; }
    public string? ContributingGenes { get; set; }
    public DateTime GeneratedAt { get; set; }
}
