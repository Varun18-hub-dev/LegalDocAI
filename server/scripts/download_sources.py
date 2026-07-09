"""
LegalDocAI - PDF Downloader
Downloads legal documents (Constitution, BNS, BNSS, BSA) from government sources.
"""

import sys
import time
import requests
from pathlib import Path
from tqdm import tqdm

# Add parent to path so we can import config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import DATA_SOURCES, RAW_DATA_DIR


def download_pdf(name: str, source: dict) -> Path:
    """
    Download a single PDF from the given source config.
    Tries primary URL first, falls back to backup URL.
    """
    output_path = RAW_DATA_DIR / source["filename"]

    # Skip if already downloaded
    if output_path.exists() and output_path.stat().st_size > 10000:
        print(f"  ✅ Already exists: {source['filename']} ({output_path.stat().st_size / 1024:.0f} KB)")
        return output_path

    # Try primary URL, then backup
    urls_to_try = [source["url"]]
    if "backup_url" in source:
        urls_to_try.append(source["backup_url"])

    for url in urls_to_try:
        try:
            print(f"  ⬇️  Downloading from: {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()

            # Get total file size for progress bar
            total_size = int(response.headers.get("content-length", 0))

            with open(output_path, "wb") as f:
                if total_size > 0:
                    with tqdm(total=total_size, unit="B", unit_scale=True, desc=source["filename"]) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                            pbar.update(len(chunk))
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

            file_size = output_path.stat().st_size
            if file_size > 10000:  # At least 10KB = valid PDF
                print(f"  ✅ Downloaded: {source['filename']} ({file_size / 1024:.0f} KB)")
                return output_path
            else:
                print(f"  ⚠️  File too small ({file_size} bytes), trying backup...")
                output_path.unlink(missing_ok=True)

        except requests.RequestException as e:
            print(f"  ❌ Failed from {url}: {e}")
            output_path.unlink(missing_ok=True)
            time.sleep(2)

    print(f"  ❌ FAILED to download: {name}")
    return None


def download_all():
    """Download all legal documents defined in config."""
    print("=" * 60)
    print("📥 LegalDocAI - Document Downloader")
    print("=" * 60)

    results = {"success": [], "failed": []}

    for key, source in DATA_SOURCES.items():
        print(f"\n📄 {source['name']}")
        result = download_pdf(key, source)
        if result:
            results["success"].append(source["name"])
        else:
            results["failed"].append(source["name"])

    # Summary
    print("\n" + "=" * 60)
    print("📊 Download Summary")
    print("=" * 60)
    print(f"  ✅ Success: {len(results['success'])}")
    for name in results["success"]:
        print(f"     • {name}")

    if results["failed"]:
        print(f"  ❌ Failed: {len(results['failed'])}")
        for name in results["failed"]:
            print(f"     • {name}")
        print("\n  💡 For failed downloads, manually download the PDFs and place them in:")
        print(f"     {RAW_DATA_DIR}")

    return results


if __name__ == "__main__":
    download_all()
