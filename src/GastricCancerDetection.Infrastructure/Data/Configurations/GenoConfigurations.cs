using GastricCancerDetection.Domain.Entities.Geno;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace GastricCancerDetection.Infrastructure.Data.Configurations;

public class GeneConfiguration : IEntityTypeConfiguration<Gene>
{
    public void Configure(EntityTypeBuilder<Gene> b)
    {
        b.ToTable("Genes", "geno");
        b.HasKey(x => x.GeneId);
        b.Property(x => x.GeneSymbol).HasMaxLength(50).IsRequired();
        b.HasIndex(x => new { x.GeneSymbol, x.BuildId }).IsUnique();
    }
}

public class TranscriptConfiguration : IEntityTypeConfiguration<Transcript>
{
    public void Configure(EntityTypeBuilder<Transcript> b)
    {
        b.ToTable("Transcripts", "geno");
        b.HasKey(x => x.TranscriptId);
    }
}

public class GenePanelConfiguration : IEntityTypeConfiguration<GenePanel>
{
    public void Configure(EntityTypeBuilder<GenePanel> b)
    {
        b.ToTable("GenePanels", "geno");
        b.HasKey(x => x.PanelId);
        b.HasIndex(x => new { x.PanelName, x.PanelVersion }).IsUnique();
    }
}

public class GenePanelGeneConfiguration : IEntityTypeConfiguration<GenePanelGene>
{
    public void Configure(EntityTypeBuilder<GenePanelGene> b)
    {
        b.ToTable("GenePanelGenes", "geno");
        b.HasKey(x => x.PanelGeneId);
        b.HasIndex(x => new { x.PanelId, x.GeneId }).IsUnique();
        b.HasOne(x => x.Gene).WithMany().HasForeignKey(x => x.GeneId);
        b.HasOne<GenePanel>().WithMany(p => p.PanelGenes).HasForeignKey(x => x.PanelId);
    }
}

public class SequencingRunConfiguration : IEntityTypeConfiguration<SequencingRun>
{
    public void Configure(EntityTypeBuilder<SequencingRun> b)
    {
        b.ToTable("SequencingRuns", "geno");
        b.HasKey(x => x.SeqRunId);
    }
}

public class GenomeFileConfiguration : IEntityTypeConfiguration<GenomeFile>
{
    public void Configure(EntityTypeBuilder<GenomeFile> b)
    {
        b.ToTable("GenomeFiles", "geno");
        b.HasKey(x => x.FileId);
        b.Property(x => x.FileFormat).HasMaxLength(20).IsRequired();
        b.HasOne<Domain.Entities.Clin.Sample>().WithMany(s => s.GenomeFiles).HasForeignKey(x => x.SampleId);
    }
}

public class VariantCatalogConfiguration : IEntityTypeConfiguration<VariantCatalog>
{
    public void Configure(EntityTypeBuilder<VariantCatalog> b)
    {
        b.ToTable("VariantCatalog", "geno");
        b.HasKey(x => x.VariantCatalogId);
        b.Property(x => x.RefAllele).HasMaxLength(500).IsRequired();
        b.Property(x => x.AltAllele).HasMaxLength(500).IsRequired();

        // VariantHash یک Computed Persisted Column در دیتابیس است (SHA2_256)
        // EF فقط آن را می‌خواند و هرگز در INSERT/UPDATE ارسال نمی‌کند
        b.Property(x => x.VariantHash)
            .HasColumnType("binary(32)")
            .ValueGeneratedOnAddOrUpdate()
            .Metadata.SetAfterSaveBehavior(Microsoft.EntityFrameworkCore.Metadata.PropertySaveBehavior.Ignore);

        b.HasIndex(x => x.VariantHash).IsUnique();
        b.HasOne(x => x.Gene).WithMany().HasForeignKey(x => x.GeneId);
    }
}

public class VariantPopulationFrequencyConfiguration : IEntityTypeConfiguration<VariantPopulationFrequency>
{
    public void Configure(EntityTypeBuilder<VariantPopulationFrequency> b)
    {
        b.ToTable("VariantPopulationFrequencies", "geno");
        b.HasKey(x => new { x.VariantCatalogId, x.SourceId });
    }
}

public class StructuralVariantCatalogConfiguration : IEntityTypeConfiguration<StructuralVariantCatalog>
{
    public void Configure(EntityTypeBuilder<StructuralVariantCatalog> b)
    {
        b.ToTable("StructuralVariantCatalog", "geno");
        b.HasKey(x => x.SVCatalogId);
    }
}

public class ExtractedVariantConfiguration : IEntityTypeConfiguration<ExtractedVariant>
{
    public void Configure(EntityTypeBuilder<ExtractedVariant> b)
    {
        b.ToTable("ExtractedVariants", "geno");
        b.HasKey(x => x.ExtractedVariantId);
        b.HasIndex(x => new { x.FileId, x.VariantCatalogId }).IsUnique();
        b.HasOne(x => x.GenomeFile).WithMany(f => f.ExtractedVariants).HasForeignKey(x => x.FileId);
        b.HasOne(x => x.VariantCatalog).WithMany().HasForeignKey(x => x.VariantCatalogId);
    }
}

public class ExtractedStructuralVariantConfiguration : IEntityTypeConfiguration<ExtractedStructuralVariant>
{
    public void Configure(EntityTypeBuilder<ExtractedStructuralVariant> b)
    {
        b.ToTable("ExtractedStructuralVariants", "geno");
        b.HasKey(x => x.ExtractedSVId);
    }
}
