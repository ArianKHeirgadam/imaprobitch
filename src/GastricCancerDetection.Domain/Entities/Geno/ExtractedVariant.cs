namespace GastricCancerDetection.Domain.Entities.Geno;

public class ExtractedVariant
{
    public long ExtractedVariantId { get; set; }
    public int FileId { get; set; }
    public GenomeFile? GenomeFile { get; set; }
    public long VariantCatalogId { get; set; }
    public VariantCatalog VariantCatalog { get; set; } = null!;
    public byte ZygosityId { get; set; }
    public double? Quality { get; set; }
    public int? ReadDepth { get; set; }
    public double? AlleleFraction { get; set; }
    public DateTime CreatedAt { get; set; }
}
