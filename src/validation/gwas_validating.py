import pandas as pd

def gwas_merge(input_csv):
    
    my_variants = pd.read_csv(input_csv)
    gwas = pd.read_csv("database/gwas.csv", sep=",")
    gwas_filtered = gwas[["SNPS", "DISEASE/TRAIT", "P-VALUE", "OR or BETA"]].dropna()
    gwas_filtered.columns = ["rsID", "GWAS_Disease", "GWAS_P", "GWAS_OR"]

    merged = pd.merge(my_variants, gwas_filtered, left_on="Variation ID", right_on="rsID", how="left")

    output_csv = "results/gwas_merged.csv"
    merged.to_csv(output_csv, index=False)

    return merged
