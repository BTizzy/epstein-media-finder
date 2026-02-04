"""
Orchestrator to run the full pipeline with resume support.
"""
import sys
import os
from subprocess import run
from utils.state_manager import get, set_

STEPS = [
    ('fetch', ['python', 'scripts/01_fetch_dataset9_manifest.py']),
    ('download', ['python', 'scripts/02_download_sample_media.py']),
    ('hash', ['python', 'scripts/03_hash_media.py']),
    ('ocr', ['python', 'scripts/08_run_ocr.py']),
    ('social', ['python', 'scripts/10_finish_social_checks.py']),
    ('filter', ['python', 'scripts/07_filter_candidates.py']),
    ('db', ['python', 'scripts/06_build_searchable_db.py']),
]

def run_step(step_cmd):
    print(f"Running: {' '.join(step_cmd)}")
    r = run(step_cmd)
    return r.returncode == 0

def main():
    for name, cmd in STEPS:
        completed = get(f'step_{name}', False)
        if completed:
            print(f"Skipping {name} (already completed)")
            continue

        ok = run_step(cmd)
        if not ok:
            print(f"Step {name} failed - stopping. You can re-run run_pipeline.py to resume.")
            return

        set_(f'step_{name}', True)

    print('✅ Pipeline complete')

if __name__ == '__main__':
    main()
