#!/usr/bin/env python3
"""
DFPlayer Mini File Rename Tool

Renames folders and audio files on an SD card to match the naming convention
expected by the DFPlayer Mini module:
  - Folders: 01, 02, ..., 99
  - Files:   001 - Original Name.mp3, 002 - Another.wav, ..., 255 - Last.wma

Special folders (kept as-is, files use 4-digit naming):
  - MP3:    0001 - Original Name.mp3 ... up to 3000 files
  - ADVERT: 0001 - Original Name.mp3 ... up to 3000 files

Files and folders are sorted using natural sort order (the same order shown
in your file manager) so that the original ordering is preserved after
renaming.  For example, "Track 2" comes before "Track 10".
"""

import argparse
import os
import re
import shutil
import sys
import time

MAX_FOLDERS = 99
MAX_FILES_PER_FOLDER = 255
TEMP_PREFIX = "__dftemp_"
RENAME_RETRIES = 5
RENAME_RETRY_DELAY = 1  # seconds
SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".wma"}

# Special folders that DFPlayer recognises by name (case-insensitive).
# They are not numbered and use 4-digit file naming.
SPECIAL_FOLDERS = {
    "mp3":    {"max_files": 3000, "digits": 4},
    "advert": {"max_files": 3000, "digits": 4},
}

# OS-created directories that should never be renamed or deleted.
SYSTEM_DIRS = {
    "system volume information",  # Windows
    "$recycle.bin",               # Windows
    "recycler",                   # Windows (legacy)
    "lost+found",                 # Linux (ext filesystem)
}


def _strip_numeric_prefix(stem):
    """Remove an existing DFPlayer numeric prefix (e.g. '001 - ') from a stem.

    This prevents double-prefixing when the tool is run more than once.
    """
    return re.sub(r'^\d{3,4}\s*-\s*', '', stem)


def _is_system_dir(name):
    """Return True if *name* is a known OS system directory."""
    return name.lower() in SYSTEM_DIRS


def _is_special_folder(name):
    """Return True if *name* is a DFPlayer special folder (MP3, ADVERT)."""
    return name.lower() in SPECIAL_FOLDERS


def _rename_with_retry(src, dst):
    """Rename *src* to *dst*, retrying on PermissionError.

    Windows background processes (Search Indexer, antivirus, shell extensions)
    can briefly lock files and folders.  A short retry loop handles these
    transient locks.
    """
    for attempt in range(RENAME_RETRIES):
        try:
            os.rename(src, dst)
            return
        except PermissionError:
            if attempt < RENAME_RETRIES - 1:
                time.sleep(RENAME_RETRY_DELAY)
            else:
                raise


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
    """Return a sorted list of subdirectory names directly under *root*.

    Hidden directories, OS system directories, and special folders (MP3,
    ADVERT) are excluded — special folders are collected separately.
    """
    entries = []
    for name in os.listdir(root):
        if name.startswith(".") or _is_system_dir(name) or _is_special_folder(name):
            continue
        if os.path.isdir(os.path.join(root, name)):
            entries.append(name)
    entries.sort(key=natural_sort_key)
    return entries


def collect_special_folders(root):
    """Return a list of special folder names (MP3, ADVERT) found under *root*."""
    found = []
    for name in os.listdir(root):
        if os.path.isdir(os.path.join(root, name)) and _is_special_folder(name):
            found.append(name)
    return found


def collect_audio_files(folder_path):
    """Return a sorted list of supported audio filenames inside *folder_path*."""
    files = []
    for name in os.listdir(folder_path):
        ext = os.path.splitext(name)[1].lower()
        if os.path.isfile(os.path.join(folder_path, name)) and ext in SUPPORTED_EXTENSIONS:
            files.append(name)
    files.sort(key=natural_sort_key)
    return files


def collect_non_audio_items(root):
    """Return a list of paths that don't belong on a DFPlayer SD card.

    The only items that should exist are non-hidden folders at the root level
    and supported audio files inside those folders.  Everything else is flagged:
      - Any file in the root directory
      - Hidden files or folders (name starts with '.')
      - Non-audio files inside folders
      - Subdirectories inside folders (DFPlayer uses one level only)
    """
    items_to_delete = []

    for name in os.listdir(root):
        full_path = os.path.join(root, name)

        # OS system directories — never touch
        if _is_system_dir(name):
            continue

        # Hidden item at root level — flag entire tree
        if name.startswith("."):
            items_to_delete.append(full_path)
            continue

        # File at root level — doesn't belong
        if os.path.isfile(full_path):
            items_to_delete.append(full_path)
            continue

        # Non-hidden directory — scan contents for non-audio items
        if os.path.isdir(full_path):
            for fname in os.listdir(full_path):
                fpath = os.path.join(full_path, fname)
                ext = os.path.splitext(fname)[1].lower()
                if fname.startswith("."):
                    items_to_delete.append(fpath)
                elif os.path.isdir(fpath):
                    items_to_delete.append(fpath)
                elif ext not in SUPPORTED_EXTENSIONS:
                    items_to_delete.append(fpath)

    return sorted(items_to_delete)


def clean_sd_card(root):
    """Find non-audio items on the SD card, prompt the user, and delete if
    confirmed.  Returns True if cleaning proceeded (or nothing to clean),
    False if the user declined.
    """
    items = collect_non_audio_items(root)

    if not items:
        print("No unsupported files found. SD card is clean.\n")
        return True

    print(f"Found {len(items)} item(s) that are not folders or audio files:\n")
    for path in items:
        rel = os.path.relpath(path, root)
        if os.path.isdir(path):
            print(f"  [DIR]  {rel}")
        else:
            print(f"  [FILE] {rel}")

    print()
    answer = input("Delete these items? (yes/no): ").strip().lower()

    if answer in ("y", "yes"):
        failed = []
        for path in items:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except PermissionError:
                failed.append(os.path.relpath(path, root))

        deleted = len(items) - len(failed)
        if failed:
            print(f"\nDeleted {deleted} item(s), but {len(failed)} could not "
                  f"be removed (in use by another process):")
            for rel in failed:
                print(f"  {rel}")
            print("\nTip: Close File Explorer and any other programs that may "
                  "be accessing the SD card, then try again.\n")
        else:
            print(f"Deleted {deleted} item(s).\n")
        return True

    print("Skipped deletion. No files were removed.\n")
    return False


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

    try:
        # Phase 1: rename to temporary names
        for i, old_name in enumerate(items):
            final_name = make_final_name(i)
            temp_name = f"{TEMP_PREFIX}{final_name}"
            _rename_with_retry(
                os.path.join(base_dir, old_name),
                os.path.join(base_dir, temp_name),
            )
            temp_names.append(temp_name)
            mapping.append((old_name, final_name))

        # Phase 2: rename temporary names to final names
        for temp_name, (_, final_name) in zip(temp_names, mapping):
            _rename_with_retry(
                os.path.join(base_dir, temp_name),
                os.path.join(base_dir, final_name),
            )
    except PermissionError as exc:
        print(
            f"\nError: Could not rename '{exc.filename}' because it is in use "
            f"by another process.\n"
            f"Close File Explorer and any other programs that may be accessing "
            f"the SD card, then try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    return mapping


def process_sd_card(root):
    """Rename all folders and audio files under *root* for DFPlayer Mini."""
    root = os.path.abspath(root)

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    # --- Clean non-audio items before renaming ---
    clean_sd_card(root)

    special_folders = collect_special_folders(root)
    folders = collect_folders(root)

    if not folders and not special_folders:
        print("No subdirectories found. Nothing to do.")
        return

    if len(folders) > MAX_FOLDERS:
        print(
            f"Error: Found {len(folders)} numbered folders but DFPlayer Mini "
            f"supports at most {MAX_FOLDERS}.",
            file=sys.stderr,
        )
        sys.exit(1)

    total_files_renamed = 0

    # --- Process special folders (MP3, ADVERT) ---
    for folder_name in special_folders:
        folder_path = os.path.join(root, folder_name)
        config = SPECIAL_FOLDERS[folder_name.lower()]
        max_files = config["max_files"]
        digits = config["digits"]
        audio_files = collect_audio_files(folder_path)

        if not audio_files:
            print(f"  Warning: '{folder_name}/' contains no audio files – skipping.")
            continue

        if len(audio_files) > max_files:
            print(
                f"Error: '{folder_name}/' contains {len(audio_files)} audio files but "
                f"DFPlayer Mini supports at most {max_files} in this folder.",
                file=sys.stderr,
            )
            sys.exit(1)

        file_mapping = rename_two_phase(
            audio_files,
            lambda i, _f=audio_files, _d=digits: (
                f"{i + 1:0{_d}d} - "
                f"{_strip_numeric_prefix(os.path.splitext(_f[i])[0])}"
                f"{os.path.splitext(_f[i])[1].lower()}"
            ),
            folder_path,
        )

        print(f"  [{folder_name}/]  (special folder – name kept as-is)")
        for old, new in file_mapping:
            if old != new:
                print(f"    {old}  ->  {new}")
            else:
                print(f"    {old}  (unchanged)")
        total_files_renamed += len(audio_files)

    # --- Rename files inside each numbered folder (while folder names are stable) ---
    for folder_name in folders:
        folder_path = os.path.join(root, folder_name)
        audio_files = collect_audio_files(folder_path)

        if not audio_files:
            print(f"  Warning: '{folder_name}/' contains no audio files – skipping.")
            continue

        if len(audio_files) > MAX_FILES_PER_FOLDER:
            print(
                f"Error: '{folder_name}/' contains {len(audio_files)} audio files but "
                f"DFPlayer Mini supports at most {MAX_FILES_PER_FOLDER}.",
                file=sys.stderr,
            )
            sys.exit(1)

        file_mapping = rename_two_phase(
            audio_files,
            lambda i, _files=audio_files: (
                f"{i + 1:03d} - "
                f"{_strip_numeric_prefix(os.path.splitext(_files[i])[0])}"
                f"{os.path.splitext(_files[i])[1].lower()}"
            ),
            folder_path,
        )

        print(f"  [{folder_name}/]")
        for old, new in file_mapping:
            if old != new:
                print(f"    {old}  ->  {new}")
            else:
                print(f"    {old}  (unchanged)")
        total_files_renamed += len(audio_files)

    # --- Now rename the numbered folders themselves ---
    if folders:
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
    else:
        folder_mapping = []

    print(
        f"\nDone. Renamed {len(folder_mapping)} folder(s) and "
        f"{total_files_renamed} file(s)."
        + (f" Special folders kept: {', '.join(special_folders)}."
           if special_folders else "")
    )


def main():
    parser = argparse.ArgumentParser(
        description="Rename folders and audio files for DFPlayer Mini.",
    )
    parser.add_argument(
        "path",
        help="Root directory of the SD card (e.g. E:\\ or /media/sdcard).",
    )
    args = parser.parse_args()
    process_sd_card(args.path)


if __name__ == "__main__":
    main()
