namespace GastricCancerDetection.Domain.Entities.Ref;

public class ProcessingStatusType
{
    public byte StatusId { get; set; }
    public string StatusName { get; set; } = null!;

    // مقادیر ثابت seed شده در دیتابیس - برای خوانایی کد به‌جای magic number
    public const byte Pending = 1;
    public const byte Processing = 2;
    public const byte Done = 3;
    public const byte Failed = 4;
    public const byte Rejected = 5;
}
