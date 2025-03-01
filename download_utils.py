import logging
import os
from pathlib import Path
import requests
from typing import Union

logger = logging.getLogger(__name__)

def setup_download_directory(dir_name: str) -> Path:
    """Create and return download directory path."""
    download_dir = Path(dir_name)
    download_dir.mkdir(exist_ok=True)
    return download_dir

def download_file(url: str, filepath: Union[str, Path], chunk_size: int = 8192) -> None:
    """
    Download a file from URL to specified path with progress tracking.

    Args:
        url: Source URL
        filepath: Destination file path
        chunk_size: Size of chunks for streaming download
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        filepath = Path(filepath) if isinstance(filepath, str) else filepath

        with open(filepath, 'wb') as file:
            if total_size == 0:
                file.write(response.content)
            else:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}%", end="", flush=True)
                print()  # New line after progress

        logger.info(f"Successfully downloaded: {filepath}")

    except requests.RequestException as e:
        logger.error(f"Download failed: {e}")
        filepath = Path(filepath) if isinstance(filepath, str) else filepath
        if filepath.exists():
            filepath.unlink()  # Remove partial download
        raise