using GastricCancerDetection.Application.DTOs;
using Microsoft.Extensions.Logging;
using GastricCancerDetection.Application.Interfaces;
using GastricCancerDetection.Domain.Entities.Analysis;
using GastricCancerDetection.Domain.Entities.Geno;
using GastricCancerDetection.Domain.Entities.Ref;
using GastricCancerDetection.Infrastructure.Data;
using GastricCancerDetection.Infrastructure.Services.Statistics;
using Microsoft.EntityFrameworkCore;

namespace GastricCancerDetection.Infrastructure.Services;

public class AnalysisService : IAnalysisService
{
    private readonly ApplicationDbContext _db;
    private readonly IPythonRunnerService _pythonRunner;
    private readonly ILogger<AnalysisService> _logger;

    public AnalysisService(ApplicationDbContext db, IPythonRunnerService pythonRunner, ILogger<AnalysisService> logger)
    {
        _db = db;
        _pythonRunner = pythonRunner;
        _logger = logger;
    }

    public async Task<AnalysisRunResultDto> RunAnalysisAsync(AnalysisRunRequestDto request, CancellationToken ct = default)
    {
        var model = await _db.RiskModelVersions.FirstOrDefaultAsync(x => x.ModelVersionId == request.ModelVersionId, ct)
            ?? throw new InvalidOperationException("نسخه‌ی مدل ریسک پیدا نشد.");

        if (!model.IsApprovedForUse)
            _logger.LogWarning("اجرای تحلیل با مدل تأییدنشده {Version} - فقط برای تست/پژوهش مناسب است.", model.VersionName);

        var panelGenes = await _db.GenePanelGenes.AsNoTracking()
            .Where(x => x.PanelId == request.PanelId)
            .Include(x => x.Gene)
            .ToListAsync(ct);

        if (panelGenes.Count == 0)
            throw new InvalidOperationException("پنل ژنی انتخاب‌شده هیچ ژنی ندارد.");

        var geneSymbols = panelGenes.Select(x => x.Gene.GeneSymbol).Distinct().ToList();

        // مرحله ۱: استخراج واریانت از فایل‌های Pending با اجرای اسکریپت Python
        await ExtractPendingFilesAsync(geneSymbols, ct);

        // مرحله ۲: جمع‌آوری افرادی که حداقل یک فایل با وضعیت Done دارند
        // عمداً این مرحله را به چند کوئری ساده می‌شکنیم (به‌جای یک زنجیره‌ی پیچیده‌ی
        // Join/Distinct/Join) تا خطر عدم ترجمه‌ی صحیح LINQ به SQL توسط EF Core را کم کنیم؛
        // حجم داده‌ی این پروژه (تعداد افراد) کوچک است، پس چند رفت‌وبرگشت اضافه به دیتابیس مشکلی ایجاد نمی‌کند.
        var doneStatusId = ProcessingStatusType.Done;

        var doneSampleIds = await _db.GenomeFiles.AsNoTracking()
            .Where(f => f.StatusId == doneStatusId)
            .Select(f => f.SampleId)
            .Distinct()
            .ToListAsync(ct);

        var relevantSamples = await _db.Samples.AsNoTracking()
            .Where(s => doneSampleIds.Contains(s.SampleId))
            .Select(s => new { s.SampleId, s.SubjectId })
            .ToListAsync(ct);

        var subjectIdsWithData = relevantSamples.Select(s => s.SubjectId).Distinct().ToList();

        var subjectsWithData = await _db.Subjects.AsNoTracking()
            .Where(s => subjectIdsWithData.Contains(s.SubjectId))
            .Select(s => new { s.SubjectId, s.SubjectCode, s.IsHealthy })
            .ToListAsync(ct);

        var healthyCount = subjectsWithData.Count(x => x.IsHealthy);
        var unhealthyCount = subjectsWithData.Count(x => !x.IsHealthy);

        if (healthyCount == 0 || unhealthyCount == 0)
            throw new InvalidOperationException("برای مقایسه‌ی آماری حداقل به یک فرد سالم و یک فرد ناسالم با فایل پردازش‌شده نیاز است.");

        // نگاشت: هر فرد -> مجموعه‌ی GeneId هایی که حداقل یک واریانت در آن‌ها دارد
        var geneIdsInPanel = panelGenes.Select(x => x.GeneId).ToHashSet();
        var sampleToSubjectMap = relevantSamples.ToDictionary(s => s.SampleId, s => s.SubjectId);

        var extractedRows = await _db.ExtractedVariants.AsNoTracking()
            .Where(ev => ev.GenomeFile!.StatusId == doneStatusId)
            .Select(ev => new { ev.GenomeFile!.SampleId, ev.VariantCatalog.GeneId })
            .ToListAsync(ct);

        var subjectGeneMap = new Dictionary<int, HashSet<int>>();
        foreach (var row in extractedRows)
        {
            if (row.GeneId is null || !geneIdsInPanel.Contains(row.GeneId.Value)) continue;
            if (!sampleToSubjectMap.TryGetValue(row.SampleId, out var subjectId)) continue;

            if (!subjectGeneMap.TryGetValue(subjectId, out var set))
            {
                set = new HashSet<int>();
                subjectGeneMap[subjectId] = set;
            }
            set.Add(row.GeneId.Value);
        }

        // مرحله ۳: ساخت رکورد AnalysisRun
        var run = new AnalysisRun
        {
            PanelId = request.PanelId,
            ModelVersionId = request.ModelVersionId,
            TriggeredByUserId = request.TriggeredByUserId,
            HealthyCount = healthyCount,
            UnhealthyCount = unhealthyCount,
            StatusId = ProcessingStatusType.Processing,
            PipelineVersion = "1.0"
        };
        _db.AnalysisRuns.Add(run);
        await _db.SaveChangesAsync(ct);

        // مرحله ۴: مقایسه‌ی آماری ژن‌به‌ژن با آزمون دقیق فیشر
        var geneResults = new List<GeneComparisonResult>();
        var geneRiskScoreMap = new Dictionary<int, double>();

        foreach (var pg in panelGenes)
        {
            int unhealthyWithVariant = subjectsWithData.Count(s => !s.IsHealthy && subjectGeneMap.TryGetValue(s.SubjectId, out var g) && g.Contains(pg.GeneId));
            int unhealthyWithoutVariant = unhealthyCount - unhealthyWithVariant;
            int healthyWithVariant = subjectsWithData.Count(s => s.IsHealthy && subjectGeneMap.TryGetValue(s.SubjectId, out var g) && g.Contains(pg.GeneId));
            int healthyWithoutVariant = healthyCount - healthyWithVariant;

            double healthyFreq = healthyCount == 0 ? 0 : (double)healthyWithVariant / healthyCount;
            double unhealthyFreq = unhealthyCount == 0 ? 0 : (double)unhealthyWithVariant / unhealthyCount;

            double pValue = FisherExactTest.TwoTailedPValue(unhealthyWithVariant, unhealthyWithoutVariant, healthyWithVariant, healthyWithoutVariant);
            double oddsRatio = FisherExactTest.OddsRatio(unhealthyWithVariant, unhealthyWithoutVariant, healthyWithVariant, healthyWithoutVariant);

            // مدل امتیازدهی v1.0: تفاضل فراوانی وزن‌دار (فقط وقتی فراوانی در گروه ناسالم بیشتر باشد)
            double geneRiskScore = pg.RiskWeight * Math.Max(0.0, unhealthyFreq - healthyFreq);
            geneRiskScoreMap[pg.GeneId] = geneRiskScore;

            geneResults.Add(new GeneComparisonResult
            {
                RunId = run.RunId,
                GeneId = pg.GeneId,
                HealthyVariantFreq = healthyFreq,
                UnhealthyVariantFreq = unhealthyFreq,
                PValue = pValue,
                OddsRatio = oddsRatio,
                GeneRiskScore = geneRiskScore
            });
        }
        _db.GeneComparisonResults.AddRange(geneResults);

        // مرحله ۵: امتیاز ریسک نهایی هر فرد = مجموع امتیاز ژن‌هایی که واریانت دارد
        var riskCategories = await _db.RiskCategoryTypes.AsNoTracking().OrderBy(x => x.MinScore).ToListAsync(ct);
        var geneSymbolById = panelGenes.ToDictionary(x => x.GeneId, x => x.Gene.GeneSymbol);

        var subjectResults = new List<SubjectRiskResult>();
        foreach (var s in subjectsWithData)
        {
            subjectGeneMap.TryGetValue(s.SubjectId, out var genesPresent);
            genesPresent ??= new HashSet<int>();

            double total = genesPresent.Sum(geneId => geneRiskScoreMap.GetValueOrDefault(geneId, 0.0));
            var category = riskCategories.LastOrDefault(c => total >= c.MinScore) ?? riskCategories.First();
            var contributingGenes = string.Join(", ", genesPresent.Select(g => geneSymbolById.GetValueOrDefault(g, "?")));

            subjectResults.Add(new SubjectRiskResult
            {
                RunId = run.RunId,
                SubjectId = s.SubjectId,
                TotalRiskScore = total,
                RiskCategoryId = category.RiskCategoryId,
                ContributingGenes = contributingGenes
            });
        }
        _db.SubjectRiskResults.AddRange(subjectResults);

        run.StatusId = ProcessingStatusType.Done;
        await _db.SaveChangesAsync(ct);

        return (await GetRunResultAsync(run.RunId, ct))!;
    }

    private async Task ExtractPendingFilesAsync(List<string> targetGeneSymbols, CancellationToken ct)
    {
        var pendingFiles = await _db.GenomeFiles
            .Where(f => f.StatusId == ProcessingStatusType.Pending)
            .ToListAsync(ct);

        if (pendingFiles.Count == 0) return;

        var genesInDb = await _db.Genes.AsNoTracking()
            .Where(g => targetGeneSymbols.Contains(g.GeneSymbol))
            .ToDictionaryAsync(g => g.GeneSymbol, g => g.GeneId, ct);

        var zygosityLookup = await _db.ZygosityTypes.AsNoTracking()
            .ToDictionaryAsync(z => z.ZygosityName, z => z.ZygosityId, ct);

        var defaultBuildId = await _db.RefGenomeBuilds.AsNoTracking()
            .Where(b => b.IsDefault).Select(b => b.BuildId).FirstOrDefaultAsync(ct);
        if (defaultBuildId == 0) defaultBuildId = 1;

        foreach (var file in pendingFiles)
        {
            try
            {
                file.StatusId = ProcessingStatusType.Processing;
                await _db.SaveChangesAsync(ct);

                var rawVariants = await _pythonRunner.ExtractVariantsAsync(file.FilePath, targetGeneSymbols, ct);

                foreach (var raw in rawVariants)
                {
                    int? geneId = raw.GeneSymbol is not null && genesInDb.TryGetValue(raw.GeneSymbol, out var gId) ? gId : null;

                    var existing = await _db.VariantCatalog.FirstOrDefaultAsync(v =>
                        v.BuildId == defaultBuildId && v.Chromosome == raw.Chromosome &&
                        v.Position == raw.Position && v.RefAllele == raw.RefAllele && v.AltAllele == raw.AltAllele, ct);

                    if (existing is null)
                    {
                        existing = new VariantCatalog
                        {
                            BuildId = defaultBuildId,
                            Chromosome = raw.Chromosome,
                            Position = raw.Position,
                            RefAllele = raw.RefAllele,
                            AltAllele = raw.AltAllele,
                            GeneId = geneId
                        };
                        _db.VariantCatalog.Add(existing);
                        await _db.SaveChangesAsync(ct); // برای گرفتن VariantCatalogId جدید (Identity)
                    }

                    var alreadyLinked = await _db.ExtractedVariants.AnyAsync(ev =>
                        ev.FileId == file.FileId && ev.VariantCatalogId == existing.VariantCatalogId, ct);
                    if (alreadyLinked) continue;

                    var zygosityId = zygosityLookup.GetValueOrDefault(raw.Zygosity, zygosityLookup.GetValueOrDefault("Unknown", (byte)4));

                    _db.ExtractedVariants.Add(new ExtractedVariant
                    {
                        FileId = file.FileId,
                        VariantCatalogId = existing.VariantCatalogId,
                        ZygosityId = zygosityId,
                        Quality = raw.Quality,
                        ReadDepth = raw.ReadDepth,
                        AlleleFraction = raw.AlleleFraction
                    });
                }

                file.StatusId = ProcessingStatusType.Done;
                file.ProcessedAt = DateTime.UtcNow;
                await _db.SaveChangesAsync(ct);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "پردازش فایل {FileId} شکست خورد", file.FileId);
                file.StatusId = ProcessingStatusType.Failed;
                file.ErrorMessage = ex.Message;
                await _db.SaveChangesAsync(ct);
            }
        }
    }

    public async Task<AnalysisRunResultDto?> GetRunResultAsync(int runId, CancellationToken ct = default)
    {
        var run = await _db.AnalysisRuns.AsNoTracking().FirstOrDefaultAsync(x => x.RunId == runId, ct);
        if (run is null) return null;

        var geneResults = await _db.GeneComparisonResults.AsNoTracking()
            .Where(x => x.RunId == runId)
            .Join(_db.Genes.AsNoTracking(), r => r.GeneId, g => g.GeneId, (r, g) => new GeneComparisonResultDto(
                g.GeneSymbol, r.HealthyVariantFreq, r.UnhealthyVariantFreq, r.PValue, r.OddsRatio, r.GeneRiskScore))
            .ToListAsync(ct);

        var subjectResults = await (
            from r in _db.SubjectRiskResults.AsNoTracking()
            where r.RunId == runId
            join s in _db.Subjects.AsNoTracking() on r.SubjectId equals s.SubjectId
            join c in _db.RiskCategoryTypes.AsNoTracking() on r.RiskCategoryId equals c.RiskCategoryId
            orderby r.TotalRiskScore descending
            select new SubjectRiskResultDto(s.SubjectId, s.SubjectCode, s.IsHealthy, r.TotalRiskScore, c.CategoryName, r.ContributingGenes)
        ).ToListAsync(ct);

        var statusName = run.StatusId switch
        {
            ProcessingStatusType.Pending => "Pending",
            ProcessingStatusType.Processing => "Processing",
            ProcessingStatusType.Done => "Done",
            ProcessingStatusType.Failed => "Failed",
            _ => "Unknown"
        };

        return new AnalysisRunResultDto(run.RunId, run.RunDate, run.HealthyCount, run.UnhealthyCount, statusName, geneResults, subjectResults);
    }

    public async Task<List<AnalysisRunResultDto>> GetAllRunsAsync(CancellationToken ct = default)
    {
        var runIds = await _db.AnalysisRuns.AsNoTracking().OrderByDescending(x => x.RunId).Select(x => x.RunId).ToListAsync(ct);
        var results = new List<AnalysisRunResultDto>();
        foreach (var id in runIds)
        {
            var r = await GetRunResultAsync(id, ct);
            if (r is not null) results.Add(r);
        }
        return results;
    }
}
