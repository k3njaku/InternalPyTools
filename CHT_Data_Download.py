import os
import csv
import requests
from urllib.parse import urlsplit

try:
    import tkinter as tk
    from tkinter import filedialog
except Exception:  # pragma: no cover - GUI may not be available
    tk = None

BASE_URL = "https://apptrack.chiraagtracker.com/"
DOWNLOAD_ROOT = os.path.join(os.path.dirname(__file__), 'downloads')


def sanitize(value: str) -> str:
    """Sanitize path components and file names."""
    return ''.join(c if c.isalnum() or c in ('-', '_') else '_' for c in value.strip())


def ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def download_file(url: str, dest_path: str) -> None:
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Downloaded {dest_path}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")


def process_csv(csv_path: str) -> None:
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            extra2 = sanitize(row.get('Extra2', 'Unknown') or 'Unknown')
            extra5 = sanitize(row.get('Extra5', 'Unknown') or 'Unknown')
            company = sanitize(row.get('CompanyName', 'Unknown') or 'Unknown')
            prospect = sanitize(row.get('ProspectName', 'Unknown') or 'Unknown')

            base_dir = os.path.join(DOWNLOAD_ROOT, extra2, extra5)
            ensure_directory(base_dir)

            for header, value in row.items():
                if value and 'assets/' in value and not value.startswith('http'):
                    url = BASE_URL + value.lstrip('/')
                    extension = os.path.splitext(urlsplit(url).path)[1]
                    filename = f"{company}-{prospect}-{sanitize(header)}{extension}"
                    dest_path = os.path.join(base_dir, filename)
                    if not os.path.exists(dest_path):
                        download_file(url, dest_path)


def main():
    default_csv = os.path.join(os.path.dirname(__file__), 'output.csv')
    csv_path = default_csv
    if tk:
        root = tk.Tk()
        root.withdraw()
        selected = filedialog.askopenfilename(
            initialdir=os.path.dirname(default_csv),
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        root.destroy()
        if selected:
            csv_path = selected
    else:
        selected = input(f"Enter CSV file path [{default_csv}]: ").strip()
        if selected:
            csv_path = selected

    if not os.path.isfile(csv_path):
        print(f"CSV file not found: {csv_path}")
        return
    ensure_directory(DOWNLOAD_ROOT)
    process_csv(csv_path)


if __name__ == '__main__':
    main()