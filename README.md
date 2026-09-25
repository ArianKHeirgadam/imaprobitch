# سیستم غربالگری ریسک زودهنگام سرطان معده — بک‌اند .NET 8

این پروژه بک‌اند (Web API) سیستم غربالگری ریسک ژنومی سرطان معده است که روی دیتابیس
Enterprise-Grade ساخته‌شده در گفتگوی قبلی (`gastriccancerdb`) کار می‌کند.

## معماری منتخب

معماری لایه‌ای (Layered / Clean-ish) در ۴ پروژه، هرکدام مسئولیت مشخص:

```
GastricCancerDetection.Domain          <- Entityهای خام، بدون هیچ وابستگی (POCO)
GastricCancerDetection.Application     <- DTOها + Interface سرویس‌ها (قرارداد)
GastricCancerDetection.Infrastructure  <- DbContext (EF Core)، پیاده‌سازی سرویس‌ها،
                                           اجرای Python، تولید گزارش (ClosedXML/QuestPDF)
GastricCancerDetection.API             <- ASP.NET Core Web API، فقط Controllerها
```

جهت وابستگی: `API -> Infrastructure -> Application -> Domain` (هیچ‌کدام برعکس آن رفرنس نمی‌گیرند).

چرا این معماری؟ چون منطق تحلیل آماری و تولید گزارش نباید داخل Controller باشد (برای
تست‌پذیری و خوانایی)، و چون DbContext باید فقط در یک لایه (Infrastructure) بماند تا
لایه‌های بالاتر به EF Core وابسته نباشند.

## نکته‌ی مهم: معماری Database-First

دیتابیس از قبل با اسکریپت SQL جداگانه (`01_schema_enterprise_final.sql`) ساخته شده.
این پروژه **هیچ Migration اجرا نمی‌کند** — `ApplicationDbContext` فقط روی جدول‌های
موجود Map می‌شود (نگاه کنید به `Infrastructure/Data/Configurations/`). یعنی وقتی شما
از Server Explorer در Visual Studio به `gastriccancerdb` وصل می‌شوید، فقط برای
مرور/مدیریت دستی دیتابیس است؛ خود برنامه از طریق Connection String در
`appsettings.json` وصل می‌شود — **این رشته‌ی اتصال را با همان چیزی که در Server
Explorer ست کردید هماهنگ کنید**:

```json
"ConnectionStrings": {
  "DefaultConnection": "Server=localhost\\SQLEXPRESS;Database=gastriccancerdb;Trusted_Connection=True;TrustServerCertificate=True;"
}
```

## جریان کار (Workflow)

1. **ثبت افراد** — `POST /api/subjects` (سالم/ناسالم + اطلاعات بالینی)
2. **ثبت نمونه** — `POST /api/samples` (برای هر فرد، یک یا چند نمونه)
3. **آپلود فایل VCF** — `POST /api/genomefiles/upload` (multipart/form-data: sampleId + file)
   فایل روی دیسک ذخیره و رکورد آن با وضعیت `Pending` ثبت می‌شود.
4. **اجرای تحلیل** — `POST /api/analysis/run` با بدنه‌ی `{ panelId, modelVersionId }`
   - تمام فایل‌های `Pending` را با اجرای اسکریپت Python (`analyze_vcf.py` به‌صورت Process)
     پردازش می‌کند و واریانت‌های داخل ژن‌های پنل را استخراج می‌کند.
   - سپس فراوانی هر ژن را بین گروه سالم/ناسالم با **آزمون دقیق فیشر** مقایسه می‌کند.
   - امتیاز ریسک هر فرد را بر اساس ژن‌های دارای جهش محاسبه می‌کند.
   - نتایج در `analysis.GeneComparisonResults` و `analysis.SubjectRiskResults` ذخیره می‌شود.
5. **دریافت نتایج** — `GET /api/analysis/runs/{runId}`
6. **تولید و دانلود گزارش** —
   `POST /api/reports/generate/{runId}?format=Excel` یا `?format=PDF`
   سپس `GET /api/reports/download/{reportId}`

برای دیدن لیست پنل‌ها/ژن‌ها/نسخه‌های مدل قبل از اجرای تحلیل: `GET /api/lookups/...`

## پایتون و دات‌نت چطور به هم وصل‌اند؟

با شبکه وصل نمی‌شوند. `PythonRunnerService.cs` اسکریپت `PythonScripts/analyze_vcf.py`
را مثل یک برنامه‌ی خط‌فرمان با `Process` اجرا می‌کند و خروجی JSON آن را از stdout
می‌خواند. مسیر Python و اسکریپت در `appsettings.json` → بخش `Storage` قابل تنظیم است.
این اسکریپت فقط از کتابخانه‌ی استاندارد پایتون استفاده می‌کند (بدون pysam/cyvcf2) تا
بدون نصب پیش‌نیاز خاصی روی هر سیستمی اجرا شود؛ فایل‌های تست نمونه در `SampleData/` هست.

## اجرا در Visual Studio

1. `GastricCancerDetection.sln` را باز کنید.
2. `appsettings.json` (پروژه‌ی API) را طبق اتصال SQL Server خودتان ویرایش کنید.
3. پروژه‌ی API را به‌عنوان Startup Project تنظیم و اجرا کنید (F5) — Swagger روی
   `https://localhost:xxxx/swagger` بالا می‌آید.
4. Python 3.10+ باید روی سیستم نصب باشد و در PATH قابل‌دسترس باشد (یا مسیر کامل را
   در `Storage:PythonExecutablePath` بدهید).

## نکته‌ی صادقانه برای دفاع پروژه

مدل امتیازدهی فعلی (`v1.0` در `analysis.RiskModelVersions`) ساده و شفاف است: تفاضل
فراوانی وزن‌دار بین دو گروه + آزمون فیشر برای معناداری آماری. برای تبدیل واقعی به
کیت تشخیصی، این بخش باید توسط متخصص ژنتیک/بایوانفورماتیک اعتبارسنجی و در صورت نیاز
با مدل‌های پیچیده‌تر (مثل رگرسیون لجستیک چندمتغیره یا Polygenic Risk Score) جایگزین
شود؛ ساختار دیتابیس و کد از قبل برای این تغییر آماده است (`RiskModelVersions` دقیقاً
برای همین منظور نسخه‌بندی شده).
