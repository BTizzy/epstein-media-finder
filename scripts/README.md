# Scripts Directory

This folder contains the step-by-step pipeline scripts for the Epstein Media Finder tool:

- `01_fetch_dataset9_manifest.py`: Scrapes DOJ Data Set 9 file listings and builds a manifest.
- `02_download_sample_media.py`: Downloads sample media files for analysis.
- `03_hash_media.py`: Computes perceptual hashes and extracts metadata from images.
- `04_check_social_presence.py`: Checks social media presence using free web scraping.
- `05_generate_report.py`: Generates a markdown report of underreported media files.

Run each script in order for a complete analysis pipeline. See the main README for details.