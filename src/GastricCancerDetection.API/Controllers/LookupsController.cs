using GastricCancerDetection.Infrastructure.Data;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace GastricCancerDetection.API.Controllers;

/// <summary>
/// داده‌های مرجع (Lookup) که برای ساخت فرم‌های آپلود/تحلیل در سمت کلاینت لازم است:
/// پنل‌های ژنی، نسخه‌های مدل ریسک، انواع نمونه و پلتفرم توالی‌یابی.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class LookupsController : ControllerBase
{
    private readonly ApplicationDbContext _db;
    public LookupsController(ApplicationDbContext db) => _db = db;

    [HttpGet("gene-panels")]
    public async Task<IActionResult> GetGenePanels(CancellationToken ct)
    {
        var panels = await _db.GenePanels.AsNoTracking()
            .Where(p => p.IsActive)
            .Select(p => new { p.PanelId, p.PanelName, p.PanelVersion, GeneCount = p.PanelGenes.Count })
            .ToListAsync(ct);
        return Ok(panels);
    }

    [HttpGet("gene-panels/{panelId:int}/genes")]
    public async Task<IActionResult> GetPanelGenes(int panelId, CancellationToken ct)
    {
        var genes = await _db.GenePanelGenes.AsNoTracking()
            .Where(pg => pg.PanelId == panelId)
            .Include(pg => pg.Gene)
            .Select(pg => new { pg.Gene.GeneId, pg.Gene.GeneSymbol, pg.RiskWeight, pg.InheritancePattern })
            .ToListAsync(ct);
        return Ok(genes);
    }

    [HttpGet("risk-model-versions")]
    public async Task<IActionResult> GetRiskModelVersions(CancellationToken ct)
    {
        var versions = await _db.RiskModelVersions.AsNoTracking()
            .Select(v => new { v.ModelVersionId, v.VersionName, v.IsApprovedForUse, v.Description })
            .ToListAsync(ct);
        return Ok(versions);
    }

    [HttpGet("sample-types")]
    public async Task<IActionResult> GetSampleTypes(CancellationToken ct)
        => Ok(await _db.SampleTypes.AsNoTracking().ToListAsync(ct));

    [HttpGet("sequencing-platforms")]
    public async Task<IActionResult> GetSequencingPlatforms(CancellationToken ct)
        => Ok(await _db.SequencingPlatforms.AsNoTracking().ToListAsync(ct));
}
