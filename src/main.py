#!/usr/bin/env python3
import asyncio
import csv
import aiohttp
import glob
import os
from vcf_processing.pre_annotation import run_vep
from vcf_processing.protein_variants import parse_vep_output_for_protein_changes
from matching.get_list import fetch_variant_info, MAX_ARTICLES
from matching.mining import get_pmids_from_csv, query_pubtator, extract_entities, write_to_csv
from visualization.plot import generate_html


async def get_list_main(input_csv, output_csv):
    rows = []
    variants = []

    with open(input_csv, 'r', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames + ["pmids", "Links", "Abstracts"]
        for row in reader:
            var = row["Protein Variation"] 
            variants.append(var)
            rows.append(row)

    unique_variants = list(set(variants))
    cache = {}

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_variant_info(session, v, cache) for v in unique_variants]
        await asyncio.gather(*tasks)

    with open(output_csv, 'w', newline='') as f:
        fieldnames = list(rows[0].keys()) + ["pmids", "Links", "Abstracts"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            var = row["Protein Variation"]
            info = cache.get(var, [])
            info = info[:MAX_ARTICLES]
            pmids = "\n".join([item[0] for item in info])
            links = "\n".join([item[1] for item in info])
            abstracts = "\n".join([item[2] for item in info])
            row["pmids"] = pmids
            row["Links"] = links
            row["Abstracts"] = abstracts
            writer.writerow(row)

def mining_main():
    pmids = get_pmids_from_csv("results/protein_pubmed.csv", pmid_column="pmids")

    all_results = []
    batch_size = 100
    for i in range(0, len(pmids), batch_size):
        batch_pmids = pmids[i:i+batch_size]
        if not batch_pmids:
            continue
        
        bioc_data = query_pubtator(batch_pmids, format="biocjson")
        batch_results = extract_entities(bioc_data)
        all_results.extend(batch_results)

    write_to_csv(all_results)

def main():
    # 1. Annotation
    input_vcf = "data/raw/chr1.vcf"
    annotated_vcf = "data/interim/chr1_annotated.vcf"
    run_vep(input_vcf, annotated_vcf)

    # 2. Extract variants
    annotated_vcf = "/Users/caicai/THESIS/annotated_everything_chr1.vcf"
    parse_vep_output_for_protein_changes(annotated_vcf)

    # 3. Getting PMIDs, links and abstracts
    asyncio.run(get_list_main("data/interim/test_variant.csv", "results/protein_pubmed.csv"))

    # 4. Text mining by pubtator
    mining_main()
    
    # 5. Visualization
    generate_html(entities_csv="results/entities_extracted.csv", variants_csv="results/protein_pubmed.csv")

    # Remove interim file
    interim_files = glob.glob("data/interim/*")
    for f in interim_files:
        os.remove(f)
    
    print("Pipeline completed.")

if __name__ == "__main__":
    main()
