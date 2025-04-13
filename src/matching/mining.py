#!/usr/bin/env python3
import requests
import json
import csv

def query_pubtator(pmids, format="biocjson"):
    pmids_str = ",".join(pmids)
    url = f"https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/{format}?pmids={pmids_str}"
    response = requests.get(url)
    response.raise_for_status() 
    return response.json()

def extract_entities(data):
    documents = data.get("PubTator3", [])
    results = []
    for doc in documents:
        pmid = doc.get("pmid", "")
        
        genes = []
        mutations = []
        diseases = []
        
        passages = doc.get("passages", [])
        for passage in passages:
            annotations = passage.get("annotations", [])
            for ann in annotations:
                infons = ann.get("infons", {})
                entity_type = infons.get("type", "")
                entity_text = ann.get("text", "")
                
                etype_lower = entity_type.lower()
                if etype_lower == "gene":
                    genes.append(entity_text)
                elif etype_lower in ["mutation", "variant"]:
                    mutations.append(entity_text)
                elif etype_lower == "disease":
                    mesh_id = infons.get("identifier", "") 
                    diseases.append(mesh_id)

        gene_str = ";".join(genes)
        mutation_str = ";".join(mutations)
        disease_str = ";".join(diseases)
        
        if disease_str.strip() == "":
            continue
        
        results.append({
            "pmid": pmid,
            "gene": gene_str,
            "mutation": mutation_str,
            "disease": disease_str
        })
    return results

def write_to_csv(results):
    output_csv="results/entities_extracted2.csv"
    fieldnames = ["pmid", "gene", "mutation", "disease"]
    with open(output_csv, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

def get_pmids_from_csv(input_csv, pmid_column="pmids"):
    pmid_set = set()
    with open(input_csv, "r", newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pmid_str = row.get(pmid_column, "")
            if pmid_str.strip():
                pmids = pmid_str.split("\n")
                for p in pmids:
                    p = p.strip()
                    if p:
                        pmid_set.add(p)
    return list(pmid_set)