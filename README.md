# Epstein Data Set 9 Media Discovery Tool (FREE VERSION)

This repository provides a free, Python-based pipeline to identify under-discussed images and videos from the DOJ's Data Set 9 release (January 30, 2026) by using free web scraping techniques. No paid APIs or API keys are required.

Features
- Scrapes the DOJ Data Set 9 page to build a manifest of media files
- Downloads a configurable sample of media files
- Computes perceptual image hashes and metadata
- Uses free web scraping (Google, Reddit, Nitter) to estimate social presence
- Flags underreported media and generates a markdown report

Prerequisites
- Python 3.11+
- No API keys required (free tooling only)

Installation
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy example environment:
   ```bash
   cp .env.example .env
   ```

Usage (step-by-step)
1. Fetch the manifest (scrapes DOJ):
   ```bash
   python scripts/01_fetch_dataset9_manifest.py
   ```
2. Download sample media (controlled by `MAX_MEDIA_TO_DOWNLOAD` in `.env`):
   ```bash
   python scripts/02_download_sample_media.py
   ```
3. Compute hashes and thumbnails:
   ```bash
   python scripts/03_hash_media.py
   ```
4. Check social presence (Google / Reddit / Nitter):
   ```bash
   python scripts/04_check_social_presence.py
   ```
5. Generate final report:
   ```bash
   python scripts/05_generate_report.py
   ```

6. Run OCR on rendered pages (optional - requires Tesseract installed):
   ```bash
   # Install Tesseract on macOS (Homebrew): brew install tesseract
   python scripts/08_run_ocr.py
   ```

7. Cluster duplicate images:
   ```bash
   python scripts/09_cluster_duplicates.py
   ```

8. Resume and finish social checks (if interrupted):
   ```bash
   python scripts/10_finish_social_checks.py
   ```

9. Build searchable DB (FTS):
   ```bash
   python scripts/06_build_searchable_db.py
   ```

10. Filter underreported but interesting candidates:
   ```bash
   python scripts/07_filter_candidates.py
   ```

11. Orchestrate and resume the full pipeline:
   ```bash
   python run_pipeline.py
   ```

Review UI (local, free)
1. Install Flask in your venv:
   ```bash
   pip install Flask
   ```
2. Run the review app:
   ```bash
   python review_app/app.py
   ```
3. Open your browser at http://127.0.0.1:5000 to review filtered candidates, mark them reviewed, and export reviewed items.

This UI runs entirely locally and uses files produced by the pipeline. No paid services or external APIs are required.

Configuration
- `config/config.yaml` controls URLs, filters, nitter instances, search settings, and output paths.
- `.env` controls runtime limits such as `MAX_MEDIA_TO_DOWNLOAD` and `MAX_SOCIAL_SEARCHES_PER_HOUR`.

Output
- Manifest: `data/manifests/dataset9_media_manifest.csv`
- Hash database: `data/manifests/media_hashes.csv`
- Results (JSON/CSV): `data/results/underreported_media.json` / `data/results/underreported_media.csv`
- Final report: `data/results/FINAL_REPORT.md`

Limitations & Ethics
- Uses free web scraping only — counts are approximate and can change over time
- Respect robots.txt and rate limits; the pipeline includes delays and retries but you should be cautious when scaling
- Use responsibly and obey platform terms of service

Future Improvements
- Add video frame extraction and hashing
- Add better deduplication across similar images
- Optional authenticated API paths for more accurate counts (opt-in)

New in this iteration
- Face detection (OpenCV Haar cascades) and face-count metadata per image
- Lightweight NSFW heuristics (skin-fraction + OCR keyword checks)
- Reverse-image search helpers (anonymous image upload + best-effort checks on Google, Bing, Yandex)
- UI improvements: sorting, pagination, CSV/JSON export, one-click copy of suggested posts
- Tests and a full-feature test script to exercise face/skin/NSFW heuristics locally
- Optional: stronger NSFW model (NudeNet) support and a script to run model scoring across media

Optional NudeNet instructions
- Install: pip install nudenet
- Run model scoring: python scripts/13_run_nudennet.py
- Output: data/results/nudenet_scores.json and media CSV will be updated with nsfw_model_score/nsfw_model_label
 
Troubleshooting NudeNet / TensorFlow on macOS
- On macOS with newer Python versions, prebuilt TensorFlow wheels may not be available (Python 3.14 in particular). If you see "No module named 'tensorflow'" when instantiating the NudeClassifier, you have options:
   - Use a Python 3.10/3.11 virtualenv (recommended) and pip install `tensorflow-macos` / `tensorflow-metal` (Apple Silicon) or `tensorflow` for other platforms.
   - Use a Docker container with a known-good Python + TensorFlow image, then run `scripts/13_run_nudennet.py` inside the container.
   - If you prefer not to install TensorFlow, the pipeline will continue to use the lightweight heuristics (skin fraction + OCR keywords), which are conservative but avoid heavy installs.

   Docker (recommended for reproducible model runs)
   - Build and run the containerized NudeNet runner (recommended on macOS where native TF wheels are problematic):
      - Build + run (native arch): ./scripts/docker_run_nudennet.sh
      - On Apple Silicon to run an amd64 image (recommended to match common TF wheels): ./scripts/docker_run_nudennet.sh "--platform=linux/amd64"
      - The script will produce: data/results/nudenet_scores.json and update data/manifests/media_hashes.csv

   I added a Dockerfile that installs Python 3.11, TensorFlow 2.12 and NudeNet, copies the repo, and lets you run the scoring script inside a container. This is the simplest reliable route to run the model if you hit local TF installation problems.

Run NudeNet in CI (no local install required)
- If Docker or TensorFlow installation is a blocker, you can run the NudeNet scoring in GitHub Actions and download the outputs. I added a workflow `Run NudeNet NSFW Scoring` that runs on demand (Actions → Run workflow).
- To run: open the repository on GitHub, go to Actions → Run NudeNet NSFW Scoring → Run workflow. When it completes the job will upload `nudenet-results` as an artifact containing `data/results/nudenet_scores.json` and `data/manifests/media_hashes.csv`.


   Terminal troubleshooting (quick checks)
   - If your terminal or integrated terminal in VS Code becomes unresponsive, try these quick steps:
      1. Close and reopen the terminal window (or reload VS Code window: Cmd+Shift+P → "Developer: Reload Window").
      2. Reboot the machine if terminal behavior persists.
      3. Run the helper: bash scripts/terminal_health_check.sh — it checks Python, venv, disk, memory, running Python processes, Docker and listening ports and prints actionable output.
      4. Check Activity Monitor (macOS) for runaway processes and kill them if needed.
      5. If Docker is needed, ensure Docker Desktop is running.

Legal Disclaimer
This tool is provided for research and journalistic purposes. The authors are not responsible for misuse.

---
Generated by the Epstein Media Finder - Free Version
