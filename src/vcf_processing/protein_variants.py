#!/usr/bin/env python3
import vcfpy
import pandas as pd
import re

def parse_vep_output_for_protein_changes(annotated_vcf):
    """
    从VEP注释后的VCF文件中解析CSQ字段，提取HGVSp蛋白变异信息（如Ala552Val）。
    """
    variant_data = []
    vcf_reader = vcfpy.Reader.from_path(annotated_vcf)
    for record in vcf_reader:
        # 获取变异的CSQ字段（VEP注释）
        csq_info = record.INFO.get("CSQ")
    
        # 如果CSQ字段存在，解析其中的信息
        if csq_info:
            for csq in csq_info:
                # 解析每个注释信息，这里可以获取基因、变异类型等
                fields = csq.split('|')
                consequence = fields[1]  # 例如获取变异的功能类型
                gene = fields[3]  # 基因符号
                transcript = fields[4]  # 转录本ID
                protein_vari = fields[11]
                variID = fields[17]
                if protein_vari:
                    match = re.search(r"\((.*?)\)", protein_vari)
                    if match:
                        result = match.group(1)
                        variant_data.append({
                            "Gene": gene,
                            "Consequence": consequence,
                            "Transcript": transcript,
                            "Variation ID": variID,
                            "Protein Variation": result
                        })
                
    df = pd.DataFrame(variant_data)
    df_deduplicated = df.drop_duplicates()

    # 将结果保存为CSV文件
    output_csv = "data/interim/annoed_variant_id.csv"
    df_deduplicated.to_csv(output_csv, index=False)
    
if __name__ == "__main__":
    # 假定输入数据在data/raw目录下
    annotated_vcf = "/Users/caicai/THESIS/annotated_everything_chr1.vcf"

    # 解析注释后的VCF文件，提取蛋白变异信息
    parse_vep_output_for_protein_changes(annotated_vcf)
