using GastricCancerDetection.Application.DTOs;
using GastricCancerDetection.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace GastricCancerDetection.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ReportsController : ControllerBase
{
    private readonly IReportService _reportService;
    public ReportsController(IReportService reportService) => _reportService = reportService;

    /// <summary>تولید گزارش خروجی (Excel یا PDF) برای یک اجرای تحلیل مشخص</summary>
    [HttpPost("generate/{runId:int}")]
    public async Task<ActionResult<GeneratedReportDto>> Generate(int runId, [FromQuery] ReportFormat format, [FromQuery] int? generatedByUserId, CancellationToken ct)
    {
        try
        {
            var result = await _reportService.GenerateAsync(runId, format, generatedByUserId, ct);
            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { error = ex.Message });
        }
    }

    /// <summary>دانلود فایل گزارش تولیدشده بر اساس شناسه‌ی گزارش</summary>
    [HttpGet("download/{reportId:int}")]
    public async Task<IActionResult> Download(int reportId, CancellationToken ct)
    {
        var file = await _reportService.GetReportFileAsync(reportId, ct);
        if (file is null) return NotFound();
        return File(file.Value.Content, file.Value.ContentType, file.Value.FileName);
    }
}
