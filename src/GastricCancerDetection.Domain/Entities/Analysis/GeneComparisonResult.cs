namespace GastricCancerDetection.Domain.Entities.Analysis;

public class GeneComparisonResult
{
    public long ResultId { get; set; }
    public int RunId { get; set; }
    public int GeneId { get; set; }
    public double HealthyVariantFreq { get; set; }
    public double UnhealthyVariantFreq { get; set; }
    public double? PValue { get; set; }
    public double? OddsRatio { get; set; }
    public double? ConfidenceInterval95Low { get; set; }
    public double? ConfidenceInterval95High { get; set; }
    public double GeneRiskScore { get; set; }
}
