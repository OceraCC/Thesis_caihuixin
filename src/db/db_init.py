import sqlite3
import pandas as pd

def init_Vrelations_db(csv_path: str, db_path: str):
    df = pd.read_csv(csv_path)
    df.columns = ['rsID', 'gene', 'disease', 'score', 'association', 'pmid']
    conn = sqlite3.connect(db_path) 
    df.to_sql('Vrelations', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()

def init_Grelations_db(csv_path: str, db_path: str):
    df = pd.read_csv(csv_path)
    df.columns = ['gene', 'disease', 'score', 'association', 'pmid']
    conn = sqlite3.connect(db_path) 
    df.to_sql('Grelations', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()

def init_mesh_db(tsv_path: str, db_path: str):
    df = pd.read_csv(tsv_path, sep='\t')
    df.columns = ['DescriptorUI', 'DescriptorName', 'TreeNumbers']
    conn = sqlite3.connect(db_path)
    df.to_sql('mesh_info', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()

def init_variant_db(csv_path: str, db_path: str):
    df = pd.read_csv(csv_path)
    df.columns = ['Gene', 'Consequence', 'Transcript', 'VariationID', 'vcf', 'pmids', "GWAS_DISEASE_or_TRAIT", "GWAS_P_VALUE", "GWAS_OR_or_BETA", "loc"]
    conn = sqlite3.connect(db_path)
    df.to_sql('mutations', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()
