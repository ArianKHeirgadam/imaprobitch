namespace GastricCancerDetection.Domain.Entities.Sec;

public class AuditLog
{
    public long AuditId { get; set; }
    public int? UserId { get; set; }
    public string ActionType { get; set; } = null!;
    public string? EntityType { get; set; }
    public long? EntityId { get; set; }
    public string? OldValue { get; set; }
    public string? NewValue { get; set; }
    public string? IPAddress { get; set; }
    public DateTime CreatedAt { get; set; }
}
