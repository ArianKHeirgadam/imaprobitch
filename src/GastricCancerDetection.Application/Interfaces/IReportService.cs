using GastricCancerDetection.Application.DTOs;

namespace GastricCancerDetection.Application.Interfaces;

public interface IReportService
{
    Task<GeneratedReportDto> GenerateAsync(int runId, ReportFormat format, int? generatedByUserId, CancellationToken ct = default);
    Task<(byte[] Content, string ContentType, string FileName)?> GetReportFileAsync(int reportId, CancellationToken ct = default);
}
