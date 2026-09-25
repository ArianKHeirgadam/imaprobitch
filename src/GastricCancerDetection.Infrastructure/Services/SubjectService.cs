using GastricCancerDetection.Application.DTOs;
using GastricCancerDetection.Application.Interfaces;
using GastricCancerDetection.Domain.Entities.Clin;
using GastricCancerDetection.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace GastricCancerDetection.Infrastructure.Services;

public class SubjectService : ISubjectService
{
    private readonly ApplicationDbContext _db;
    public SubjectService(ApplicationDbContext db) => _db = db;

    public async Task<SubjectDto> CreateAsync(SubjectCreateDto dto, CancellationToken ct = default)
    {
        var entity = new Subject
        {
            SubjectCode = dto.SubjectCode,
            Gender = dto.Gender,
            BirthYear = dto.BirthYear,
            Ethnicity = dto.Ethnicity,
            IsHealthy = dto.IsHealthy,
            DiagnosisICD10 = dto.DiagnosisICD10,
            DiagnosisNotes = dto.DiagnosisNotes,
            FamilyHistoryCancer = dto.FamilyHistoryCancer,
            SmokingStatus = dto.SmokingStatus,
            HPyloriStatus = dto.HPyloriStatus,
            SourceDatabase = dto.SourceDatabase,
            ConsentObtained = dto.ConsentObtained,
            ConsentDate = dto.ConsentObtained ? DateOnly.FromDateTime(DateTime.UtcNow) : null
        };

        _db.Subjects.Add(entity);
        await _db.SaveChangesAsync(ct);

        return Map(entity);
    }

    public async Task<SubjectDto?> GetByIdAsync(int subjectId, CancellationToken ct = default)
    {
        var entity = await _db.Subjects.AsNoTracking().FirstOrDefaultAsync(x => x.SubjectId == subjectId, ct);
        return entity is null ? null : Map(entity);
    }

    public async Task<List<SubjectDto>> GetAllAsync(bool? isHealthy = null, CancellationToken ct = default)
    {
        var query = _db.Subjects.AsNoTracking().AsQueryable();
        if (isHealthy.HasValue) query = query.Where(x => x.IsHealthy == isHealthy.Value);
        var list = await query.OrderByDescending(x => x.SubjectId).ToListAsync(ct);
        return list.Select(Map).ToList();
    }

    public async Task<bool> DeleteAsync(int subjectId, CancellationToken ct = default)
    {
        var entity = await _db.Subjects.FirstOrDefaultAsync(x => x.SubjectId == subjectId, ct);
        if (entity is null) return false;
        entity.IsDeleted = true; // Soft delete - رکورد و تاریخچه‌اش هرگز فیزیکی حذف نمی‌شود
        await _db.SaveChangesAsync(ct);
        return true;
    }

    private static SubjectDto Map(Subject s) =>
        new(s.SubjectId, s.SubjectCode, s.IsHealthy, s.DiagnosisICD10, DateTime.UtcNow);
}
