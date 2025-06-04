#!/usr/bin/env python3
import vcfpy
import pandas as pd
import re

def parse_vep_output_for_changes(annotated_vcf, output_csv):
    # After reading the annotated VCF, save the non-annotate lines (so that the INFO string could be processed)
    raw_lines = []
    with open(annotated_vcf, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.startswith('#'):
                raw_lines.append(line)

    # Parsing with vcfpy (extracting CSQ from comments for subsequent table information processing)
    vcf_reader = vcfpy.Reader.from_path(annotated_vcf)

    variant_data = []
    line_index = 0

    for record in vcf_reader:
        original_line = raw_lines[line_index]
        line_index += 1

        columns = original_line.split('\t')
        if len(columns) >= 8:
            info = columns[7]  # Column 8 is INFO

            # Find the starting position of "CSQ="
            idx_csq = info.find("CSQ=")
            if idx_csq != -1:
                # If there is a semicolon in front, remove it as well.
                start_cut = idx_csq
                if start_cut > 0 and info[start_cut - 1] == ';':
                    start_cut -= 1
                info = info[:start_cut].rstrip(';')  # Keep it until CSQ and clean up the trailing semicolon

            columns[7] = info
            cleaned_line = '\t'.join(columns[:8])
        else:
            # If the number of columns is abnormal, keep it as is
            cleaned_line = original_line

        csq_info = record.INFO.get("CSQ")
        if csq_info:
            for csq in csq_info:
                fields = csq.split('|')
                consequence = fields[1]
                gene = fields[3]
                transcript = fields[4]
                variID = fields[17]
                variant_data.append({
                    "Gene": gene,
                    "Consequence": consequence,
                    "Transcript": transcript,
                    "VariationID": variID,
                    "vcf": cleaned_line
                })

    # Deduplication & Writing CSV
    df = pd.DataFrame(variant_data)
    df_deduplicated = df.drop_duplicates()

    df_deduplicated.to_csv(output_csv, index=False)

    return df_deduplicated
