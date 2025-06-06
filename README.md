# A Mutation–Disease Association Analysis Tool

This is an end-to-end bioinformatics tool for identifying disease associations from human genetic variants. 

## Installation
1. Clone the repository:

```bash
git clone https://github.com/OceraCC/Thesis_caihuixin.git
cd Thesis_caihuixin
```

2. Install dependencies:

```bash
pip install -r requirement.txt
```

3. Install Ensembl VEP and ensure it is in your PATH(version 114):

https://www.ensembl.org/info/docs/tools/vep/index.html

4. Install cache

```bash
perl INSTALL.pl --AUTO c --SPECIES homo_sapiens --ASSEMBLY GRCh38 --CACHE_VERSION 114 --NO_HTSLIB
## make sure you're under your vep folder
```

## Usage

```bash
python src/main.py input_file_path
```
