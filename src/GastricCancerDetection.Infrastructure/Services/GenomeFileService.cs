using System.Security.Cryptography;
using GastricCancerDetection.Application.DTOs;
using GastricCancerDetection.Application.Interfaces;
using GastricCancerDetection.Domain.Entities.Geno;
using GastricCancerDetection.Domain.Entities.Ref;
using GastricCancerDetection.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;

namespace GastricCancerDetection.Infrastructure.Services;

public class GenomeFileService : IGenomeFileService
{
    private readonly ApplicationDbContext _db;
    private readonly StorageOptions _options;

    public GenomeFileService(ApplicationDbContext db, IOptions<StorageOptions> options)
    {
        _db = db;
        _options = options.Value;
    }

    public async Task<GenomeFileUploadResultDto> UploadAsync(int sampleId, Stream fileStream, string fileName, int? uploadedByUserId, CancellationToken ct = default)
    {
        var sampleExists = await _db.Samples.AnyAsync(x => x.SampleId == sampleId, ct);
        if (!sampleExists)
            throw new InvalidOperationException($"نمونه‌ای با شناسه {sampleId} پیدا نشد.");

        var extension = Path.GetExtension(fileName);
        if (!string.Equals(extension, ".vcf", StringComparison.OrdinalIgnoreCase) &&
            !string.Equals(extension, ".gz", StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("فقط فایل‌های VCF (.vcf یا .vcf.gz) در حال حاضر پشتیبانی می‌شوند.");

        Directory.CreateDirectory(_options.GenomeFilesRoot);
        var storedFileName = $"{Guid.NewGuid()}_{fileName}";
        var fullPath = Path.Combine(_options.GenomeFilesRoot, storedFileName);

        using (var sha256 = SHA256.Create())
        using (var output = new FileStream(fullPath, FileMode.Create, FileAccess.Write))
        using (var hashingStream = new CryptoStream(output, sha256, CryptoStreamMode.Write))
        {
            await fileStream.CopyToAsync(hashingStream, ct);
            hashingStream.FlushFinalBlock();

            var defaultBuildId = await _db.RefGenomeBuilds
                .Where(x => x.IsDefault)
                .Select(x => x.BuildId)
                .FirstOrDefaultAsync(ct);

            var entity = new GenomeFile
            {
                SampleId = sampleId,
                BuildId = defaultBuildId == 0 ? 1 : defaultBuildId,
                FileName = fileName,
                FilePath = fullPath,
                FileFormat = "VCF",
                FileSizeBytes = output.Length,
                Checksum_SHA256 = Convert.ToHexString(sha256.Hash!),
                UploadedByUserId = uploadedByUserId,
                StatusId = ProcessingStatusType.Pending
            };

            _db.GenomeFiles.Add(entity);
            await _db.SaveChangesAsync(ct);

            return new GenomeFileUploadResultDto(entity.FileId, entity.FileName, "Pending");
        }
    }
}
