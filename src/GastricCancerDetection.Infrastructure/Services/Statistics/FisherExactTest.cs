namespace GastricCancerDetection.Infrastructure.Services.Statistics;

/// <summary>
/// پیاده‌سازی آزمون دقیق فیشر (Fisher's Exact Test) دوطرفه برای جدول ۲×۲،
/// بدون وابستگی به کتابخانه‌ی خارجی آماری. برای مقایسه‌ی فراوانی جهش بین
/// گروه سالم و ناسالم استفاده می‌شود.
///
///                 دارای جهش      فاقد جهش
///   ناسالم            a              b
///   سالم              c              d
/// </summary>
public static class FisherExactTest
{
    public static double TwoTailedPValue(int a, int b, int c, int d)
    {
        int row1 = a + b, row2 = c + d, col1 = a + c, col2 = b + d, total = row1 + row2;
        if (total == 0) return 1.0;

        double observed = HypergeometricProbability(a, row1, col1, total);
        double pValue = 0.0;

        int minA = Math.Max(0, col1 - row2);
        int maxA = Math.Min(row1, col1);

        // جمع احتمال تمام جدول‌های ۲×۲ ممکن (با همان مجموع سطر/ستون) که احتمالشان
        // مساوی یا کمتر از جدول مشاهده‌شده است - تعریف استاندارد آزمون دوطرفه‌ی فیشر
        for (int x = minA; x <= maxA; x++)
        {
            double p = HypergeometricProbability(x, row1, col1, total);
            if (p <= observed * 1.0000001)
                pValue += p;
        }

        return Math.Clamp(pValue, 0.0, 1.0);
    }

    public static double OddsRatio(int a, int b, int c, int d)
    {
        // اصلاح Haldane-Anscombe برای جلوگیری از تقسیم بر صفر وقتی یکی از سلول‌ها صفر است
        if (b == 0 || c == 0 || a == 0 || d == 0)
            return ((a + 0.5) * (d + 0.5)) / ((b + 0.5) * (c + 0.5));
        return (double)(a * d) / (b * c);
    }

    private static double HypergeometricProbability(int a, int row1, int col1, int total)
    {
        int b = row1 - a;
        int row2 = total - row1;
        int c = col1 - a;
        int d = row2 - c;
        if (a < 0 || b < 0 || c < 0 || d < 0) return 0.0;

        double logP = LogFactorial(row1) + LogFactorial(row2) + LogFactorial(col1) + LogFactorial(total - col1)
                    - LogFactorial(total) - LogFactorial(a) - LogFactorial(b) - LogFactorial(c) - LogFactorial(d);
        return Math.Exp(logP);
    }

    private static readonly Dictionary<int, double> _logFactorialCache = new();

    private static double LogFactorial(int n)
    {
        if (n <= 1) return 0.0;
        if (_logFactorialCache.TryGetValue(n, out var cached)) return cached;

        double result = 0.0;
        for (int i = 2; i <= n; i++) result += Math.Log(i);
        _logFactorialCache[n] = result;
        return result;
    }
}
