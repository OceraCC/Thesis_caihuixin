import sqlite3
import pandas as pd


def query_gene(gene, db_path):
    conn = sqlite3.connect(db_path)
    query = '''
        SELECT g.gene, g.disease AS mesh, m.DescriptorName AS disease, g.score, g.pmid, m.TreeNumbers AS classification
        FROM Grelations g
        JOIN mesh_info m ON g.disease = m.DescriptorUI
        WHERE g.gene = ?
    '''
    df = pd.read_sql_query(query, conn, params=(gene,))
    conn.close()
    return df

def query_gene_vcf(gene, db_path):
    conn = sqlite3.connect(db_path)
    query = '''
        SELECT m.Gene, m.Consequence, m.Transcript, m.VariationID, m.GWAS_DISEASE_or_TRAIT, m.GWAS_P_VALUE, m.GWAS_OR_or_BETA, m.vcf
        FROM mutations m
        WHERE m.Gene = ?
    '''
    df = pd.read_sql_query(query, conn, params=(gene,))
    df.columns = ['Gene', 'Consequence', 'Transcript ID', 'Variant ID', 'GWAS Disease or Trait', 'P-value', 'OR or BETA', 'VCF Info']
    conn.close()
    return df

def query_rsID(rsID, db_path):
    conn = sqlite3.connect(db_path)
    query = '''
        SELECT v.gene, v.rsID, v.disease AS mesh, m.DescriptorName AS disease, v.score, v.pmid, m.TreeNumbers AS classification
        FROM Vrelations v
        JOIN mesh_info m ON v.disease = m.DescriptorUI
        WHERE v.gene = ?
    '''
    df = pd.read_sql_query(query, conn, params=(rsID,))
    conn.close()
    return df

def query_loc(loc, db_path):
    conn = sqlite3.connect(db_path)
    query = '''
        SELECT m.Gene
        FROM mutations m
        WHERE m.loc = ?
    '''
    df = pd.read_sql_query(query, conn, params=(loc,))
    conn.close()
    return list(set(df["Gene"]))
