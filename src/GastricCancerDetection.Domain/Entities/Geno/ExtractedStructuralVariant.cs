namespace GastricCancerDetection.Domain.Entities.Geno;

public class ExtractedStructuralVariant
{
    public long ExtractedSVId { get; set; }
    public int FileId { get; set; }
    public long SVCatalogId { get; set; }
    public int? CopyNumber { get; set; }
    public double? ConfidenceScore { get; set; }
}
