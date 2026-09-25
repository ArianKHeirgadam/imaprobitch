using GastricCancerDetection.Domain.Entities.Analysis;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace GastricCancerDetection.Infrastructure.Data.Configurations;

public class RiskModelVersionConfiguration : IEntityTypeConfiguration<RiskModelVersion>
{
    public void Configure(EntityTypeBuilder<RiskModelVersion> b)
    {
        b.ToTable("RiskModelVersions", "analysis");
        b.HasKey(x => x.ModelVersionId);
        b.HasIndex(x => x.VersionName).IsUnique();
    }
}

public class AnalysisRunConfiguration : IEntityTypeConfiguration<AnalysisRun>
{
    public void Configure(EntityTypeBuilder<AnalysisRun> b)
    {
        // analysis.AnalysisRuns هم Temporal Table است، مشابه clin.Subjects
        b.ToTable("AnalysisRuns", "analysis");
        b.HasKey(x => x.RunId);
        b.HasOne(x => x.ModelVersion).WithMany().HasForeignKey(x => x.ModelVersionId);
    }
}

public class GeneComparisonResultConfiguration : IEntityTypeConfiguration<GeneComparisonResult>
{
    public void Configure(EntityTypeBuilder<GeneComparisonResult> b)
    {
        b.ToTable("GeneComparisonResults", "analysis");
        b.HasKey(x => x.ResultId);
        b.HasIndex(x => new { x.RunId, x.GeneId }).IsUnique();
        b.HasOne<AnalysisRun>().WithMany(r => r.GeneResults).HasForeignKey(x => x.RunId);
    }
}

public class SubjectRiskResultConfiguration : IEntityTypeConfiguration<SubjectRiskResult>
{
    public void Configure(EntityTypeBuilder<SubjectRiskResult> b)
    {
        b.ToTable("SubjectRiskResults", "analysis");
        b.HasKey(x => x.ResultId);
        b.HasIndex(x => new { x.RunId, x.SubjectId }).IsUnique();
        b.HasOne<AnalysisRun>().WithMany(r => r.SubjectResults).HasForeignKey(x => x.RunId);
    }
}

public class GeneratedReportConfiguration : IEntityTypeConfiguration<GeneratedReport>
{
    public void Configure(EntityTypeBuilder<GeneratedReport> b)
    {
        b.ToTable("GeneratedReports", "analysis");
        b.HasKey(x => x.ReportId);
    }
}
