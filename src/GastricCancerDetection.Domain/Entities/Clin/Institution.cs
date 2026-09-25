namespace GastricCancerDetection.Domain.Entities.Clin;

public class Institution
{
    public int InstitutionId { get; set; }
    public string Name { get; set; } = null!;
    public string? Country { get; set; }
    public string? ContactEmail { get; set; }
}
