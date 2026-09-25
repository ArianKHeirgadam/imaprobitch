using GastricCancerDetection.Application.DTOs;
using GastricCancerDetection.Application.Interfaces;
using GastricCancerDetection.Domain.Entities.Clin;
using GastricCancerDetection.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace GastricCancerDetection.Infrastructure.Services;

public class SampleService : ISampleService
{
    private readonly ApplicationDbContext _db;
    public SampleService(ApplicationDbContext db) => _db = db;

    public async Task<SampleDto> CreateAsync(SampleCreateDto dto, CancellationToken ct = default)
    {
        var subjectExists = await _db.Subjects.AnyAsync(x => x.SubjectId == dto.SubjectId, ct);
        if (!subjectExists)
            throw new InvalidOperationException($"فردی با شناسه {dto.SubjectId} پیدا نشد.");

        var entity = new Sample
        {
            SubjectId = dto.SubjectId,
            SampleCode = dto.SampleCode,
            SampleTypeId = dto.SampleTypeId,
            CollectionDate = dto.CollectionDate,
            PlatformId = dto.PlatformId,
            SequencingType = dto.SequencingType,
            MeanCoverageDepth = dto.MeanCoverageDepth,
            LabName = dto.LabName
        };

        _db.Samples.Add(entity);
        await _db.SaveChangesAsync(ct);

        return new SampleDto(entity.SampleId, entity.SubjectId, entity.SampleCode);
    }

    public async Task<List<SampleDto>> GetBySubjectAsync(int subjectId, CancellationToken ct = default)
    {
        return await _db.Samples.AsNoTracking()
            .Where(x => x.SubjectId == subjectId)
            .Select(x => new SampleDto(x.SampleId, x.SubjectId, x.SampleCode))
            .ToListAsync(ct);
    }
}
