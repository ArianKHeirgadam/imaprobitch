namespace GastricCancerDetection.Domain.Entities.Ref;

public class RiskCategoryType
{
    public byte RiskCategoryId { get; set; }
    public string CategoryName { get; set; } = null!;
    public double MinScore { get; set; }
    public double? MaxScore { get; set; }
    public string? ColorHex { get; set; }
}
