using GastricCancerDetection.Application.DTOs;
using GastricCancerDetection.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace GastricCancerDetection.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class SamplesController : ControllerBase
{
    private readonly ISampleService _sampleService;
    public SamplesController(ISampleService sampleService) => _sampleService = sampleService;

    /// <summary>ثبت یک نمونه‌ی جدید (Sample) برای یک فرد از قبل ثبت‌شده</summary>
    [HttpPost]
    public async Task<ActionResult<SampleDto>> Create([FromBody] SampleCreateDto dto, CancellationToken ct)
    {
        try
        {
            var result = await _sampleService.CreateAsync(dto, ct);
            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpGet("by-subject/{subjectId:int}")]
    public async Task<ActionResult<List<SampleDto>>> GetBySubject(int subjectId, CancellationToken ct)
        => Ok(await _sampleService.GetBySubjectAsync(subjectId, ct));
}
