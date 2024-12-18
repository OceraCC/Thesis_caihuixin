import csv
import json
import zlib
import base64
from collections import defaultdict

def generate_html(entities_csv, variants_csv):
  ENTITIES_CSV = entities_csv
  VARIANTS_CSV = variants_csv

  entities_data = []
  disease_pmid_map = defaultdict(set)
  with open(ENTITIES_CSV, "r", encoding="utf-8", newline="") as f:
      reader = csv.DictReader(f)
      for row in reader:
          entities_data.append(row)
          pmid = row.get("pmid", "")
          diseases = row.get("disease", "").split(";")
          for disease in diseases:
              if disease.strip():
                  disease_pmid_map[disease.strip()].add(pmid)

  # Convert sets to lists for JSON serialization
  disease_pmid_map = {k: list(v) for k, v in disease_pmid_map.items()}

  # Load variants data and organize by PMIDs
  variants_data = []
  pmid_variant_map = defaultdict(list)
  all_amino_acids = set()
  with open(VARIANTS_CSV, "r", encoding="utf-8", newline="") as f:
      reader = csv.DictReader(f)
      for row in reader:
          # Replace newline characters with semicolons
          for key in ["pmids", "Links"]:
              if key in row and row[key]:
                  row[key] = row[key].replace("\n", ";")
          variants_data.append(row)
          pmids = row.get("pmids", "").split(";")
          for pmid in pmids:
              if pmid.strip():
                  pmid_variant_map[pmid.strip()].append(row)
          # Collect all amino acids from Protein Variation
          if row.get("Protein Variation"):
              parts = row["Protein Variation"].split(" ")
              for part in parts:
                  if part[:3].isalpha():
                      all_amino_acids.add(part[:3])

  # Compression 
  def compress_and_encode(data):
      compressed = zlib.compress(json.dumps(data, ensure_ascii=False).encode())
      return base64.b64encode(compressed).decode()

  compressed_disease_pmid = compress_and_encode(disease_pmid_map)
  compressed_pmid_variant = compress_and_encode(pmid_variant_map)
  compressed_amino_acids = compress_and_encode(list(all_amino_acids))

  html_part1 = """
  <!DOCTYPE html>
  <html>
  <head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Disease-Protein Variants</title>
  <script src="https://unpkg.com/react@17/umd/react.development.js"></script>
  <script src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/@babel/standalone@7/babel.min.js"></script>
  <script src="https://unpkg.com/pako@2.1.0/dist/pako.min.js"></script>
  <style>
  body {{ font-family: sans-serif; margin: 0; background: #f5f5f5; }}
  .container {{ width: 90%; margin: 40px auto; }}
  h1 {{ text-align: center; }}
  .filter-controls {{ margin: 10px 0; text-align: center; }}
  .disease-list {{ background: #fff; padding: 15px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
  .disease-item {{ cursor: pointer; margin: 5px 0; padding: 8px; border: 1px solid #ccc; border-radius: 3px; }}
  .disease-item:hover {{ background: #eee; }}
  .sidebar {{ position: fixed; right: 0; top: 0; height: 100%; width: 300px; background: #fff; box-shadow: -2px 0 10px rgba(0,0,0,0.2); padding: 20px; overflow-y: auto; display: none; }}
  .sidebar.active {{ display: block; }}
  .close-btn {{ cursor: pointer; color: red; float: right; }}
  .details-table {{ width: 100%; border-collapse: collapse; }}
  .details-table th, .details-table td {{ border-bottom: 1px solid #ddd; padding: 6px; text-align: left; }}
  </style>
  </head>
  <body>
  <div class="container">
    <h1>Disease-Protein Variants Relationship</h1>
    <div class="filter-controls">
      <label for="aminoFilter">Filter by Amino Acid:</label>
    </div>
    <div id="root"></div>
  </div>
  <div id="sidebar" class="sidebar">
    <span class="close-btn" onclick="closeSidebar()">&times;</span>
    <h2 id="sidebar-title"></h2>
    <div id="sidebar-content"></div>
  </div>
  <script>
  function decompressData(data) {{
      const binData = Uint8Array.from(atob(data), c => c.charCodeAt(0));
      return JSON.parse(pako.inflate(binData, {{ to: 'string' }}));
  }}
  entitiesData = decompressData("{entities_compressed}");
  variantsData = decompressData("{variants_compressed}");
  aminoAcids = decompressData("{amino_acids}");
  </script>
  """

  html_part1 = html_part1.format(entities_compressed=compressed_disease_pmid, 
                                variants_compressed=compressed_pmid_variant, 
                                amino_acids=compressed_amino_acids)

  html_part2 = """
  <script type="text/babel">
  const { useState, useEffect } = React;

  function App() {
      const [selectedAmino, setSelectedAmino] = useState(""); 
      const [filteredDiseases, setFilteredDiseases] = useState(Object.keys(entitiesData)); 

      const applyFilter = () => {
          console.log("Selected Amino Acid:", selectedAmino);
          if (selectedAmino) {
              const filtered = Object.keys(entitiesData).filter(disease => {
                  const pmids = entitiesData[disease];
                  return pmids.some(pmid => {
                      const variants = variantsData[pmid] || [];
                      return variants.some(variant => variant["Protein Variation"]?.includes(selectedAmino));
                  });
              });
              console.log("Filtered Diseases:", filtered);
              setFilteredDiseases(filtered); 
          }
      };

      const resetFilter = () => {
          console.log("Resetting filter");
          setSelectedAmino(""); 
          setFilteredDiseases(Object.keys(entitiesData)); 
      };

      const handleAminoChange = (e) => {
          const selectedValue = e.target.value;
          setSelectedAmino(selectedValue);
          console.log("Changed Amino Acid to:", selectedValue);
      };

      const handleDiseaseClick = (disease) => {
          const pmids = entitiesData[disease] || [];
          console.log("Selected Disease:", disease);
          console.log("PMIDs for Disease:", pmids);

          let detailsHTML = '<h3>Associated PMIDs and Variants</h3>';
          pmids.forEach(pmid => {
              detailsHTML += `<h4>PMID: <a href='https://pubmed.ncbi.nlm.nih.gov/${pmid}' target='_blank'>${pmid}</a></h4>`;
              detailsHTML += '<table class="details-table"><thead><tr><th>Gene</th><th>Consequence</th><th>Protein Variation</th></tr></thead><tbody>';
              const variants = variantsData[pmid] || [];
              variants.forEach(variant => {
                  detailsHTML += `<tr><td>${variant.Gene}</td><td>${variant.Consequence}</td><td>${variant["Protein Variation"]}</td></tr>`;
              });
              detailsHTML += '</tbody></table>';
          });
          document.getElementById('sidebar-title').innerText = disease;
          document.getElementById('sidebar-content').innerHTML = detailsHTML;
          document.getElementById('sidebar').classList.add('active');
      };

      return (
          <div>
              <div className="filter-controls">
                  <select onChange={handleAminoChange} value={selectedAmino}>
                      <option value="">Select Amino Acid</option>
                      {aminoAcids.sort().map(acid => (
                          <option key={acid} value={acid}>{acid}</option>
                      ))}
                  </select>
                  <button onClick={applyFilter}>Apply</button>
                  <button onClick={resetFilter}>Reset</button>
              </div>
              <div className="disease-list">
                  {filteredDiseases.map(disease => (
                      <div key={disease} className="disease-item" onClick={() => handleDiseaseClick(disease)}>
                          {disease}
                      </div>
                  ))}
              </div>
          </div>
      );
  }

  function closeSidebar() {
      document.getElementById('sidebar').classList.remove('active');
  }

  ReactDOM.render(<App />, document.getElementById('root'));

  </script>
  </body>
  </html>
  """
  
  with open("results/output.html", "w", encoding="utf-8") as f:
      f.write(html_part1 + html_part2)
