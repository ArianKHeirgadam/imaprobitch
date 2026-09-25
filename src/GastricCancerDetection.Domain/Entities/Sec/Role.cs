namespace GastricCancerDetection.Domain.Entities.Sec;

public class Role
{
    public int RoleId { get; set; }
    public string RoleName { get; set; } = null!;
    public ICollection<User> Users { get; set; } = new List<User>();
}
