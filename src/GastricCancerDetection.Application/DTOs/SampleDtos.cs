namespace GastricCancerDetection.Application.DTOs;

public record SampleCreateDto(
    int SubjectId,
    string SampleCode,
    byte? SampleTypeId,
    DateOnly? CollectionDate,
    byte? PlatformId,
    string? SequencingType,
    double? MeanCoverageDepth,
    string? LabName);

public record SampleDto(int SampleId, int SubjectId, string SampleCode);
