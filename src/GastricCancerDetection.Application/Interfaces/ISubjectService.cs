using GastricCancerDetection.Application.DTOs;

namespace GastricCancerDetection.Application.Interfaces;

public interface ISubjectService
{
    Task<SubjectDto> CreateAsync(SubjectCreateDto dto, CancellationToken ct = default);
    Task<SubjectDto?> GetByIdAsync(int subjectId, CancellationToken ct = default);
    Task<List<SubjectDto>> GetAllAsync(bool? isHealthy = null, CancellationToken ct = default);
    Task<bool> DeleteAsync(int subjectId, CancellationToken ct = default); // Soft delete
}
