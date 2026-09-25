namespace GastricCancerDetection.Domain.Entities.Clin;

public class Subject
{
    public int SubjectId { get; set; }
    public string SubjectCode { get; set; } = null!;
    public int? InstitutionId { get; set; }
    public Institution? Institution { get; set; }
    public char? Gender { get; set; }
    public int? BirthYear { get; set; }
    public string? Ethnicity { get; set; }

    /// <summary>مشخص می‌کند فرد سالم (کنترل) یا مبتلا (مورد) است</summary>
    public bool IsHealthy { get; set; }

    public string? DiagnosisICD10 { get; set; }
    public string? DiagnosisNotes { get; set; }
    public bool? FamilyHistoryCancer { get; set; }
    public string? SmokingStatus { get; set; }
    public string? HPyloriStatus { get; set; }
    public string? SourceDatabase { get; set; }
    public bool ConsentObtained { get; set; }
    public DateOnly? ConsentDate { get; set; }
    public bool IsDeleted { get; set; }
    public int? EnrolledByUserId { get; set; }

    public ICollection<Sample> Samples { get; set; } = new List<Sample>();
}
