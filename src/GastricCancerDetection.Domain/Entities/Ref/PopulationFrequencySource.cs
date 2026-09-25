namespace GastricCancerDetection.Domain.Entities.Ref;

public class PopulationFrequencySource
{
    public byte SourceId { get; set; }
    public string SourceName { get; set; } = null!;
    public string? SourceVersion { get; set; }
    public string? Url { get; set; }
}
