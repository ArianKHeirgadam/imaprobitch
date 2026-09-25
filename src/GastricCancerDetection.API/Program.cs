using GastricCancerDetection.Application.Interfaces;
using GastricCancerDetection.Infrastructure.Data;
using GastricCancerDetection.Infrastructure.Services;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// ---------- سرویس‌ها ----------
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo
    {
        Title = "Gastric Cancer Early Detection API",
        Version = "v1",
        Description = "سیستم غربالگری ریسک زودهنگام سرطان معده بر پایه‌ی مقایسه‌ی ژنومی"
    });
});

// دیتابیس - معماری Database-First روی اسکیمای Enterprise که با SQL جداگانه ساخته شده
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection"),
        sql => sql.EnableRetryOnFailure(3)));

builder.Services.Configure<StorageOptions>(builder.Configuration.GetSection("Storage"));

builder.Services.AddScoped<ISubjectService, SubjectService>();
builder.Services.AddScoped<ISampleService, SampleService>();
builder.Services.AddScoped<IGenomeFileService, GenomeFileService>();
builder.Services.AddScoped<IPythonRunnerService, PythonRunnerService>();
builder.Services.AddScoped<IAnalysisService, AnalysisService>();
builder.Services.AddScoped<IReportService, ReportGenerationService>();

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy => policy.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod());
});

var app = builder.Build();

// ---------- Pipeline ----------
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors();
app.UseAuthorization();
app.MapControllers();

app.Run();
