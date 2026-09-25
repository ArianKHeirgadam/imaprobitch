using GastricCancerDetection.Domain.Entities.Cfg;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace GastricCancerDetection.Infrastructure.Data.Configurations;

public class SystemSettingConfiguration : IEntityTypeConfiguration<SystemSetting>
{
    public void Configure(EntityTypeBuilder<SystemSetting> b)
    {
        b.ToTable("SystemSettings", "cfg");
        b.HasKey(x => x.SettingKey);
    }
}
