namespace GastricCancerDetection.Application.DTOs;

public enum ReportFormat { Excel, PDF }

public record GeneratedReportDto(int ReportId, int RunId, string ReportFormat, string FilePath);
