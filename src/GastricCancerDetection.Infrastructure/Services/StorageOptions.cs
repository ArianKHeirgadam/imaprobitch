namespace GastricCancerDetection.Infrastructure.Services;

/// <summary>از appsettings.json (بخش "Storage") خوانده می‌شود</summary>
public class StorageOptions
{
    public string GenomeFilesRoot { get; set; } = "Storage/GenomeFiles";
    public string ReportsRoot { get; set; } = "Storage/Reports";
    public string PythonExecutablePath { get; set; } = "python";
    public string PythonScriptPath { get; set; } = "PythonScripts/analyze_vcf.py";
}
