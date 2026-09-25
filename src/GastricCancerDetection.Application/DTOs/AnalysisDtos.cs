namespace GastricCancerDetection.Application.DTOs;

public record AnalysisRunRequestDto(int PanelId, int ModelVersionId, int? TriggeredByUserId);

public record GeneComparisonResultDto(
    string GeneSymbol,
    double HealthyVariantFreq,
    double UnhealthyVariantFreq,
    double? PValue,
    double? OddsRatio,
    double GeneRiskScore);

public record SubjectRiskResultDto(
    int SubjectId,
    string SubjectCode,
    bool IsHealthy,
    double TotalRiskScore,
    string RiskCategory,
    string? ContributingGenes);

public record AnalysisRunResultDto(
    int RunId,
    DateTime RunDate,
    int HealthyCount,
    int UnhealthyCount,
    string Status,
    List<GeneComparisonResultDto> GeneResults,
    List<SubjectRiskResultDto> SubjectResults);
