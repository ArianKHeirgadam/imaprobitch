using GastricCancerDetection.Application.DTOs;
using GastricCancerDetection.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace GastricCancerDetection.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class GenomeFilesController : ControllerBase
{
    private readonly IGenomeFileService _genomeFileService;
    public GenomeFilesController(IGenomeFileService genomeFileService) => _genomeFileService = genomeFileService;

    /// <summary>
    /// آپلود فایل ژنومی (VCF) برای یک نمونه‌ی مشخص. فایل روی دیسک ذخیره می‌شود و رکورد آن
    /// با وضعیت Pending ثبت می‌گردد؛ استخراج واریانت هنگام اجرای بعدی تحلیل انجام خواهد شد.
    /// تعداد آپلود محدودیتی ندارد - برای هر Sample هر چند فایل که لازم باشد.
    /// </summary>
    [HttpPost("upload")]
    [RequestSizeLimit(500_000_000)] // تا ۵۰۰ مگابایت برای فایل‌های VCF بزرگ
    public async Task<ActionResult<GenomeFileUploadResultDto>> Upload(
    [FromForm] UploadGenomeFileRequest request, CancellationToken ct)
    {
        if (request.File is null || request.File.Length == 0)
            return BadRequest(new { error = "فایلی ارسال نشده است." });

        try
        {
            await using var stream = request.File.OpenReadStream();
            var result = await _genomeFileService.UploadAsync(
                request.SampleId, stream, request.File.FileName, request.UploadedByUserId, ct);
            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { error = ex.Message });
        }
    }
}
