using GastricCancerDetection.Domain.Entities.Sec;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace GastricCancerDetection.Infrastructure.Data.Configurations;

public class UserConfiguration : IEntityTypeConfiguration<User>
{
    public void Configure(EntityTypeBuilder<User> b)
    {
        b.ToTable("Users", "sec");
        b.HasKey(x => x.UserId);
        b.Property(x => x.Email).HasMaxLength(200).IsRequired();
        b.HasIndex(x => x.Email).IsUnique();
        b.HasOne(x => x.Role).WithMany(r => r.Users).HasForeignKey(x => x.RoleId);
    }
}

public class RoleConfiguration : IEntityTypeConfiguration<Role>
{
    public void Configure(EntityTypeBuilder<Role> b)
    {
        b.ToTable("Roles", "sec");
        b.HasKey(x => x.RoleId);
        b.HasIndex(x => x.RoleName).IsUnique();
    }
}

public class PermissionConfiguration : IEntityTypeConfiguration<Permission>
{
    public void Configure(EntityTypeBuilder<Permission> b)
    {
        b.ToTable("Permissions", "sec");
        b.HasKey(x => x.PermissionId);
    }
}

public class RolePermissionConfiguration : IEntityTypeConfiguration<RolePermission>
{
    public void Configure(EntityTypeBuilder<RolePermission> b)
    {
        b.ToTable("RolePermissions", "sec");
        b.HasKey(x => new { x.RoleId, x.PermissionId });
    }
}

public class AuditLogConfiguration : IEntityTypeConfiguration<AuditLog>
{
    public void Configure(EntityTypeBuilder<AuditLog> b)
    {
        b.ToTable("AuditLog", "sec");
        b.HasKey(x => x.AuditId);
    }
}
