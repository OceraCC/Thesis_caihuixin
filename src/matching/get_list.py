import asyncio
import aiohttp
import xml.etree.ElementTree as ET

# PubMed E-utilities URLs
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

MAX_ARTICLES = 5
SEM = asyncio.Semaphore(3)  # Requests at a same time
API_KEY = "b8cdab5841380c33827fc8c164be118b0e08"

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
                        print(resp.status)
                        await asyncio.sleep(2)
        except aiohttp.ClientError:
            await asyncio.sleep(1)
    return []