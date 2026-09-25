namespace GastricCancerDetection.Domain.Entities.Ref;

public class RefGenomeBuild
{
    public int BuildId { get; set; }
    public string BuildName { get; set; } = null!;
    public bool IsDefault { get; set; }
}
