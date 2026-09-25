namespace GastricCancerDetection.Domain.Entities.Clin;

public class SubjectPhenotype
{
    public int SubjectId { get; set; }
    public int HPOTermId { get; set; }
    public string? Notes { get; set; }
}
