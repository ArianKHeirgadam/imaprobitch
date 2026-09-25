namespace GastricCancerDetection.Domain.Entities.Clin;

public class HPOTerm
{
    public int HPOTermId { get; set; }
    public string HPOCode { get; set; } = null!;
    public string TermName { get; set; } = null!;
}
