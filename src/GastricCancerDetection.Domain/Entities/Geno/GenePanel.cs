namespace GastricCancerDetection.Domain.Entities.Geno;

public class GenePanel
{
    public int PanelId { get; set; }
    public string PanelName { get; set; } = null!;
    public string PanelVersion { get; set; } = null!;
    public string? Description { get; set; }
    public int? CreatedByUserId { get; set; }
    public DateTime CreatedAt { get; set; }
    public bool IsActive { get; set; } = true;

    public ICollection<GenePanelGene> PanelGenes { get; set; } = new List<GenePanelGene>();
}
