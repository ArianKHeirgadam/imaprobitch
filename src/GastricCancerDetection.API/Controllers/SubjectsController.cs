using GastricCancerDetection.Application.DTOs;
using GastricCancerDetection.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace GastricCancerDetection.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class SubjectsController : ControllerBase
{
    private readonly ISubjectService _subjectService;
    public SubjectsController(ISubjectService subjectService) => _subjectService = subjectService;

    /// <summary>ثبت یک فرد جدید (سالم یا ناسالم) در سیستم</summary>
    [HttpPost]
    public async Task<ActionResult<SubjectDto>> Create([FromBody] SubjectCreateDto dto, CancellationToken ct)
    {
        try
        {
            var result = await _subjectService.CreateAsync(dto, ct);
            return CreatedAtAction(nameof(GetById), new { id = result.SubjectId }, result);
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { error = ex.Message });
        }
    }

    /// <summary>دریافت لیست افراد؛ با پارامتر isHealthy می‌توان فیلتر کرد</summary>
    [HttpGet]
    public async Task<ActionResult<List<SubjectDto>>> GetAll([FromQuery] bool? isHealthy, CancellationToken ct)
        => Ok(await _subjectService.GetAllAsync(isHealthy, ct));

    [HttpGet("{id:int}")]
    public async Task<ActionResult<SubjectDto>> GetById(int id, CancellationToken ct)
    {
        var result = await _subjectService.GetByIdAsync(id, ct);
        return result is null ? NotFound() : Ok(result);
    }

    /// <summary>حذف نرم (Soft Delete) - رکورد و تاریخچه‌اش در دیتابیس باقی می‌ماند</summary>
    [HttpDelete("{id:int}")]
    public async Task<IActionResult> Delete(int id, CancellationToken ct)
    {
        var deleted = await _subjectService.DeleteAsync(id, ct);
        return deleted ? NoContent() : NotFound();
    }
}
