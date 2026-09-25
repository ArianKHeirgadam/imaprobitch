namespace GastricCancerDetection.Domain.Entities.Clin;

using GastricCancerDetection.Domain.Entities.Geno;

public class Sample
{
    public int SampleId { get; set; }
    public int SubjectId { get; set; }
    public Subject Subject { get; set; } = null!;
    public string SampleCode { get; set; } = null!;
    public byte? SampleTypeId { get; set; }
    public DateOnly? CollectionDate { get; set; }
    public byte? PlatformId { get; set; }
    public string? SequencingType { get; set; }
    public double? MeanCoverageDepth { get; set; }
    public string? LabName { get; set; }
    public bool? QCPassed { get; set; }
    public string? QCNotes { get; set; }
    public DateTime CreatedAt { get; set; }

    public ICollection<GenomeFile> GenomeFiles { get; set; } = new List<GenomeFile>();
}
