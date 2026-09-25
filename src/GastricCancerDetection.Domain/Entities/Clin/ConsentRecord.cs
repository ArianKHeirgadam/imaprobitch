namespace GastricCancerDetection.Domain.Entities.Clin;

public class ConsentRecord
{
    public int ConsentId { get; set; }
    public int SubjectId { get; set; }
    public string? ConsentFormVersion { get; set; }
    public string? ConsentScope { get; set; }
    public DateTime? SignedAt { get; set; }
    public DateTime? WithdrawnAt { get; set; }
    public string? DocumentPath { get; set; }
}
