#!/usr/bin/env python3
import asyncio
import csv
import aiohttp
import glob
import os
import subprocess
import sys
from vcf_processing.pre_annotation import run_vep
from vcf_processing.variants import parse_vep_output_for_changes
from matching.get_list import fetch_variant_info, MAX_ARTICLES
from matching.mining import get_pmids_from_csv, query_pubtator, extract_relations, write_to_csv
from matching.shaping_v import shaping_v
from matching.shaping_g import shaping_g
from db.db_init import init_Vrelations_db, init_Grelations_db, init_variant_db, init_mesh_db
from validation.gwas_merge import gwas_merge


async def get_list_main(input_csv, output_csv):
    rows = []
    variants = []

    with open(input_csv, 'r', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames + ["pmids"]
        for row in reader:
            var = row["Gene"] 
            variants.append(var)
            rows.append(row)

    unique_variants = list(set(variants))
    cache = {}

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_variant_info(session, v, cache) for v in unique_variants]
        await asyncio.gather(*tasks)

    with open(output_csv, 'w', newline='') as f:
        fieldnames = list(rows[0].keys()) + ["pmids"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            var = row["Gene"]
            info = cache.get(var, [])
            info = info[:MAX_ARTICLES]
            pmids = "\n".join(info)
            if pmids:
                row["pmids"] = pmids
                writer.writerow(row)

def mining_main():
    pmids = get_pmids_from_csv("data/interim/variant_pubmed.csv", pmid_column="pmids")

    all_variant = []
    all_gene = []
    batch_size = 70
    for i in range(0, len(pmids), batch_size):
        batch_pmids = pmids[i:i+batch_size]
        if not batch_pmids:
            continue

        bioc_data = query_pubtator(batch_pmids, format="biocjson")
        gene_rels, var_rels = extract_relations(bioc_data)
        all_variant.extend(var_rels)
        all_gene.extend(gene_rels)

    # Write to separate files
    write_to_csv(all_variant, "results/extracted_v.csv")
    write_to_csv(all_gene, "results/extracted_g.csv")
    
def launch_visualization():
    vis_path = os.path.join(os.path.dirname(__file__), 'visualization', 'page.py')

    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(__file__)
    subprocess.run(['streamlit', 'run', vis_path], env=env)

def main():
    # 1. Annotation
    if len(sys.argv) < 2:
        print("Usage: python main.py <input_file_path>")
        sys.exit(1)

    input_vcf = sys.argv[1]
    print("Input file path is:", input_vcf)
    annotated_vcf = "data/interim/annotated.vcf"
    run_vep(input_vcf, annotated_vcf)

    # 2. Extract variants
    annotated_vcf = "data/interim/annotated.vcf"
    output_csv = "data/interim/variants.csv"
    parse_vep_output_for_changes(annotated_vcf, output_csv)

    # 3. Getting PMIDs
    asyncio.run(get_list_main("data/interim/variants.csv", "data/interim/variant_pubmed.csv"))

    # 4. Text mining by pubtator
    mining_main()
    
    # 5. Shaping
    shaping_v(entities_csv="data/interim/extracted_v.csv", pubmed_csv="data/interim/variant_pubmed.csv")
    shaping_g(entities_csv="data/interim/extracted_g.csv", pubmed_csv="data/interim/variant_pubmed.csv")
    
    # 6. Validating by GWAS
    gwas_merge(input_csv="data/interim/variant_pubmed.csv")
    
    # 7. Building database
    db_path = 'database/data.db'
    init_Vrelations_db(csv_path="results/relations_v.csv", db_path=db_path)
    init_Grelations_db(csv_path="results/relations_g.csv", db_path=db_path)
    init_variant_db(csv_path="results/gwas_merged.csv", db_path=db_path)
    init_mesh_db(tsv_path="database/mesh2025.tsv", db_path=db_path)
    
    # 7. Visualization
    launch_visualization()

    # Remove interim file
    interim_files = glob.glob("data/interim/*")
    for f in interim_files:
       os.remove(f)
    
    print("Pipeline completed.")

if __name__ == "__main__":
    main()
