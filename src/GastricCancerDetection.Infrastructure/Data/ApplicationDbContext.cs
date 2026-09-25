using GastricCancerDetection.Domain.Entities.Analysis;
using GastricCancerDetection.Domain.Entities.Cfg;
using GastricCancerDetection.Domain.Entities.Clin;
using GastricCancerDetection.Domain.Entities.Geno;
using GastricCancerDetection.Domain.Entities.Ref;
using GastricCancerDetection.Domain.Entities.Sec;
using Microsoft.EntityFrameworkCore;

namespace GastricCancerDetection.Infrastructure.Data;

/// <summary>
/// DbContext با معماری Database-First: دیتابیس از قبل با اسکریپت SQL (Enterprise Schema)
/// ساخته شده و اینجا فقط روی همون ساختار Map می‌کنیم. به همین دلیل Migration اجرا نمی‌کنیم
/// و در Program.cs هم EnsureCreated/Migrate صدا زده نمی‌شود.
/// </summary>
public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : base(options) { }

    // sec
    public DbSet<User> Users => Set<User>();
    public DbSet<Role> Roles => Set<Role>();
    public DbSet<Permission> Permissions => Set<Permission>();
    public DbSet<RolePermission> RolePermissions => Set<RolePermission>();
    public DbSet<AuditLog> AuditLogs => Set<AuditLog>();

    // ref
    public DbSet<RefGenomeBuild> RefGenomeBuilds => Set<RefGenomeBuild>();
    public DbSet<ProcessingStatusType> ProcessingStatusTypes => Set<ProcessingStatusType>();
    public DbSet<ZygosityType> ZygosityTypes => Set<ZygosityType>();
    public DbSet<RiskCategoryType> RiskCategoryTypes => Set<RiskCategoryType>();
    public DbSet<ClinicalSignificanceType> ClinicalSignificanceTypes => Set<ClinicalSignificanceType>();
    public DbSet<ConsequenceType> ConsequenceTypes => Set<ConsequenceType>();
    public DbSet<SampleType> SampleTypes => Set<SampleType>();
    public DbSet<SequencingPlatform> SequencingPlatforms => Set<SequencingPlatform>();
    public DbSet<PopulationFrequencySource> PopulationFrequencySources => Set<PopulationFrequencySource>();

    // clin
    public DbSet<Institution> Institutions => Set<Institution>();
    public DbSet<Subject> Subjects => Set<Subject>();
    public DbSet<FamilyRelation> FamilyRelations => Set<FamilyRelation>();
    public DbSet<HPOTerm> HPOTerms => Set<HPOTerm>();
    public DbSet<SubjectPhenotype> SubjectPhenotypes => Set<SubjectPhenotype>();
    public DbSet<ConsentRecord> ConsentRecords => Set<ConsentRecord>();
    public DbSet<Sample> Samples => Set<Sample>();

    // geno
    public DbSet<Gene> Genes => Set<Gene>();
    public DbSet<Transcript> Transcripts => Set<Transcript>();
    public DbSet<GenePanel> GenePanels => Set<GenePanel>();
    public DbSet<GenePanelGene> GenePanelGenes => Set<GenePanelGene>();
    public DbSet<SequencingRun> SequencingRuns => Set<SequencingRun>();
    public DbSet<GenomeFile> GenomeFiles => Set<GenomeFile>();
    public DbSet<VariantCatalog> VariantCatalog => Set<VariantCatalog>();
    public DbSet<VariantPopulationFrequency> VariantPopulationFrequencies => Set<VariantPopulationFrequency>();
    public DbSet<StructuralVariantCatalog> StructuralVariantCatalog => Set<StructuralVariantCatalog>();
    public DbSet<ExtractedVariant> ExtractedVariants => Set<ExtractedVariant>();
    public DbSet<ExtractedStructuralVariant> ExtractedStructuralVariants => Set<ExtractedStructuralVariant>();

    // analysis
    public DbSet<RiskModelVersion> RiskModelVersions => Set<RiskModelVersion>();
    public DbSet<AnalysisRun> AnalysisRuns => Set<AnalysisRun>();
    public DbSet<GeneComparisonResult> GeneComparisonResults => Set<GeneComparisonResult>();
    public DbSet<SubjectRiskResult> SubjectRiskResults => Set<SubjectRiskResult>();
    public DbSet<GeneratedReport> GeneratedReports => Set<GeneratedReport>();

    // cfg
    public DbSet<SystemSetting> SystemSettings => Set<SystemSetting>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);
        base.OnModelCreating(modelBuilder);
    }
}
