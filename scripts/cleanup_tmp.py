#!/usr/bin/env python3
"""
AI Social Post Generator - Temporary File Cleanup Script

This script removes temporary job directories older than 24 hours.
Run this script periodically to manage disk space.
"""


# Standard library imports
import sys
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import argparse

def cleanup_tmp_directories(base_dir: Path, max_age_hours: int = 24, dry_run: bool = False):
    """Clean up temporary job directories older than specified hours."""
    
    tmp_dir = base_dir / "tmp"
    
    if not tmp_dir.exists():
        print(f"❌ Temporary directory not found: {tmp_dir}")
        return
    
    print(f"🧹 Cleaning up temporary directories in: {tmp_dir}")
    print(f"⏰ Removing directories older than: {max_age_hours} hours")
    print(f"🔍 Dry run mode: {'Yes' if dry_run else 'No'}")
    print("-" * 50)
    
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    cleaned_count = 0
    total_size_cleaned = 0
    
    for job_dir in tmp_dir.iterdir():
        if not job_dir.is_dir():
            continue
        
        try:
            # Check if directory is old enough to clean
            dir_time = datetime.fromtimestamp(job_dir.stat().st_mtime)
            
            if dir_time < cutoff_time:
                # Calculate directory size
                dir_size = get_directory_size(job_dir)
                
                print(f"🗑️  Removing: {job_dir.name}")
                print(f"   Age: {datetime.now() - dir_time}")
                print(f"   Size: {format_size(dir_size)}")
                
                if not dry_run:
                    shutil.rmtree(job_dir)
                    cleaned_count += 1
                    total_size_cleaned += dir_size
                    print(f"   ✅ Removed")
                else:
                    print(f"   🔍 Would remove (dry run)")
                
                print()
            else:
                # Show directories that are kept
                dir_size = get_directory_size(job_dir)
                age = datetime.now() - dir_time
                print(f"📁 Keeping: {job_dir.name} (Age: {age}, Size: {format_size(dir_size)})")
                
        except Exception as e:
            print(f"❌ Error processing directory {job_dir}: {e}")
    
    # Summary
    print("-" * 50)
    if dry_run:
        print(f"🔍 Dry run completed. Would clean up {cleaned_count} directories.")
    else:
        print(f"✅ Cleanup completed successfully!")
        print(f"🗑️  Directories removed: {cleaned_count}")
        print(f"💾 Total space freed: {format_size(total_size_cleaned)}")
    
    # Show remaining directories
    remaining_dirs = list(tmp_dir.iterdir())
    if remaining_dirs:
        print(f"\n📁 Remaining directories: {len(remaining_dirs)}")
        for job_dir in remaining_dirs:
            if job_dir.is_dir():
                dir_size = get_directory_size(job_dir)
                print(f"   • {job_dir.name} ({format_size(dir_size)})")
    else:
        print("\n📁 No temporary directories remaining")

def get_directory_size(directory: Path) -> int:
    """Calculate the total size of a directory in bytes."""
    total_size = 0
    try:
        for path in directory.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
    except Exception:
        pass
    return total_size

def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Clean up temporary job directories for AI Social Post Generator"
    )
    parser.add_argument(
        "--max-age", 
        type=int, 
        default=24,
        help="Maximum age in hours before cleanup (default: 24)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be cleaned without actually removing files"
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Base directory containing the tmp folder (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Get base directory
    base_dir = Path(args.base_dir).resolve()
    
    if not base_dir.exists():
        print(f"❌ Base directory does not exist: {base_dir}")
        sys.exit(1)
    
    print(f"🚀 AI Social Post Generator - Cleanup Script")
    print(f"📁 Base directory: {base_dir}")
    print()
    
    try:
        cleanup_tmp_directories(
            base_dir=base_dir,
            max_age_hours=args.max_age,
            dry_run=args.dry_run
        )
    except KeyboardInterrupt:
        print("\n⚠️  Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
