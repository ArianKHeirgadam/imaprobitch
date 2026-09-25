namespace GastricCancerDetection.Domain.Entities.Cfg;

public class SystemSetting
{
    public string SettingKey { get; set; } = null!;
    public string SettingValue { get; set; } = null!;
    public string? Description { get; set; }
    public int? UpdatedByUserId { get; set; }
    public DateTime UpdatedAt { get; set; }
}
