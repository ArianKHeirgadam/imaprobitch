using GastricCancerDetection.Domain.Entities.Ref;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace GastricCancerDetection.Infrastructure.Data.Configurations;

public class RefGenomeBuildConfiguration : IEntityTypeConfiguration<RefGenomeBuild>
{
    public void Configure(EntityTypeBuilder<RefGenomeBuild> b)
    {
        b.ToTable("RefGenomeBuilds", "ref");
        b.HasKey(x => x.BuildId);
    }
}

public class ProcessingStatusTypeConfiguration : IEntityTypeConfiguration<ProcessingStatusType>
{
    public void Configure(EntityTypeBuilder<ProcessingStatusType> b)
    {
        b.ToTable("ProcessingStatusTypes", "ref");
        b.HasKey(x => x.StatusId);
    }
}

public class ZygosityTypeConfiguration : IEntityTypeConfiguration<ZygosityType>
{
    public void Configure(EntityTypeBuilder<ZygosityType> b)
    {
        b.ToTable("ZygosityTypes", "ref");
        b.HasKey(x => x.ZygosityId);
    }
}

public class RiskCategoryTypeConfiguration : IEntityTypeConfiguration<RiskCategoryType>
{
    public void Configure(EntityTypeBuilder<RiskCategoryType> b)
    {
        b.ToTable("RiskCategoryTypes", "ref");
        b.HasKey(x => x.RiskCategoryId);
    }
}

public class ClinicalSignificanceTypeConfiguration : IEntityTypeConfiguration<ClinicalSignificanceType>
{
    public void Configure(EntityTypeBuilder<ClinicalSignificanceType> b)
    {
        b.ToTable("ClinicalSignificanceTypes", "ref");
        b.HasKey(x => x.ClinSigId);
    }
}

public class ConsequenceTypeConfiguration : IEntityTypeConfiguration<ConsequenceType>
{
    public void Configure(EntityTypeBuilder<ConsequenceType> b)
    {
        b.ToTable("ConsequenceTypes", "ref");
        b.HasKey(x => x.ConsequenceId);
    }
}

public class SampleTypeConfiguration : IEntityTypeConfiguration<SampleType>
{
    public void Configure(EntityTypeBuilder<SampleType> b)
    {
        b.ToTable("SampleTypes", "ref");
        b.HasKey(x => x.SampleTypeId);
    }
}

public class SequencingPlatformConfiguration : IEntityTypeConfiguration<SequencingPlatform>
{
    public void Configure(EntityTypeBuilder<SequencingPlatform> b)
    {
        b.ToTable("SequencingPlatforms", "ref");
        b.HasKey(x => x.PlatformId);
    }
}

public class PopulationFrequencySourceConfiguration : IEntityTypeConfiguration<PopulationFrequencySource>
{
    public void Configure(EntityTypeBuilder<PopulationFrequencySource> b)
    {
        b.ToTable("PopulationFrequencySources", "ref");
        b.HasKey(x => x.SourceId);
    }
}
