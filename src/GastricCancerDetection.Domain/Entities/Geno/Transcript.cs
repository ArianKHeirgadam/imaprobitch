namespace GastricCancerDetection.Domain.Entities.Geno;

public class Transcript
{
    public int TranscriptId { get; set; }
    public int GeneId { get; set; }
    public string EnsemblTranscriptId { get; set; } = null!;
    public bool IsCanonical { get; set; }
    public int? ExonCount { get; set; }
}
