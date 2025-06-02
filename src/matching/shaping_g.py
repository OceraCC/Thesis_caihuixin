#!/usr/bin/env python3
import csv
import pandas as pd
from collections import defaultdict
from statistics import mean

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
    merged = defaultdict(lambda: {"pmids": [], "scores": []})

    for rec in records:
        key = (rec["gene"], rec["disease"], rec["association"])
        merged[key]["pmids"].append(rec["pmid"])
        try:
            merged[key]["scores"].append(float(rec["score"]))
        except ValueError:
            continue
        
    fieldnames = ["gene", "disease", "score", "association", "pmid"]
    with open(output_csv, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for (gene, disease, association), data in merged.items():
            avg_score = round(mean(data["scores"]), 3) if data["scores"] else ""
            pmid_str = ",".join(sorted(set(data["pmids"])))
            writer.writerow({
                "gene": gene,
                "disease": disease,
                "score": avg_score,
                "association": association,
                "pmid": pmid_str
            })

def shaping_g(entities_csv, pubmed_csv):
    transformed_records = transform_entities(entities_csv)
    gene_pubmed = pd.read_csv(pubmed_csv, dtype=str)
    gene_set = set(gene_pubmed["Gene"])
    final_records = filter_by_gene(transformed_records, gene_set)
    output_csv = "results/relations_g.csv"
    write_final_csv(final_records, output_csv)
