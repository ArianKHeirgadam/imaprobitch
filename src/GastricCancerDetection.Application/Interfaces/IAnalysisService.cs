using GastricCancerDetection.Application.DTOs;

namespace GastricCancerDetection.Application.Interfaces;

public interface IAnalysisService
{
    /// <summary>
    /// یک اجرای کامل تحلیل را روی تمام فایل‌های Pending متعلق به پنل مشخص‌شده انجام می‌دهد:
    /// استخراج واریانت (Python) -> ثبت در کاتالوگ -> مقایسه‌ی آماری بین گروه سالم/ناسالم (Fisher's Exact Test)
    /// -> محاسبه‌ی امتیاز ریسک هر فرد -> ذخیره‌ی نتایج.
    /// </summary>
    Task<AnalysisRunResultDto> RunAnalysisAsync(AnalysisRunRequestDto request, CancellationToken ct = default);
    Task<AnalysisRunResultDto?> GetRunResultAsync(int runId, CancellationToken ct = default);
    Task<List<AnalysisRunResultDto>> GetAllRunsAsync(CancellationToken ct = default);
}
