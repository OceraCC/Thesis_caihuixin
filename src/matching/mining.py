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
    """
    从单个关系对象中提取信息，并格式化成字符串：
    "MESH(identifier)!gene(name)!score!type"。
    这里假设在关系中的 infons 部分包含：
      - "score": 表示关系分数
      - "type": 表示关系的类型（如 Association、Negative_Correlation、treat 等）
      - "role1" 和 "role2" 分别为两个角色信息。
    其中判断哪一角色属于疾病时，依据其 identifier 以 "MESH:" 开头；另一角色作为 gene，
    则取它的 "name" 字段。
    如果未能同时找到疾病和 gene 信息，则返回 None。
    """
    infons = rel.get("infons", {})
    score = infons.get("score", "")
    r_type = infons.get("type", "")
    role1 = infons.get("role1", {})
    role2 = infons.get("role2", {})

    disease = None
    gene = None
    # 判断 role1 与 role2：以 identifier 以 "MESH:" 开头的为疾病
    if role1.get("type", "") == "Disease" and role2.get("type", "") == "Gene":
        disease = role1.get("identifier", "")
        gene = role2.get("name", "")
    elif role2.get("type", "") == "Disease" and role1.get("type", "") == "Gene":
        disease = role2.get("identifier", "")
        gene = role1.get("name", "")
        
    if not disease or not gene:
        return None
    # 返回格式化结果
    return f"{disease}!{gene}!{score}!{r_type}"

def extract_relations(data):
    """
    根据 PubTator 返回的 JSON 数据，提取每个文献（pmid）对应的关系信息。
    对于每个文献：
      - 检查顶层的 "relations" 字段（若存在）
      - 同时遍历每个 passage 中的 "relations"
    将所有关系转换为格式化字符串，多个关系之间用 ";" 分隔。
    如果文献中没有关系信息，则略过该文献。
    """
    documents = data.get("PubTator3", [])
    results = []
    for doc in documents:
        pmid = doc.get("pmid", "")
        all_relations = []
        
        # 提取顶层关系（如果存在）
        top_relations = doc.get("relations", [])
        for rel in top_relations:
            rel_str = process_relation(rel)
            if rel_str:
                all_relations.append(rel_str)
                
        # 遍历 passages 内的关系信息
        for passage in doc.get("passages", []):
            passage_relations = passage.get("relations", [])
            for rel in passage_relations:
                rel_str = process_relation(rel)
                if rel_str:
                    all_relations.append(rel_str)
                    
        if not all_relations:
            continue
        
        relations_str = ";".join(all_relations)
        results.append({
            "pmid": pmid,
            "relations": relations_str
        })
    return results

def write_to_csv(results):
    """
    将最终结果写入 CSV 文件，字段为 "pmid" 和 "relations"
    """
    output_csv = "results/entities_extracted2.csv"
    fieldnames = ["pmid", "relations"]
    with open(output_csv, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

def get_pmids_from_csv(input_csv, pmid_column="pmids"):
    """
    从指定 CSV 文件中提取所有 PMID（假设每个单元格中可能有多行文本），
    返回一个 PMID 列表。
    """
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

