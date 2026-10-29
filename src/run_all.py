#!/usr/bin/env python3
"""One-command reproducible rebuild of the complete analytical deliverables."""
from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
for script in ['run_pipeline.py','prepare_counterfactual_pilot.py','extended_analysis.py','forensic_analysis.py','reconcile_outputs.py','operational_controls.py','investment_business_case.py','analyze_counterfactual_pilot.py']:
    print(f'\n=== Running {script} ===', flush=True)
    subprocess.run([sys.executable,str(ROOT/'src'/script)],cwd=ROOT,check=True)
print('\nAll pipeline stages completed successfully.')
