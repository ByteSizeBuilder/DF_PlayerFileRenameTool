#!/usr/bin/env python3
"""
DFPlayer Mini File Rename Tool

Renames folders and MP3 files on an SD card to match the naming convention
expected by the DFPlayer Mini module:
  - Folders: 01, 02, ..., 99
  - Files:   001.mp3, 002.mp3, ..., 255.mp3

Files and folders are sorted using natural sort order (the same order shown
in your file manager) so that the original ordering is preserved after
renaming.  For example, "Track 2" comes before "Track 10".
"""

import argparse
import os
import re
import sys

MAX_FOLDERS = 99
MAX_FILES_PER_FOLDER = 255
TEMP_PREFIX = "__dftemp_"


def natural_sort_key(text):
    """Return a sort key that matches file manager ordering (natural sort).

    Splits the text into a list of strings and integers so that numeric
    portions are compared by value rather than lexicographically.
    For example: "Track 2" < "Track 10" (because 2 < 10).
    """
    parts = []
    for part in re.split(r'(\d+)', text.lower()):
        if part.isdigit():
            parts.append(int(part))
        else:
            parts.append(part)
    return parts


def collect_folders(root):
    """Return a sorted list of subdirectory names directly under *root*."""
    entries = []
    for name in os.listdir(root):
        if os.path.isdir(os.path.join(root, name)):
            entries.append(name)
    entries.sort(key=natural_sort_key)
    return entries


def collect_mp3s(folder_path):
    """Return a sorted list of .mp3 filenames inside *folder_path*."""
    files = []
    for name in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, name)) and name.lower().endswith(".mp3"):
            files.append(name)
    files.sort(key=natural_sort_key)
    return files


def rename_two_phase(items, make_final_name, base_dir):
    """Rename *items* inside *base_dir* using a two-phase approach to avoid
    collisions.

    Phase 1: old name -> temporary name
    Phase 2: temporary name -> final name

    *make_final_name(index)* returns the target name for the item at *index*
    (0-based).

    Returns a list of (old_name, new_name) tuples.
    """
    mapping = []
    temp_names = []

    # Phase 1: rename to temporary names
    for i, old_name in enumerate(items):
        final_name = make_final_name(i)
        temp_name = f"{TEMP_PREFIX}{final_name}"
        os.rename(
            os.path.join(base_dir, old_name),
            os.path.join(base_dir, temp_name),
        )
        temp_names.append(temp_name)
        mapping.append((old_name, final_name))

    # Phase 2: rename temporary names to final names
    for temp_name, (_, final_name) in zip(temp_names, mapping):
        os.rename(
            os.path.join(base_dir, temp_name),
            os.path.join(base_dir, final_name),
        )

    return mapping


def process_sd_card(root):
    """Rename all folders and MP3 files under *root* for DFPlayer Mini."""
    root = os.path.abspath(root)

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    folders = collect_folders(root)

    if not folders:
        print("No subdirectories found. Nothing to do.")
        return

    if len(folders) > MAX_FOLDERS:
        print(
            f"Error: Found {len(folders)} folders but DFPlayer Mini supports "
            f"at most {MAX_FOLDERS}.",
            file=sys.stderr,
        )
        sys.exit(1)

    total_files_renamed = 0

    # --- Rename files inside each folder first (while folder names are stable) ---
    for folder_name in folders:
        folder_path = os.path.join(root, folder_name)
        mp3s = collect_mp3s(folder_path)

        if not mp3s:
            print(f"  Warning: '{folder_name}/' contains no .mp3 files – skipping files.")
            continue

        if len(mp3s) > MAX_FILES_PER_FOLDER:
            print(
                f"Error: '{folder_name}/' contains {len(mp3s)} .mp3 files but "
                f"DFPlayer Mini supports at most {MAX_FILES_PER_FOLDER}.",
                file=sys.stderr,
            )
            sys.exit(1)

        file_mapping = rename_two_phase(
            mp3s,
            lambda i: f"{i + 1:03d}.mp3",
            folder_path,
        )

        print(f"  [{folder_name}/]")
        for old, new in file_mapping:
            if old != new:
                print(f"    {old}  ->  {new}")
            else:
                print(f"    {old}  (unchanged)")
        total_files_renamed += len(file_mapping)

    # --- Now rename the folders themselves ---
    folder_mapping = rename_two_phase(
        folders,
        lambda i: f"{i + 1:02d}",
        root,
    )

    print("\nFolder renames:")
    for old, new in folder_mapping:
        if old != new:
            print(f"  {old}/  ->  {new}/")
        else:
            print(f"  {old}/  (unchanged)")

    print(
        f"\nDone. Renamed {len(folder_mapping)} folder(s) and "
        f"{total_files_renamed} file(s)."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Rename folders and MP3 files for DFPlayer Mini.",
    )
    parser.add_argument(
        "path",
        help="Root directory of the SD card (e.g. E:\\ or /media/sdcard).",
    )
    args = parser.parse_args()
    process_sd_card(args.path)


if __name__ == "__main__":
    main()
