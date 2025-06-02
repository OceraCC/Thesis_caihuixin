import pandas as pd

def gwas_merge(input_csv):
    
    my_variants = pd.read_csv(input_csv)
    gwas = pd.read_csv("database/gwas.csv", sep=",")
    gwas_filtered = gwas[["SNPS", "DISEASE_or_TRAIT", "P_VALUE", "OR_or_BETA"]].dropna()
    gwas_filtered.columns = ["rsID", "GWAS_DISEASE_or_TRAIT", "GWAS_P_VALUE", "GWAS_OR_or_BETA"]

    merged = pd.merge(my_variants, gwas_filtered, left_on="VariationID", right_on="rsID", how="left")
    merged = merged.drop(columns=["rsID"])
    merged["location"] = merged["vcf"].apply(lambda x: x.split('\t')[0] + ":" + x.split('\t')[1])
    output_csv = "results/gwas_merged.csv"
    merged.to_csv(output_csv, index=False)

    return merged