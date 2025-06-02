import ast
import streamlit as st
import pandas as pd
from collections import defaultdict, Counter
import os
from collections import defaultdict
from db.db_query import *
from streamlit_agraph import agraph, Node, Edge, Config

# Disease map
CATEGORY_MAP = {
    "C01": "Bacterial Infections and Mycoses",
    "C02": "Virus Diseases",
    "C03": "Parasitic Diseases",
    "C04": "Neoplasms",
    "C05": "Musculoskeletal Diseases",
    "C06": "Digestive System Diseases",
    "C07": "Stomatognathic Diseases",
    "C08": "Respiratory Tract Diseases",
    "C09": "Otorhinolaryngologic Diseases",
    "C10": "Nervous System Diseases",
    "C11": "Eye Diseases",
    "C12": "Male Urogenital Diseases",
    "C13": "Female Urogenital Diseases and Pregnancy Complications",
    "C14": "Cardiovascular Diseases",
    "C15": "Hemic and Lymphatic Diseases",
    "C16": "Congenital, Hereditary, and Neonatal Diseases and Abnormalities",
    "C17": "Skin and Connective Tissue Diseases",
    "C18": "Nutritional and Metabolic Diseases",
    "C19": "Endocrine System Diseases",
    "C20": "Immunologic Diseases",
    "C21": "Disorders of Environmental Origin",
    "C22": "Animal Diseases",
    "C23": "Pathological Conditions, Signs and Symptoms",
    "C24": "Occupational Diseases",
    "C25": "Chemically-Induced Disorders",
    "C26": "Wounds and Injuries",
    "F03": "Mental Disorders"
}

def get_category(tree_number):
    if not tree_number:
        return "Unknown"
    for prefix in tree_number:
        if prefix in CATEGORY_MAP:
            return CATEGORY_MAP[prefix]
    return "Unknown"

def score_to_size(score):
    if score < 0.9:
        return 7
    else:
        adjusted = (score - 0.9) / 0.1
        size = 6 + (adjusted ** 3) * 10
        return size
    
def build_graph(gene_name, df_gene):
    # 统计每个分类码出现次数
    code_lists = df_gene['classification'].apply(lambda x: x if isinstance(x, list) else [])
    code_counts = Counter([c for codes in code_lists for c in codes])

    nodes = []
    edges = []
    seen_nodes = set()

    # 基因节点
    gene_link = f"https://meshb.nlm.nih.gov/record/ui?ui={gene_name}"
    nodes.append(Node(id=gene_name, label=gene_name, size=10, color="#035DA6", link=gene_link))
    seen_nodes.add(gene_name)

    for _, row in df_gene.iterrows():
        dis = row['disease']
        codes = row['classification']
        score = row['score']

        # 确保疾病节点只添加一次
        if dis not in seen_nodes and dis!="Neoplasms" :
            nodes.append(Node(id=dis, label=dis, size=score_to_size(score), title=score))
            seen_nodes.add(dis)

        # 分离共享与唯一分类
        shared = [c for c in codes if code_counts[c] > 1]
        unique = [c for c in codes if code_counts[c] == 1]

        if shared:
            # 添加共享分类节点并从基因连接
            for sc in shared:
                sc_id = f"cat_{sc}"
                if sc_id not in seen_nodes:
                    if sc in CATEGORY_MAP:
                        nodes.append(Node(id=sc_id, label=CATEGORY_MAP[sc], color="#497BEF", size=10))
                        edges.append(Edge(source=gene_name, target=sc_id))
                    else:
                        nodes.append(Node(id=sc_id, label='unknown', color="#858FD4", size=10))
                        edges.append(Edge(source=gene_name, target=sc_id))
                    seen_nodes.add(sc_id)
            # 添加唯一分类节点，并连接到共享分类，再连疾病
            if unique:
                # 先添加唯一分类节点
                for uc in unique:
                    uc_id = f"cat_{uc}"
                    if uc_id not in seen_nodes:
                        if sc in CATEGORY_MAP:
                            nodes.append(Node(id=uc_id, label=CATEGORY_MAP.get(uc, uc), color="#497BEF", size=10))
                        else:
                            nodes.append(Node(id=sc_id, label='unknown', color="#858FD4", size=10))
                        seen_nodes.add(uc_id)
                    # 连接 shared -> unique
                    for sc in shared:
                        edges.append(Edge(source=f"cat_{sc}", target=uc_id))
                    # 再连接 unique -> 疾病
                    edges.append(Edge(source=uc_id, target=dis))
            else:
                # 如果只有共享分类，直接连接 shared -> 疾病
                for sc in shared:
                    edges.append(Edge(source=f"cat_{sc}", target=dis))
        else:
            # 无共享分类，合并为一个节点
            comp_id = "cat_" + "_".join(codes)
            if comp_id not in seen_nodes:
                comp_label = "/".join([CATEGORY_MAP[c] for c in codes if c in CATEGORY_MAP])
                nodes.append(Node(id=comp_id, label=comp_label, color="#497BEF", size=10))
                seen_nodes.add(comp_id)
            edges.append(Edge(source=gene_name, target=comp_id))
            edges.append(Edge(source=comp_id, target=dis))

    return nodes, edges

# 页面内容
st.set_page_config(
    page_icon="🧬",
    layout="wide"
    )
st.title("Gene-Disease Association Query Page")
for key, default in {
    "queried_genes": [],
    "gene_name": "",
    "df_gene": pd.DataFrame(),
    "df_rsID": pd.DataFrame(),
    "df_gene_vcf": pd.DataFrame()
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# 定位数据库
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
db_path = os.path.join(project_root, 'database', 'data.db')
    
loc = st.text_input("Type a location(e.g. chr1:18477480)")

if st.button("Query", key="loc"):
    st.session_state["queried_genes"] = query_loc(loc, db_path)
        
if st.session_state["queried_genes"]:
    for gene in st.session_state.get("queried_genes", []):
        cols = st.columns([3, 1])
        with cols[0]:
            st.write(gene)
        with cols[1]:
            if st.button("Choose", key=gene):
                st.session_state["gene_name"] = gene
                st.session_state["queried_genes"] = ""
                        
gene_name = st.text_input("Type a gene", value=st.session_state.get("gene_name", ""))

if st.button("Query", key="gene"):
    
    df_gene = query_gene(gene_name, db_path)
    df_rsID = query_rsID(gene_name, db_path)
    df_gene_vcf = query_gene_vcf(gene_name, db_path)
    
    st.session_state["df_gene"] = df_gene
    st.session_state["df_rsID"] = df_rsID
    st.session_state["df_gene_vcf"] = df_gene_vcf
    st.session_state["gene_name"] = gene_name
    
    if df_gene.empty or df_gene_vcf.empty:
            st.warning(f"{gene_name} Not Found")
        
if "df_gene" in st.session_state and not st.session_state["df_gene"].empty:
    df_gene = st.session_state["df_gene"]
    df_gene_vcf = st.session_state["df_gene_vcf"]
    df_rsID = st.session_state["df_rsID"]
    
    try:           
        st.success(f"{len(df_gene)} diseases in total")
        
        df_gene['classification'] = df_gene['classification'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        df_gene['Category'] = df_gene['classification'].apply(get_category)
        
        st.subheader("Disease Network Visualization")

        nodes, edges = build_graph(st.session_state['gene_name'], df_gene)
        config = Config(
            width=1100, 
            height=700,
            directed=True, 
            physics=True, 
            hierarchical=True,
            interaction={"zoomView": False, 
                            "dragView": True, 
                            "dragNodes": True, 
                            "hover": True}
        )
        selected = agraph(nodes=nodes, edges=edges, config=config)
        # 选中节点后展示链接或提示
        if selected:
            match = df_gene[df_gene['disease'] == selected]
            if not match.empty:
                mesh_str = match.iloc[0]['mesh']
                if isinstance(mesh_str, str) and mesh_str.startswith("MESH:"):
                    mesh_code = mesh_str.split(":")[1]
                    mesh_link = f"https://meshb.nlm.nih.gov/record/ui?ui={mesh_code}"
                    st.markdown(f"🔗 [{selected}]({mesh_link})", unsafe_allow_html=True)
                else:
                    st.info(f"Node `{selected}` has no mesh info")

            
        st.subheader("Variants Information")
        diseases = set(df_gene["disease"])
        df_gene_vcf["disease"] = [diseases] * len(df_gene_vcf)
        if len(df_rsID) > 0:
            ID_disease = defaultdict(set)
            for k, v in zip(df_rsID["rsID"], df_rsID["disease"]):
                ID_disease[k].add(v)
            df_gene_vcf["disease"] = df_gene_vcf["Variant ID"].apply(lambda x: ID_disease.get(x, diseases))
        
        st.dataframe(df_gene_vcf)

    except Exception as e:
        st.error(f"Failed: {e}")
        

