namespace GastricCancerDetection.Domain.Entities.Geno;

public class StructuralVariantCatalog
{
    public long SVCatalogId { get; set; }
    public int BuildId { get; set; }
    public string Chromosome { get; set; } = null!;
    public long StartPosition { get; set; }
    public long EndPosition { get; set; }
    public string SVType { get; set; } = null!;
    public int? GeneId { get; set; }
    public byte? ClinSigId { get; set; }
}
