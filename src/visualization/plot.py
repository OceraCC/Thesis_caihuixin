import csv
import json
import zlib
import base64
from collections import defaultdict

def load_mesh_info(mesh_tsv_path="database/mesh2025.tsv"):
    mesh_map = {}
    with open(mesh_tsv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader, None)  # 跳过表头
        for row in reader:
            if len(row) < 3:
                continue
            descriptor_ui = row[0].strip()
            descriptor_name = row[1].strip()
            tree_numbers = row[2].strip()

            mesh_id = f"MESH:{descriptor_ui}"

            classification = ""
            for tn in tree_numbers.split("|"):
                tn = tn.strip()
                if tn.startswith("C"):
                    dot_pos = tn.find(".")
                    if dot_pos != -1:
                        classification = tn[:dot_pos]
                    else:
                        classification = tn
                    break

            mesh_map[mesh_id] = {
                "name": descriptor_name,
                "classification": classification,
                "allTreeNumbers": tree_numbers
            }
    return mesh_map

def generate_html(relations_csv, variants_csv):
    RELATIONS_CSV = relations_csv
    VARIANTS_CSV = variants_csv

    mesh_dict = load_mesh_info("database/mesh2025.tsv")

    # 读取 relations_csv
    disease_pmid_map = defaultdict(set)
    with open(RELATIONS_CSV, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pmid = row.get("pmid", "")
            disease = row.get("disease", "")
            disease_pmid_map[disease].add(pmid)
    disease_pmid_map = {k: list(v) for k, v in disease_pmid_map.items()}

    # 整理 disease_info_map
    disease_info_map = {}
    for disease_id, pmids in disease_pmid_map.items():
        mesh_info = mesh_dict.get(disease_id, {})
        disease_name = mesh_info.get("name", disease_id)
        classification = mesh_info.get("classification", "unknown")
        disease_info_map[disease_id] = {
            "name": disease_name,
            "classification": classification,
            "pmids": pmids
        }
        
    # 读取 variants_csv
    pmid_variant_map = defaultdict(list)
    with open(VARIANTS_CSV, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 将换行符替换为分号，保证 pmids 与 Links 字段不会因为换行导致解析错误
            for key in ["pmids", "Links"]:
                if key in row and row[key]:
                    row[key] = row[key].replace("\n", ";")
            pmids = row.get("pmids", "").split(";")
            for pmid in pmids:
                pmid = pmid.strip()
                if pmid:
                    pmid_variant_map[pmid].append(row)


    def compress_and_encode(data):
        compressed = zlib.compress(json.dumps(data, ensure_ascii=False).encode())
        return base64.b64encode(compressed).decode()

    compressed_disease_info = compress_and_encode(disease_info_map)
    compressed_pmid_variant = compress_and_encode(pmid_variant_map)

    html_part1 = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Disease-Variants</title>
    <script src="https://unpkg.com/react@17/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone@7/babel.min.js"></script>
    <script src="https://unpkg.com/pako@2.1.0/dist/pako.min.js"></script>
    <style>
    body {{
      font-family: sans-serif;
      margin: 0;
      background: #f5f5f5;
    }}
    .container {{
      width: 90%;
      margin: 40px auto;
    }}
    h1 {{
      text-align: center;
    }}
    .filter-controls {{
      margin: 10px 0;
      text-align: center;
      position: relative;
    }}
    .reset-btn {{
      float: right;
      font-size: 1.2em;
      margin-right: 40px;
      padding: 6px 12px;
      cursor: pointer;
    }}

    .disease-list {{
      background: #fff;
      padding: 15px;
      border-radius: 5px;
      box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }}
    .disease-item {{
      cursor: pointer;
      margin: 5px 0;
      padding: 8px;
      border: 1px solid #ccc;
      border-radius: 3px;
    }}
    .disease-item:hover {{
      background: #eee;
    }}
    .sidebar {{
      position: fixed;
      right: 0;
      top: 0;
      height: 100%;
      width: 300px;
      background: #fff;
      box-shadow: -2px 0 10px rgba(0,0,0,0.2);
      padding: 20px;
      overflow-y: auto;
      display: none;
    }}
    .sidebar.active {{
      display: block;
    }}
    .close-btn {{
      cursor: pointer;
      color: red;
      float: right;
    }}
    .details-table {{
      width: 100%;
      border-collapse: collapse;
    }}
    .details-table th, .details-table td {{
      border-bottom: 1px solid #ddd;
      padding: 6px;
      text-align: left;
    }}
    .classification-sidebar {{
      position: fixed;
      left: 0;
      top: 0;
      height: 100%;
      width: 220px;
      background: #fff;
      box-shadow: 2px 0 10px rgba(0,0,0,0.2);
      padding: 20px;
      overflow-y: auto;
    }}
    .classification-item {{
      cursor: pointer;
      margin: 5px 0;
      padding: 8px;
      border: 1px solid #ccc;
      border-radius: 3px;
    }}
    .classification-item:hover {{
      background: #eee;
    }}
    .selected-classification {{
      background: #ccc;
      font-weight: bold;
    }}
    .content-container {{
      margin-left: 240px;
      padding: 20px;
    }}

    /* 小窗（popover）样式 */
    .vcf-popover {{
      position: absolute;
      min-width: 200px;
      max-width: 350px;
      background: #fff;
      border: 1px solid #ccc;
      padding: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.2);
      z-index: 9999;
      display: none; /* 初始隐藏 */
      border-radius: 4px;
    }}
    .vcf-popover-header {{
      font-weight: bold;
      margin-bottom: 6px;
    }}
    .vcf-popover-close {{
      cursor: pointer;
      float: right;
      font-size: 1.1em;
      font-weight: normal;
      margin-left: 8px;
      color: #555;
    }}
    .vcf-popover-close:hover {{
      color: #e00;
    }}
    .vcf-popover-body {{
      white-space: pre-wrap; /* 保留换行等 */
      word-wrap: break-word; /* 让长字符串折行 */
    }}
    .vcf-link {{
      text-decoration: underline;
      cursor: pointer;
      color: #0073e6;
    }}
    .vcf-link:hover {{
      color: #005bb5;
    }}
    </style>
    </head>
    <body>

    <!-- 左侧分类边栏 -->
    <div class="classification-sidebar">
      <h3>Classification</h3>
      <div id="classification-list"></div>
    </div>

    <div id="sidebar" class="sidebar">
      <span class="close-btn" onclick="closeSidebar()">&times;</span>
      <h2 id="sidebar-title"></h2>
      <div id="sidebar-content"></div>
    </div>
    
    <!-- 右侧展示区 -->
    <div class="container content-container">
      <h1>Disease-Gene Variation Relationship</h1>
      <div class="filter-controls">
        <button class="reset-btn" id="reset-button">Reset</button>
      </div>

      <div id="root"></div>
    </div>
    
    <!-- 只创建一个通用的 popover，用时再改内容、改位置 -->
    <div id="vcf-popover" class="vcf-popover">
      <div class="vcf-popover-header">
        <span>VCF Info</span>
        <span class="vcf-popover-close" onclick="closeVCFPopover()">×</span>
      </div>
      <div id="vcf-popover-body" class="vcf-popover-body"></div>
    </div>

    <script>
    function decompressData(data) {{
        const binData = Uint8Array.from(atob(data), c => c.charCodeAt(0));
        return JSON.parse(pako.inflate(binData, {{ to: 'string' }}));
    }}

    diseaseInfoMap = decompressData("{compressed_disease_info}");
    variantsData = decompressData("{compressed_pmid_variant}");

    const classificationNameMap = {{
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
        "C26": "Wounds and Injuries"
    }};

    function closeSidebar() {{
        document.getElementById('sidebar').classList.remove('active');
    }}

    // VCF popover相关
    function closeVCFPopover() {{
        const popover = document.getElementById('vcf-popover');
        popover.style.display = "none";
    }}

    function showVCFPopover(element, vcfText) {{
        const popover = document.getElementById('vcf-popover');
        const body = document.getElementById('vcf-popover-body');

        body.textContent = vcfText || "";

        // 先显示，先隐藏可见性，这样能计算到 popover的 offsetWidth / offsetHeight
        popover.style.display = "block";
        popover.style.visibility = "hidden";

        // 强制刷新一次DOM，让浏览器计算offsetWidth
        popover.offsetWidth;  // 读一下，强制重排

        const popoverWidth = popover.offsetWidth;
        // 让它的“右边”贴着右侧sidebar的“左边线” (即 window.innerWidth - 300)
        const rightSidebarLeft = window.innerWidth - 300;
        
        // 获取被点击元素的位置信息
        const rect = element.getBoundingClientRect();
        // 计算 top 位置：让 popover 的 top 与点击元素的 top 大致相同
        const top = window.scrollY + rect.top;
        // 计算 left 位置：即 “sidebar左边线 - popover宽度”
        const left = rightSidebarLeft - popoverWidth;

        // 设置最终定位
        popover.style.top = top + "px";
        popover.style.left = left + "px";
        // 最后让它可见
        popover.style.visibility = "visible";
    }}
    </script>
    """

    # 前端 React 代码和事件处理逻辑
    html_part2 = r"""
    <script type="text/babel">
    const { useState, useEffect } = React;

    function App() {
        const allDiseaseIds = Object.keys(diseaseInfoMap);

        const [selectedClassification, setSelectedClassification] = useState("");
        const [filteredDiseases, setFilteredDiseases] = useState(allDiseaseIds);

        const applyFilter = () => {
            let result = allDiseaseIds;
            if (selectedClassification) {
                result = result.filter(did => diseaseInfoMap[did].classification === selectedClassification);
            }
            setFilteredDiseases(result);
        };

        const resetFilter = () => {
            setSelectedClassification("");
            setFilteredDiseases(allDiseaseIds);
        };

        // 给reset-button绑定点击事件
        useEffect(() => {
            const resetBtn = document.getElementById("reset-button");
            if (resetBtn) {
                resetBtn.onclick = () => {
                    resetFilter();
                };
            }
        }, []);

        const handleDiseaseClick = (diseaseId) => {
            const info = diseaseInfoMap[diseaseId];
            if (!info) return;

            let detailsHTML = '<h3>Associated PMIDs and Variants</h3>';
            (info.pmids || []).forEach(pmid => {
                detailsHTML += `<h4>PMID: <a href='https://pubmed.ncbi.nlm.nih.gov/${pmid}' target='_blank'>${pmid}</a></h4>`;
                detailsHTML += '<table class="details-table"><thead><tr><th>Gene</th><th>Consequence</th><th>Variation ID</th></tr></thead><tbody>';
                const variants = variantsData[pmid] || [];
                variants.forEach(variant => {
                    // 对 vcf 的引号做转义，避免 HTML 拼接时出错
                    const vcfValue = (variant.vcf || "")
                      .replace(/"/g, '&quot;')
                      .replace(/'/g, '&#39;');

                    detailsHTML += "<tr><td>";

                    // 用 data-vcf 存放真实文本，通过点击事件展示弹窗
                    detailsHTML += "<span class='vcf-link' data-vcf='" + vcfValue + "'>" +
                                   (variant["Gene"] || "") + "</span>" + "</td><td>";
                    
                    detailsHTML += (variant["Consequence"] || "") + "</td><td>" +
                                   (variant["Variaion ID"] || "") + "</td></tr>";
                                   
                });
                detailsHTML += '</tbody></table>';
            });

            document.getElementById('sidebar-title').innerText = info.name || diseaseId;
            document.getElementById('sidebar-content').innerHTML = detailsHTML;
            document.getElementById('sidebar').classList.add('active');

            // sidebar-content 添加事件委托，用于点击 .vcf-link 时展示 popover
            const sidebarContent = document.getElementById('sidebar-content');
            if (sidebarContent) {
                sidebarContent.addEventListener('click', function(e) {
                    if (e.target && e.target.classList.contains('vcf-link')) {
                        const vcf = e.target.getAttribute('data-vcf') || '';
                        showVCFPopover(e.target, vcf);
                    }
                });
            }
        };

        const handleClassificationClick = (cls) => {
            setSelectedClassification(cls);
            let result = allDiseaseIds.filter(did => diseaseInfoMap[did].classification === cls);
            setFilteredDiseases(result);
        };

        // 监听 classificationSelect 事件
        useEffect(() => {
            function onClassificationSelect(e) {
                const cls = e.detail;
                handleClassificationClick(cls);
            }
            window.addEventListener("classificationSelect", onClassificationSelect);
            return () => window.removeEventListener("classificationSelect", onClassificationSelect);
        }, []);

        return (
            <div>

                <div className="disease-list">
                    {filteredDiseases.map(did => {
                        const info = diseaseInfoMap[did];
                        const displayName = info ? info.name : did;
                        return (
                            <div key={did} className="disease-item" onClick={() => handleDiseaseClick(did)}>
                                {displayName}
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    }

    function ClassificationList() {
        const [classifications, setClassifications] = useState([]);
        const [selectedCls, setSelectedCls] = useState("");

        useEffect(() => {
            const clsSet = new Set();
            Object.keys(diseaseInfoMap).forEach(did => {
                const c = diseaseInfoMap[did].classification;
                if (c) clsSet.add(c);
            });
            const sorted = Array.from(clsSet).sort();
            setClassifications(sorted);
        }, []);

        // 当事件发生时，高亮分类
        useEffect(() => {
            function handleChange(e) {
                setSelectedCls(e.detail);
            }
            window.addEventListener("classificationSelect", handleChange);
            return () => {
                window.removeEventListener("classificationSelect", handleChange);
            };
        }, []);

        const handleClick = (cls) => {
            if (window.appHandleClassificationClick) {
                window.appHandleClassificationClick(cls);
            }
        };

        return (
            <div>
                {classifications.map(cls => {
                    const officialName = classificationNameMap[cls] || cls;
                    const isSelected = (cls === selectedCls);
                    return (
                        <div
                            key={cls}
                            className={"classification-item" + (isSelected ? " selected-classification" : "")}
                            onClick={() => handleClick(cls)}
                        >
                            {officialName}
                        </div>
                    );
                })}
            </div>
        );
    }

    ReactDOM.render(<App />, document.getElementById('root'));
    ReactDOM.render(<ClassificationList />, document.getElementById('classification-list'));

    window.appHandleClassificationClick = function(cls) {
        const event = new CustomEvent("classificationSelect", { detail: cls });
        window.dispatchEvent(event);
    };
    </script>
    </body>
    </html>
    """

    with open("results/output.html", "w", encoding="utf-8") as f:
        f.write(html_part1 + html_part2)
