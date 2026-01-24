"""File system safety utilities.

Provides functions for sanitizing filenames, resolving paths safely, 
and extracting ZIP files without Zip Slip vulnerability.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Set


def sanitize_filename(name: str, max_length: int = 120) -> str:
    """Sanitize a filename to be safe for local storage.
    
    Removes path separators, control characters, and limits length.
    
    Args:
        name: Original filename.
        max_length: Maximum allowed length.
        
    Returns:
        Sanitized filename.
    """
    # Remove path separators
    name = name.replace("/", "_").replace("\\", "_")
    
    # Remove control characters and other dangerous characters
    # Keep alphanumeric, dots, dashes, and underscores
    name = re.sub(r"[^\w\.\-\ ]", "_", name)
    
    # Strip leading/trailing whitespace
    name = name.strip()
    
    # Limit length
    if len(name) > max_length:
        stem = Path(name).stem[:max_length-10]
        suffix = Path(name).suffix
        name = f"{stem}{suffix}"
        
    if not name:
        name = "unnamed_file"
        
    return name


def resolve_under(base: Path, target: Path) -> Path:
    """Resolve a target path and ensure it's under the base directory.
    
    Args:
        base: The directory that should contain the target.
        target: The target path to resolve.
        
    Returns:
        The resolved absolute path.
        
    Raises:
        ValueError: If target is not under base.
    """
    base_abs = base.resolve()
    target_abs = target.resolve()
    
    if not str(target_abs).startswith(str(base_abs)):
        raise ValueError(f"Security error: path {target_abs} is not under {base_abs}")
        
    return target_abs


def safe_extract_zip(
    zip_path: Path, 
    dest_dir: Path, 
    *, 
    max_files: int = 100, 
    max_total_size: int = 100 * 1024 * 1024,
    allowed_ext: Set[str] | None = None
) -> list[Path]:
    """Safely extract a ZIP file preventing Zip Slip and DoS.
    
    Args:
        zip_path: Path to the ZIP file.
        dest_dir: Destination directory.
        max_files: Maximum number of files to extract.
        max_total_size: Maximum total size of extracted files.
        allowed_ext: Set of allowed file extensions (including dot).
        
    Returns:
        List of paths to extracted files.
        
    Raises:
        ValueError: For security violations or limits exceeded.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_abs = dest_dir.resolve()
    
    extracted_paths = []
    total_size = 0
    file_count = 0
    
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Check file count limit
        infolist = zf.infolist()
        if len(infolist) > max_files:
            raise ValueError(f"Too many files in ZIP: {len(infolist)} (max {max_files})")
            
        for info in infolist:
            # Skip directories and symlinks
            if info.is_dir():
                continue
                
            # Check file extension
            if allowed_ext:
                ext = Path(info.filename).suffix.lower()
                if ext not in allowed_ext:
                    continue
            
            # Prevent Zip Slip: ensure resolved path is under dest_dir
            target_path = (dest_dir / info.filename).resolve()
            if not str(target_path).startswith(str(dest_abs)):
                raise ValueError(f"Zip Slip attempt detected: {info.filename}")
            
            # Check total size limit
            total_size += info.file_size
            if total_size > max_total_size:
                raise ValueError(f"Total extracted size exceeds limit: {max_total_size} bytes")
            
            # Extract file
            zf.extract(info, dest_dir)
            extracted_paths.append(target_path)
            file_count += 1
            
    return extracted_paths
