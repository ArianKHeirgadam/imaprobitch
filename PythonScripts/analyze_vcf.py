#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_vcf.py
----------------
اسکریپت استخراج واریانت از فایل VCF، محدود به محدوده‌ی ژن‌های هدف.

این اسکریپت مستقیماً توسط .NET (از طریق PythonRunnerService.cs) به‌صورت Process
اجرا می‌شود، نه به‌عنوان یک سرویس شبکه‌ای جدا. ورودی از طریق آرگومان‌های خط فرمان
و خروجی به‌صورت یک شیء JSON در stdout است تا .NET بتواند آن را Deserialize کند.

استفاده:
    python analyze_vcf.py --vcf path/to/file.vcf --genes CDH1,TP53,ARID1A

نکته‌ی مهم: این نسخه فقط فایل‌های VCF متنی استاندارد (نسخه ۴.x) را می‌خواند و از
کتابخانه‌های تخصصی مثل pysam/cyvcf2 استفاده نمی‌کند تا نصب و اجرا روی هر سیستمی
بدون وابستگی اضافه ساده باشد. برای فایل‌های VCF.gz یا BAM، باید مرحله‌ی
Alignment/Variant Calling جداگانه (BWA+GATK) قبل از این اسکریپت اجرا شود.
"""

import argparse
import gzip
import json
import sys

# مختصات ژن‌های پنل غربالگری سرطان معده روی GRCh38 - باید دقیقاً با داده‌ی
# seed شده در geno.Genes در دیتابیس (فایل 01_schema_enterprise_final.sql) هماهنگ باشد
GENE_COORDINATES = {
    "CDH1":   {"chromosome": "16", "start": 68737225, "end": 68835548},
    "TP53":   {"chromosome": "17", "start": 7661779,  "end": 7687550},
    "ARID1A": {"chromosome": "1",  "start": 26696429, "end": 26782104},
    "CTNNA1": {"chromosome": "5",  "start": 138169763, "end": 138194351},
    "STK11":  {"chromosome": "19", "start": 1205798,  "end": 1228431},
    "SMAD4":  {"chromosome": "18", "start": 51030213, "end": 51085042},
    "MLH1":   {"chromosome": "3",  "start": 36993350, "end": 37050996},
    "MSH2":   {"chromosome": "2",  "start": 47403067, "end": 47709830},
}


def find_gene_for_variant(chromosome: str, position: int, target_genes: set) -> str | None:
    """اگر واریانت داخل محدوده‌ی یکی از ژن‌های هدف باشد، نام آن ژن را برمی‌گرداند"""
    chrom_normalized = chromosome.replace("chr", "").replace("Chr", "").replace("CHR", "")
    for gene_symbol in target_genes:
        coords = GENE_COORDINATES.get(gene_symbol)
        if coords is None:
            continue
        if coords["chromosome"] == chrom_normalized and coords["start"] <= position <= coords["end"]:
            return gene_symbol
    return None


def parse_info_field(info_str: str) -> dict:
    result = {}
    for item in info_str.split(";"):
        if "=" in item:
            key, _, value = item.partition("=")
            result[key] = value
        else:
            result[item] = True
    return result


def zygosity_from_genotype(gt: str) -> str:
    gt_clean = gt.replace("|", "/")
    alleles = gt_clean.split("/")
    if len(alleles) < 2:
        return "Unknown"
    if alleles[0] == "0" and alleles[1] == "0":
        return "Homozygous_Ref"
    if alleles[0] == alleles[1] and alleles[0] not in ("0", "."):
        return "Homozygous_Alt"
    if alleles[0] != alleles[1] and "." not in alleles:
        return "Heterozygous"
    return "Unknown"


def open_vcf(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def extract_variants(vcf_path: str, target_genes: list) -> list:
    target_gene_set = set(target_genes)
    variants = []

    with open_vcf(vcf_path) as f:
        format_keys = []
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                continue  # خط هدر ستون‌ها - فیلدهای FORMAT پویا هستند و از رکورد خود می‌خوانیم

            fields = line.split("\t")
            if len(fields) < 8:
                continue

            chrom, pos_str, _vid, ref, alt, qual_str, _filter, info_str = fields[:8]

            try:
                position = int(pos_str)
            except ValueError:
                continue

            gene_symbol = find_gene_for_variant(chrom, position, target_gene_set)
            if gene_symbol is None:
                continue  # فقط واریانت‌های داخل ژن‌های هدف نگه داشته می‌شوند

            info = parse_info_field(info_str)

            quality = None
            try:
                quality = float(qual_str) if qual_str not in (".", "") else None
            except ValueError:
                quality = None

            read_depth = None
            if "DP" in info:
                try:
                    read_depth = int(info["DP"])
                except ValueError:
                    read_depth = None

            allele_fraction = None
            if "AF" in info:
                try:
                    allele_fraction = float(info["AF"])
                except ValueError:
                    allele_fraction = None

            zygosity = "Unknown"
            if len(fields) >= 10:
                format_keys = fields[8].split(":")
                sample_values = fields[9].split(":")
                if "GT" in format_keys:
                    gt_index = format_keys.index("GT")
                    if gt_index < len(sample_values):
                        zygosity = zygosity_from_genotype(sample_values[gt_index])
                if read_depth is None and "DP" in format_keys:
                    dp_index = format_keys.index("DP")
                    if dp_index < len(sample_values):
                        try:
                            read_depth = int(sample_values[dp_index])
                        except ValueError:
                            pass

            # هر ALT چندگانه (comma-separated) را به‌صورت واریانت جدا ثبت می‌کنیم
            for alt_allele in alt.split(","):
                if alt_allele in (".", ""):
                    continue
                variants.append({
                    "chromosome": chrom.replace("chr", ""),
                    "position": position,
                    "refAllele": ref,
                    "altAllele": alt_allele,
                    "geneSymbol": gene_symbol,
                    "zygosity": zygosity,
                    "quality": quality,
                    "readDepth": read_depth,
                    "alleleFraction": allele_fraction,
                })

    return variants


def main():
    parser = argparse.ArgumentParser(description="استخراج واریانت از فایل VCF محدود به ژن‌های هدف")
    parser.add_argument("--vcf", required=True, help="مسیر فایل VCF ورودی")
    parser.add_argument("--genes", required=True, help="لیست نام ژن‌های هدف، جدا شده با کاما")
    args = parser.parse_args()

    target_genes = [g.strip() for g in args.genes.split(",") if g.strip()]

    try:
        variants = extract_variants(args.vcf, target_genes)
        print(json.dumps({"success": True, "errorMessage": None, "variants": variants}, ensure_ascii=False))
    except FileNotFoundError:
        print(json.dumps({"success": False, "errorMessage": f"فایل VCF پیدا نشد: {args.vcf}", "variants": []}, ensure_ascii=False))
        sys.exit(1)
    except Exception as ex:  # noqa: BLE001 - عمداً کلی، چون این خروجی به .NET برمی‌گردد
        print(json.dumps({"success": False, "errorMessage": str(ex), "variants": []}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
