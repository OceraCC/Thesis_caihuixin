#!/usr/bin/env python3
import subprocess
import os

def run_vep(input_vcf, output_vcf):
    input_vcf = os.path.abspath(input_vcf)
    output_vcf = os.path.abspath(output_vcf)

    cmd = [
        "vep",
        "--input_file", input_vcf,
        "--output_file", output_vcf,
        '--vcf',  
        '--cache',  
        '--offline',  
        '--symbol',  
        '--force_overwrite', 
        '--check_existing', 
        '--fork', '30',
        '--no_stats'
    ]

    subprocess.check_call(cmd)
    