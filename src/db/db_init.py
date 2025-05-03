import sqlite3
import pandas as pd

def init_relations_db(csv_path: str, db_path: str):
    df = pd.read_csv(csv_path)
    df.columns = ['gene', 'disease', 'score', 'association', 'pmid']
    conn = sqlite3.connect(db_path) 
    df.to_sql('relations', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()

def init_mesh_db(tsv_path: str, db_path: str):
    df = pd.read_csv(tsv_path, sep='\t')
    df.columns = ['DescriptorUI', 'DescriptorName', 'TreeNumbers']
    conn = sqlite3.connect(db_path)
    df.to_sql('mesh_info', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()

def init_gene_db(csv_path: str, db_path: str):
    df = pd.read_csv(csv_path)
    df.columns = ['Gene', 'Consequence', 'Transcript', 'VariationID', 'vcf', 'pmids', 'Links']
    conn = sqlite3.connect(db_path)
    df.to_sql('mutations', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()
