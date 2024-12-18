#!/usr/bin/env python3
import vcfpy
import pandas as pd
import re

def parse_vep_output_for_protein_changes(annotated_vcf):

    variant_data = []
    vcf_reader = vcfpy.Reader.from_path(annotated_vcf)
    for record in vcf_reader:
        csq_info = record.INFO.get("CSQ")
    
        if csq_info:
            for csq in csq_info:
                # Parse each annotation information, such as genes, variant types, etc.
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
                            "Protein Variation": result
                        })
                
    df = pd.DataFrame(variant_data)
    df_deduplicated = df.drop_duplicates()

    output_csv = "data/interim/annoed_variant_id.csv"
    df_deduplicated.to_csv(output_csv, index=False)
