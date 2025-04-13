#!/usr/bin/env python3
import csv
import os
import pandas as pd

def transform_entities(input_csv):
    transformed_records = []
    with open(input_csv, "r", newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pmid = row.get("pmid", "").strip()
            relations_field = row.get("relations", "").strip()
            if not relations_field:
                continue

            relation_items = [item.strip() for item in relations_field.split(";") if item.strip()]
            for item in relation_items:
                parts = item.split("!")
                if len(parts) != 4:
                    continue
                disease = parts[0].strip()
                gene = parts[1].strip()
                score = parts[2].strip()
                association = parts[3].strip()

                transformed_records.append({
                    "pmid": pmid,
                    "gene": gene,
                    "disease": disease,
                    "score": score,
                    "association": association
                })
    return transformed_records

def filter_by_gene(records, gene_set):
    filtered = []
    for rec in records:
        gene = rec.get("gene", "").strip().upper()
        if gene in gene_set:
            filtered.append(rec)
    return filtered

def write_final_csv(records, output_csv):
    
    fieldnames = ["gene", "disease", "score", "association", "pmid"]
    with open(output_csv, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)

def shaping(entities_csv, gene_pubmed_csv):
    transformed_records = transform_entities(entities_csv)
    gene_pubmed = pd.read_csv(gene_pubmed_csv, dtype=str)
    gene_set = set(gene_pubmed["Gene"])
    final_records = filter_by_gene(transformed_records, gene_set)
    
    output_csv = "results/relations.csv"
    write_final_csv(final_records, output_csv)
