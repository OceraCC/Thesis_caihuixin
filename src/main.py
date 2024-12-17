#!/usr/bin/env python3
import asyncio
import csv
import aiohttp
import glob
import os
# 假设函数来自以下模块（请根据实际项目结构调整import路径）
from vcf_processing.pre_annotation import run_vep
from vcf_processing.protein_variants import parse_vep_output_for_protein_changes
from matching.get_list import fetch_variant_info, MAX_ARTICLES
from matching.mining import get_pmids_from_csv, query_pubtator, extract_entities, write_to_csv

# 根据提供的代码片段，需要在main.py中重新定义get_list和mining中的main逻辑

async def get_list_main(input_csv, output_csv):
    rows = []
    variants = []

    # 从input_csv中获取蛋白变异列表
    with open(input_csv, 'r', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames + ["pmids", "Links", "Abstracts"]
        for row in reader:
            var = row["Protein Variation"] 
            variants.append(var)
            rows.append(row)

    unique_variants = list(set(variants))
    cache = {}

    # 异步抓取所有variants的信息
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_variant_info(session, v, cache) for v in unique_variants]
        await asyncio.gather(*tasks)

    # 将查询结果映射回原表格
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
    # 每批次请求100个PMID
    batch_size = 100
    for i in range(0, len(pmids), batch_size):
        batch_pmids = pmids[i:i+batch_size]
        # 若batch_pmids为空或没有PMID则跳过
        if not batch_pmids:
            continue
        
        # 查询PubTator
        bioc_data = query_pubtator(batch_pmids, format="biocjson")
        # 解析数据
        batch_results = extract_entities(bioc_data)
        all_results.extend(batch_results)

    # 所有批次合并后写入CSV
    write_to_csv(all_results)

def main():
    # 1. 使用VEP进行注释
    input_vcf = "data/raw/chr1.vcf"
    annotated_vcf = "data/interim/chr1_annotated.vcf"
    run_vep(input_vcf, annotated_vcf)

    # 2. 从注释后的VCF中提取蛋白质变异信息（假设会输出csv，如test_variant.csv）
    # 请根据实际情况修改parse_vep_output_for_protein_changes的参数和输出
    # 假设该函数会生成 "data/interim/test_variant.csv"
    annotated_vcf = "/Users/caicai/THESIS/annotated_everything_chr1.vcf"
    parse_vep_output_for_protein_changes(annotated_vcf)

    # 3. 异步获取PMIDs及其相关链接和摘要，并输出results/protein_pubmed.csv
    # 假设parse_vep_output_for_protein_changes 生成了 data/interim/test_variant.csv
    asyncio.run(get_list_main("data/interim/test_variant.csv", "results/protein_pubmed.csv"))

    # 4. 使用PubTator提取Gene/Mutation/Disease信息
    # 根据results/protein_pubmed.csv获取PMIDs，并批量从PubTator获取信息，然后输出entities_extracted.csv
    mining_main()

    interim_files = glob.glob("data/interim/*")
    for f in interim_files:
        os.remove(f)
    
    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
