namespace GastricCancerDetection.Application.DTOs;

public record SubjectCreateDto(
    string SubjectCode,
    char? Gender,
    int? BirthYear,
    string? Ethnicity,
    bool IsHealthy,
    string? DiagnosisICD10,
    string? DiagnosisNotes,
    bool? FamilyHistoryCancer,
    string? SmokingStatus,
    string? HPyloriStatus,
    string? SourceDatabase,
    bool ConsentObtained);

public record SubjectDto(
    int SubjectId,
    string SubjectCode,
    bool IsHealthy,
    string? DiagnosisICD10,
    DateTime CreatedImplicitly);
