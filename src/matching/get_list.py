import csv
import asyncio
import aiohttp
import xml.etree.ElementTree as ET

from urllib.parse import quote

# PubMed E-utilities URLs
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

MAX_ARTICLES = 5
SEM = asyncio.Semaphore(5)  # 限制同时进行的请求数，防止服务器过载
API_KEY = "a5a62f477ecadf68b6f60e03633847489c08"

async def fetch_pmids(session, variant, retries=3):
    params = {
        "db": "pubmed",
        "term": variant,
        "retmax": str(MAX_ARTICLES),
        "retmode": "json",
        "api_key": API_KEY
    }
    for attempt in range(retries):
        try:
            async with SEM:
                async with session.get(ESEARCH_URL, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        pmid_list = data.get("esearchresult", {}).get("idlist", [])
                        return pmid_list
                    else:
                        await asyncio.sleep(0.5)
        except aiohttp.ClientError:
            # 网络错误，等待重试
            await asyncio.sleep(1)
    # 重试失败返回空
    return []

async def fetch_pubmed_details(session, pmids, retries=3):
    if not pmids:
        return []
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }
    for attempt in range(retries):
        try:
            async with SEM:
                async with session.get(EFETCH_URL, params=params) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        root = ET.fromstring(text)
                        results = []
                        for article in root.findall(".//PubmedArticle"):
                            pmid_el = article.find(".//PMID")
                            pmid = pmid_el.text if pmid_el is not None else ""
                            abstract_text = ""
                            abstract_el = article.find(".//AbstractText")
                            if abstract_el is not None:
                                abstract_text = "".join(abstract_el.itertext()).strip()
                            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                            results.append((pmid, link, abstract_text))
                        return results
                    else:
                        print(resp.status)
                        # 非200状态码，等待重试
                        await asyncio.sleep(1)
        except aiohttp.ClientError:
            # 网络错误，等待重试
            await asyncio.sleep(1)
    # 重试失败返回空列表
    return []

async def fetch_variant_info(session, variant, cache):
    if variant in cache:
        return cache[variant]
    pmids = await fetch_pmids(session, variant)
    details = await fetch_pubmed_details(session, pmids)
    cache[variant] = details
    return details

async def main(input_csv, output_csv):
    # 读取CSV，提取variants
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

if __name__ == "__main__":
    asyncio.run(main("data/interim/test_variant.csv", "results/protein_pubmed.csv"))
