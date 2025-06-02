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

def process_relation(rel):
    infons = rel.get("infons", {})
    score = infons.get("score", "")
    r_type = infons.get("type", "")
    role1 = infons.get("role1", {})
    role2 = infons.get("role2", {})

    disease = None
    variant = None
    category = None
    # 判断 role1 与 role2：以 identifier 以 "MESH:" 开头的为疾病
    if role1.get("type", "") == "Disease" and role2.get("type", "") in ["Variant", "Gene"]:
        disease = role1.get("identifier", "")
        variant = role2.get("name", "")
        category = role2.get("type", "")
    elif role2.get("type", "") == "Disease" and role1.get("type", "") in ["Variant", "Gene"]:
        disease = role2.get("identifier", "")
        variant = role1.get("name", "")
        category = role1.get("type", "")
        
    if not disease:
        return None
    # 返回格式化结果
    return [category, f"{disease}!{variant}!{score}!{r_type}"]

def extract_relations(data):
    documents = data.get("PubTator3", [])
    v_results = []
    g_results = []
    for doc in documents:
        pmid = doc.get("pmid", "")
        v_relations = []
        g_relations = []

        top_relations = doc.get("relations", [])
        for rel in top_relations:
            retn = process_relation(rel)
            if retn:
                if retn[0] == "Variant":
                    rel_str = retn[1]
                    if rel_str:
                        v_relations.append(rel_str)
                elif retn[0] == "Gene":
                    rel_str = retn[1]
                    if rel_str:
                        g_relations.append(rel_str)
                
        for passage in doc.get("passages", []):
            passage_relations = passage.get("relations", [])
            for rel in passage_relations:
                retn = process_relation(rel)
                if retn:
                    if retn[0] == "Variant":
                        rel_str = retn[1]
                        if rel_str:
                            v_relations.append(rel_str)
                    elif retn[0] == "Gene":
                        rel_str = retn[1]
                        if rel_str:
                            g_relations.append(rel_str)
                    
        if not g_relations or not v_relations:
            continue
        
        g_relations_str = ";".join(g_relations)
        v_relations_str = ";".join(v_relations)
        if g_relations_str:
            g_results.append({
                "pmid": pmid,
                "relations": g_relations_str
            })
        if v_relations_str:
            v_results.append({
                "pmid": pmid,
                "relations": v_relations_str
            })
    return g_results, v_results

def write_to_csv(results, output_csv):
    fieldnames = ["pmid", "relations"]
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

