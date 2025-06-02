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
                rsID = parts[1].strip()
                score = parts[2].strip()
                association = parts[3].strip()

                transformed_records.append({
                    "pmid": pmid,
                    "rsID": rsID,
                    "disease": disease,
                    "score": score,
                    "association": association
                })
    return transformed_records

def filter_by_ID(records, ID_set):
    filtered = []
    for rec in records:
        rsID = rec.get("rsID", "").strip()
        if rsID in ID_set:
            filtered.append(rec)
    return filtered

def write_final_csv(records, output_csv, ID_gene):
    merged = defaultdict(lambda: {"pmids": [], "scores": []})

    for rec in records:
        key = (rec["rsID"], rec["disease"], rec["association"])
        merged[key]["pmids"].append(rec["pmid"])
        try:
            merged[key]["scores"].append(float(rec["score"]))
        except ValueError:
            continue

    fieldnames = ["rsID", "gene", "disease", "score", "association", "pmid"]
    with open(output_csv, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for (rsID, disease, association), data in merged.items():
            avg_score = round(mean(data["scores"]), 3) if data["scores"] else ""
            pmid_str = ",".join(sorted(set(data["pmids"])))
            gene = list(set(ID_gene[rsID]))
            for g in gene:
                writer.writerow({
                    "rsID": rsID,
                    "gene": g,
                    "disease": disease,
                    "score": avg_score,
                    "association": association,
                    "pmid": pmid_str
                })

def shaping_v(entities_csv, pubmed_csv):
    transformed_records = transform_entities(entities_csv)
    gene_pubmed = pd.read_csv(pubmed_csv, dtype=str)
    ID_set = set(gene_pubmed["VariationID"])
    ID_gene = defaultdict(list)
    for k, v in zip(gene_pubmed["VariationID"], gene_pubmed["Gene"]):
        ID_gene[k].append(v)
    final_records = filter_by_ID(transformed_records, ID_set)
    output_csv = "results/relations_v.csv"
    write_final_csv(final_records, output_csv, ID_gene)
