import csv
import asyncio
import aiohttp
import xml.etree.ElementTree as ET

from urllib.parse import quote

# PubMed E-utilities URLs
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

MAX_ARTICLES = 5
SEM = asyncio.Semaphore(3)  # Requests at a same time
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
                        await asyncio.sleep(2)
        except aiohttp.ClientError:
            await asyncio.sleep(1)
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
                            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                            results.append((pmid, link))
                        return results
                    else:
                        print(resp.status)
                        await asyncio.sleep(1)
        except aiohttp.ClientError:
            await asyncio.sleep(1)
    return []

async def fetch_variant_info(session, variant, cache):
    if variant in cache:
        return cache[variant]
    pmids = await fetch_pmids(session, variant)
    details = await fetch_pubmed_details(session, pmids)
    cache[variant] = details
    return details
