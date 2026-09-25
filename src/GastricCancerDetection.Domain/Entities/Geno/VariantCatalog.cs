namespace GastricCancerDetection.Domain.Entities.Geno;

public class VariantCatalog
{
    public long VariantCatalogId { get; set; }
    public int BuildId { get; set; }
    public string Chromosome { get; set; } = null!;
    public long Position { get; set; }
    public string RefAllele { get; set; } = null!;
    public string AltAllele { get; set; } = null!;
    public string? dbSNP_Id { get; set; }
    public int? GeneId { get; set; }
    public Gene? Gene { get; set; }
    public int? TranscriptId { get; set; }
    public string? ClinVar_Id { get; set; }
    public byte? ClinSigId { get; set; }
    public byte? ConsequenceId { get; set; }
    public string? ProteinChange { get; set; }
    public double? SIFT_Score { get; set; }
    public double? PolyPhen_Score { get; set; }
    public double? CADD_Score { get; set; }
    public DateTime CreatedAt { get; set; }

    // VariantHash یک ستون Computed در دیتابیس است؛ EF فقط آن را می‌خواند (never insert/update)
    public byte[]? VariantHash { get; set; }
}
