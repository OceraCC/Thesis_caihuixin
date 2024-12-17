#!/usr/bin/env python3
import subprocess
import os

def run_vep(input_vcf, output_vcf):
    """
    使用VEP对输入VCF进行注释，并将结果写出到新的VCF文件中。
    """
    input_vcf = os.path.abspath(input_vcf)
    output_vcf = os.path.abspath(output_vcf)

    cmd = [
        "vep",
        "--input_file", input_vcf,
        "--output_file", output_vcf,
        '--vcf',  # 输出 VCF 格式
        '--cache',  # 使用缓存注释（离线模式）
        '--offline',  # 以离线模式运行
        '--symbol',  # 添加基因符号信息
        '--hgvsp', # 蛋白质层面信息
        '--fasta', '/Users/caicai/.vep/homo_sapiens/112_GRCh38/Homo_sapiens.GRCh38.dna.toplevel.fa',  # 使用压缩的FASTA文件
        '--force_overwrite',  # 覆盖已有输出文件
        '--everything',
        '--check_existing',  # 检查是否已知的dbSNP变异
        '--fork', '10',
        '--no_stats'  # 禁用统计信息生成
    ]

    subprocess.check_call(cmd)
    
if __name__ == "__main__":
    input_vcf = "data/raw/chr1.vcf"
    annotated_vcf = "data/interim/chr1_annotated.vcf"
    # 首先运行VEP注释
    run_vep(input_vcf, annotated_vcf)