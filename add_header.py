#!/usr/bin/env python3
"""Prepend a tab-separated header to all files in a folder.

Each file is expected to be a text file with 3 columns. The script will
skip files that already start with the header line.

Usage examples:
  python add_header.py /path/to/folder --pattern "*.txt"
  python add_header.py . -p "*" --no-backup
  python add_header.py data -p "*.dat" --dry-run
"""
import argparse
import glob
import os
import shutil
import tempfile

DEFAULT_HEADER = "Frequency\tReal\tImag"

def file_has_header(path, header=DEFAULT_HEADER):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            first = f.readline().strip()
            return first == header or first.split()[:3] == header.split()
    except Exception:
        return False

def prepend_header(path, header=DEFAULT_HEADER, backup=True):
    if file_has_header(path, header=header):
        return False
    dirn = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=dirn)
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8") as out_f, open(path, "r", encoding="utf-8", errors="ignore") as in_f:
            out_f.write(header + "\n")
            shutil.copyfileobj(in_f, out_f)
        if backup:
            shutil.copy2(path, path + ".bak")
        os.replace(tmp, path)
        return True
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass

def main():
    p = argparse.ArgumentParser(description="Prepend header to all files in a folder")
    p.add_argument("folder", nargs="?", default=".", help="Target folder (default: current directory)")
    p.add_argument("--pattern", "-p", default="*", help="Filename glob pattern (default: '*')")
    p.add_argument("--no-backup", action="store_true", help="Don't keep a .bak backup of modified files")
    p.add_argument("--dry-run", action="store_true", help="Show which files would be changed, don't modify anything")
    p.add_argument("--header", default=DEFAULT_HEADER, help="Header line to insert (tab-separated).")
    args = p.parse_args()

    search = os.path.join(args.folder, args.pattern)
    files = [f for f in glob.glob(search) if os.path.isfile(f)]
    if not files:
        print("No files found for:", search)
        return

    for fp in sorted(files):
        try:
            if file_has_header(fp, header=args.header):
                print("Skipped (already has header):", fp)
            else:
                if args.dry_run:
                    print("Would add header to:", fp)
                else:
                    ok = prepend_header(fp, header=args.header, backup=not args.no_backup)
                    if ok:
                        print("Added header to:", fp)
                    else:
                        print("Skipped (already has header):", fp)
        except Exception as e:
            print("Error processing", fp, "->", str(e))

if __name__ == "__main__":
    main()
