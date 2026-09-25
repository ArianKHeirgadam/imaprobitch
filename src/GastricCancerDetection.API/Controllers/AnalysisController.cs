using GastricCancerDetection.Application.DTOs;
using GastricCancerDetection.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace GastricCancerDetection.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AnalysisController : ControllerBase
{
    private readonly IAnalysisService _analysisService;
    public AnalysisController(IAnalysisService analysisService) => _analysisService = analysisService;

    /// <summary>
    /// اجرای کامل یک تحلیل: استخراج واریانت از فایل‌های در انتظار (Python) -> مقایسه‌ی آماری
    /// بین گروه سالم/ناسالم (Fisher's Exact Test) -> محاسبه‌ی امتیاز ریسک هر فرد -> ذخیره‌ی نتایج.
    /// این عملیات ممکن است بسته به تعداد فایل‌های Pending چند ثانیه تا چند دقیقه طول بکشد.
    /// </summary>
    [HttpPost("run")]
    public async Task<ActionResult<AnalysisRunResultDto>> Run([FromBody] AnalysisRunRequestDto request, CancellationToken ct)
    {
        try
        {
            var result = await _analysisService.RunAnalysisAsync(request, ct);
            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpGet("runs")]
    public async Task<ActionResult<List<AnalysisRunResultDto>>> GetAllRuns(CancellationToken ct)
        => Ok(await _analysisService.GetAllRunsAsync(ct));

    [HttpGet("runs/{runId:int}")]
    public async Task<ActionResult<AnalysisRunResultDto>> GetRun(int runId, CancellationToken ct)
    {
        var result = await _analysisService.GetRunResultAsync(runId, ct);
        return result is null ? NotFound() : Ok(result);
    }
}
