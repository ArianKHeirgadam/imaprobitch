using GastricCancerDetection.Application.DTOs;

namespace GastricCancerDetection.Application.Interfaces;

public interface ISampleService
{
    Task<SampleDto> CreateAsync(SampleCreateDto dto, CancellationToken ct = default);
    Task<List<SampleDto>> GetBySubjectAsync(int subjectId, CancellationToken ct = default);
}
