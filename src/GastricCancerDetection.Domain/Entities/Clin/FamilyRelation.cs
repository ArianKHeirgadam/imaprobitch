namespace GastricCancerDetection.Domain.Entities.Clin;

public class FamilyRelation
{
    public int RelationId { get; set; }
    public int SubjectId { get; set; }
    public int RelativeSubjectId { get; set; }
    public string RelationType { get; set; } = null!;
}
