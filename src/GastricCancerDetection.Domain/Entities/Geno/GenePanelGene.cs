namespace GastricCancerDetection.Domain.Entities.Geno;

public class GenePanelGene
{
    public int PanelGeneId { get; set; }
    public int PanelId { get; set; }
    public int GeneId { get; set; }
    public Gene Gene { get; set; } = null!;

    /// <summary>وزن ژن در محاسبه‌ی امتیاز ریسک نهایی فرد</summary>
    public double RiskWeight { get; set; } = 1.0;
    public string? InheritancePattern { get; set; }
    public string? EvidenceSource { get; set; }
}
