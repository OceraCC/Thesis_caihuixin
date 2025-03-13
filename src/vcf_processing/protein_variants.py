#!/usr/bin/env python3
import vcfpy
import pandas as pd
import re

def parse_vep_output_for_protein_changes(annotated_vcf):
    # 读取原始文件，保存非注释行
    raw_lines = []
    with open(annotated_vcf, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.startswith('#'):
                raw_lines.append(line)

    vcf_reader = vcfpy.Reader.from_path(annotated_vcf)

    variant_data = []
    line_index = 0

    # 解析每个 record 的同时，获取对应的原始文本行
    for record in vcf_reader:
        # 当前变异对应的原始行
        original_line = raw_lines[line_index]
        line_index += 1

        csq_info = record.INFO.get("CSQ")
        if csq_info:
            for csq in csq_info:
                fields = csq.split('|')
                consequence = fields[1]
                gene = fields[3]
                transcript = fields[4]
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
                            "Protein Variation": result,
                            "vcf": original_line
                        })

    df = pd.DataFrame(variant_data)
    df_deduplicated = df.drop_duplicates()

    output_csv = "data/interim/annoed_variant_id.csv"
    df_deduplicated.to_csv(output_csv, index=False)

    return df_deduplicated
