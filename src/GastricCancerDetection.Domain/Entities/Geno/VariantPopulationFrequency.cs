namespace GastricCancerDetection.Domain.Entities.Geno;

public class VariantPopulationFrequency
{
    public long VariantCatalogId { get; set; }
    public byte SourceId { get; set; }
    public double AlleleFrequency { get; set; }
    public int? AlleleCount { get; set; }
    public int? TotalAlleleNumber { get; set; }
}
