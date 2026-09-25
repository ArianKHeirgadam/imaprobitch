using GastricCancerDetection.Application.DTOs;

namespace GastricCancerDetection.Application.Interfaces;

public interface IGenomeFileService
{
    /// <summary>
    /// فایل ژنومی (VCF) آپلودشده را روی دیسک ذخیره می‌کند، رکورد GenomeFiles را با وضعیت
    /// Pending می‌سازد. استخراج واریانت‌ها بعداً و هنگام اجرای تحلیل انجام می‌شود.
    /// </summary>
    Task<GenomeFileUploadResultDto> UploadAsync(int sampleId, Stream fileStream, string fileName, int? uploadedByUserId, CancellationToken ct = default);
}
