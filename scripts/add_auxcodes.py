#!/usr/bin/env python3
"""
add_auxcodes.py

Append auxiliary codes from moqima table to pinyin fields in a chars.dict.yaml file.

Usage:
  python scripts/add_auxcodes.py --moqi fuzhuma/moqi/moqima_41448.txt --file dicts/wanxiang/dicts/chars.dict.yaml [--inplace] [--backup] [--dry-run]

Behavior:
  - Reads moqima TSV (char \t aux \t ...), uses the first aux for each character.
  - For lines in chars.dict.yaml of the form: <char>\t<pinyin>\t<weight>, appends `;aux` to the pinyin when a mapping exists and pinyin doesn't already contain a ';'.
  - Preserves comments and other lines unchanged.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import shutil
import difflib
from datetime import datetime


def load_moqi(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\n\r")
            if not ln:
                continue
            if ln.startswith("#"):
                continue
            parts = ln.split("\t")
            if len(parts) < 2:
                continue
            ch = parts[0]
            aux = parts[1]
            if ch and aux and ch not in mapping:
                mapping[ch] = aux
    return mapping


def process_chars(chars_path: Path, moqi_map: dict[str, str]) -> tuple[list[str], int]:
    lines = chars_path.read_text(encoding="utf-8").splitlines(keepends=True)
    out_lines: list[str] = []
    changed = 0
    for line in lines:
        if line.strip() == "":
            out_lines.append(line)
            continue
        if line.startswith("#") or line.strip() == "---":
            out_lines.append(line)
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            ch = parts[0]
            pinyin = parts[1]
            rest = "\t".join(parts[2:])
            aux = moqi_map.get(ch)
            if aux and ";" not in pinyin:
                new_pinyin = f"{pinyin};{aux}"
                new_line = "\t".join([ch, new_pinyin, rest])
                # Preserve original line ending
                if line.endswith("\n") and not new_line.endswith("\n"):
                    new_line += "\n"
                out_lines.append(new_line)
                changed += 1
                continue
        out_lines.append(line)
    return out_lines, changed


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Append moqi auxiliary codes to chars.dict.yaml pinyin fields")
    p.add_argument("--moqi", required=True, help="path to moqima_41448.txt")
    p.add_argument("--file", help="path to a single chars.dict.yaml to update (mutually exclusive with --dir)")
    p.add_argument("--dir", help="directory containing dictionary files to process (non-recursive). If omitted, uses parent dir of --file")
    p.add_argument("--out-dir", help="output directory for modified files (default: ./auxified)")
    p.add_argument("--inplace", action="store_true", help="write changes inplace (overwrites originals). Use with care")
    p.add_argument("--backup", action="store_true", help="make a timestamped backup before writing (only when --inplace is used)")
    p.add_argument("--dry-run", action="store_true", help="print unified diff(s) to stdout and do not modify files")
    args = p.parse_args(argv)

    moqi_path = Path(args.moqi)
    if not moqi_path.exists():
        print(f"moqi file not found: {moqi_path}")
        return 2

    moqi_map = load_moqi(moqi_path)

    # Determine files to process
    files_to_process: list[Path] = []
    if args.file and args.dir:
        print("Specify either --file or --dir, not both.")
        return 2
    if args.file:
        chars_path = Path(args.file)
        if not chars_path.exists():
            print(f"chars file not found: {chars_path}")
            return 2
        files_to_process = [chars_path]
        base_out_dir = Path(args.out_dir) if args.out_dir else Path.cwd() / "auxified" / "moqi"
    else:
        # directory mode
        target_dir = Path(args.dir) if args.dir else None
        if target_dir is None:
            print("Either --file or --dir must be provided")
            return 2
        if not target_dir.exists() or not target_dir.is_dir():
            print(f"directory not found: {target_dir}")
            return 2
        # collect candidate files (non-recursive)
        for p in sorted(target_dir.iterdir()):
            if p.is_file() and (p.name.endswith('.dict.yaml') or p.suffix in ['.yaml', '.txt']):
                files_to_process.append(p)
        base_out_dir = Path(args.out_dir) if args.out_dir else Path.cwd() / "auxified"

    if not files_to_process:
        print("No files found to process.")
        return 0

    # ensure output dir exists when not inplace
    if not args.inplace:
        base_out_dir.mkdir(parents=True, exist_ok=True)

    total_changed = 0
    for fp in files_to_process:
        try:
            orig = fp.read_text(encoding="utf-8").splitlines(keepends=True)
        except Exception as e:
            print(f"Skipping {fp}: could not read ({e})")
            continue
        out_lines, changed = process_chars(fp, moqi_map)
        total_changed += changed

        if changed == 0:
            print(f"{fp}: no changes")
            continue

        if args.dry_run:
            diff = difflib.unified_diff(orig, out_lines, fromfile=str(fp), tofile=str(fp) + " (with-aux)")
            sys.stdout.writelines(diff)
            print(f"\nPlanned changes for {fp}: {changed} lines modified.")
            continue

        if args.inplace:
            if args.backup:
                stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                backup = fp.with_suffix(fp.suffix + f".{stamp}.bak")
                shutil.copy2(fp, backup)
                print(f"Backup written to: {backup}")
            fp.write_text("".join(out_lines), encoding="utf-8")
            print(f"Wrote {changed} modifications into {fp}")
        else:
            out_path = base_out_dir / fp.name
            out_path.write_text("".join(out_lines), encoding="utf-8")
            print(f"Wrote {changed} modifications to {out_path}")

    print(f"Done. Total files processed: {len(files_to_process)}, total lines modified: {total_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
