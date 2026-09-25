using GastricCancerDetection.Domain.Entities.Clin;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace GastricCancerDetection.Infrastructure.Data.Configurations;

public class InstitutionConfiguration : IEntityTypeConfiguration<Institution>
{
    public void Configure(EntityTypeBuilder<Institution> b)
    {
        b.ToTable("Institutions", "clin");
        b.HasKey(x => x.InstitutionId);
    }
}

public class SubjectConfiguration : IEntityTypeConfiguration<Subject>
{
    public void Configure(EntityTypeBuilder<Subject> b)
    {
        // clin.Subjects یک Temporal Table است (System-Versioned)؛ ستون‌های ValidFrom/ValidTo
        // را عمداً در Entity نیاورده‌ایم چون SQL Server خودش این‌ها را مدیریت می‌کند
        // و تاریخچه‌ی کامل تغییرات در clin.Subjects_History نگه داشته می‌شود.
        b.ToTable("Subjects", "clin");
        b.HasKey(x => x.SubjectId);
        b.Property(x => x.SubjectCode).HasMaxLength(50).IsRequired();
        b.HasIndex(x => x.SubjectCode).IsUnique();
        b.HasOne(x => x.Institution).WithMany().HasForeignKey(x => x.InstitutionId);
        b.HasQueryFilter(x => !x.IsDeleted); // Soft delete خودکار در تمام کوئری‌ها اعمال می‌شود
    }
}

public class FamilyRelationConfiguration : IEntityTypeConfiguration<FamilyRelation>
{
    public void Configure(EntityTypeBuilder<FamilyRelation> b)
    {
        b.ToTable("FamilyRelations", "clin");
        b.HasKey(x => x.RelationId);
        b.HasOne<Subject>().WithMany().HasForeignKey(x => x.SubjectId).OnDelete(DeleteBehavior.NoAction);
        b.HasOne<Subject>().WithMany().HasForeignKey(x => x.RelativeSubjectId).OnDelete(DeleteBehavior.NoAction);
    }
}

public class HPOTermConfiguration : IEntityTypeConfiguration<HPOTerm>
{
    public void Configure(EntityTypeBuilder<HPOTerm> b)
    {
        b.ToTable("HPOTerms", "clin");
        b.HasKey(x => x.HPOTermId);
    }
}

public class SubjectPhenotypeConfiguration : IEntityTypeConfiguration<SubjectPhenotype>
{
    public void Configure(EntityTypeBuilder<SubjectPhenotype> b)
    {
        b.ToTable("SubjectPhenotypes", "clin");
        b.HasKey(x => new { x.SubjectId, x.HPOTermId });
    }
}

public class ConsentRecordConfiguration : IEntityTypeConfiguration<ConsentRecord>
{
    public void Configure(EntityTypeBuilder<ConsentRecord> b)
    {
        b.ToTable("ConsentRecords", "clin");
        b.HasKey(x => x.ConsentId);
    }
}

public class SampleConfiguration : IEntityTypeConfiguration<Sample>
{
    public void Configure(EntityTypeBuilder<Sample> b)
    {
        b.ToTable("Samples", "clin");
        b.HasKey(x => x.SampleId);
        b.Property(x => x.SampleCode).HasMaxLength(50).IsRequired();
        b.HasIndex(x => x.SampleCode).IsUnique();
        b.HasOne(x => x.Subject).WithMany(s => s.Samples).HasForeignKey(x => x.SubjectId);
    }
}
