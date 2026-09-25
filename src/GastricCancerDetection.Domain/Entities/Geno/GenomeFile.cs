namespace GastricCancerDetection.Domain.Entities.Geno;

public class GenomeFile
{
    public int FileId { get; set; }
    public int SampleId { get; set; }
    public int? SeqRunId { get; set; }
    public int BuildId { get; set; }
    public string FileName { get; set; } = null!;
    public string FilePath { get; set; } = null!;
    public string FileFormat { get; set; } = "VCF";
    public long? FileSizeBytes { get; set; }
    public string? Checksum_SHA256 { get; set; }
    public bool IsEncryptedAtRest { get; set; } = true;
    public int? UploadedByUserId { get; set; }
    public DateTime UploadedAt { get; set; }

    /// <summary>وضعیت پردازش: Pending/Processing/Done/Failed/Rejected — ref.ProcessingStatusTypes</summary>
    public byte StatusId { get; set; }
    public DateTime? ProcessedAt { get; set; }
    public string? ErrorMessage { get; set; }

    public ICollection<ExtractedVariant> ExtractedVariants { get; set; } = new List<ExtractedVariant>();
}
