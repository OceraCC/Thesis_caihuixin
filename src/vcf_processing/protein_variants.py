#!/usr/bin/env python3
import vcfpy
import pandas as pd
import re

def parse_vep_output_for_protein_changes(annotated_vcf):
    # 1) 读取注释后VCF，保存非注释行（以便我们手动处理INFO字符串）
    raw_lines = []
    with open(annotated_vcf, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.startswith('#'):
                raw_lines.append(line)

    # 2) 用 vcfpy 解析（从注释里提取CSQ进行后续表格信息处理）
    vcf_reader = vcfpy.Reader.from_path(annotated_vcf)

    variant_data = []
    line_index = 0

    for record in vcf_reader:
        original_line = raw_lines[line_index]
        line_index += 1

        columns = original_line.split('\t')
        if len(columns) >= 8:
            info = columns[7]  # 第8列是INFO

            # 找到 "CSQ=" 起始位置
            idx_csq = info.find("CSQ=")
            if idx_csq != -1:
                # 若前面有分号，则也一起去除
                start_cut = idx_csq
                if start_cut > 0 and info[start_cut - 1] == ';':
                    start_cut -= 1
                info = info[:start_cut].rstrip(';')  # 保留到CSQ前，并清理末尾分号

            columns[7] = info
            cleaned_line = '\t'.join(columns[:8])
        else:
            # 如果列数异常，就原样保留
            cleaned_line = original_line

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
                            # 这里写入“只保留到SOR为止”的行
                            "vcf": cleaned_line
                        })

    # 去重 & 写CSV
    df = pd.DataFrame(variant_data)
    df_deduplicated = df.drop_duplicates()

    output_csv = "data/interim/annoed_variant_id.csv"
    df_deduplicated.to_csv(output_csv, index=False)

    return df_deduplicated
