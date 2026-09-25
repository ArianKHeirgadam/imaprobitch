namespace GastricCancerDetection.Domain.Entities.Geno;

public class SequencingRun
{
    public int SeqRunId { get; set; }
    public string RunName { get; set; } = null!;
    public string? FlowCellId { get; set; }
    public DateOnly? RunDate { get; set; }
    public int? OperatorUserId { get; set; }
}
