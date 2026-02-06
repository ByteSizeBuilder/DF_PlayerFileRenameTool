# DFPlayer Mini File Rename Tool

A Python utility that renames folders and audio files on an SD card to match the
naming convention required by the **DFPlayer Mini** MP3 player module.

## DFPlayer Mini Naming Convention

The DFPlayer Mini expects a specific directory layout on its SD card:

```
SD Card Root/
├── 01/
│   ├── 001.mp3
│   ├── 002.mp3
│   └── 003.mp3
├── 02/
│   ├── 001.mp3
│   └── 002.mp3
├── 03/
│   └── 001.mp3
├── MP3/
│   ├── 0001.mp3
│   ├── 0002.mp3
│   └── 0003.mp3
└── ADVERT/
    ├── 0001.mp3
    └── 0002.mp3
```

### Numbered folders (01–99)

- **Folders** are numbered `01` through `99` (two-digit, zero-padded).
- **Files** within each folder are numbered `001` through `255` (three-digit,
  zero-padded) with their original extension preserved (`.mp3`, `.wav`, `.wma`).

### Special folders (MP3, ADVERT)

- **MP3** – A special folder whose name is kept as-is. Files are numbered with
  four digits (`0001` through `65535`). Use this folder to play tracks by number
  without needing a numbered parent folder.
- **ADVERT** – A special folder for advertisement/interrupt tracks. Files are
  numbered with four digits (`0001` through `0255`). Tracks in this folder can
  be played as interrupts during normal playback.

## Requirements

- Python 3.6 or later
- No external dependencies (uses only the standard library)

## Usage

```
python dfplayer_rename.py <path_to_sd_card>
```

### Example

Suppose your SD card is mounted and contains:

```
/path/to/sdcard/
├── Classical/
│   ├── Bach - Cello Suite.mp3
│   ├── Debussy - Clair de Lune.mp3
│   └── Mozart - Eine Kleine.mp3
├── Jazz/
│   ├── Coltrane - Blue Train.mp3
│   └── Davis - So What.mp3
├── Rock/
│   ├── Led Zeppelin - Stairway.mp3
│   └── Pink Floyd - Comfortably Numb.mp3
├── MP3/
│   ├── Announcement 1.mp3
│   └── Announcement 2.mp3
└── ADVERT/
    └── Welcome.mp3
```

Run:

```
python dfplayer_rename.py /path/to/sdcard
```

The result:

```
/path/to/sdcard/
├── 01/              (was Classical/)
│   ├── 001.mp3      (was Bach - Cello Suite.mp3)
│   ├── 002.mp3      (was Debussy - Clair de Lune.mp3)
│   └── 003.mp3      (was Mozart - Eine Kleine.mp3)
├── 02/              (was Jazz/)
│   ├── 001.mp3      (was Coltrane - Blue Train.mp3)
│   └── 002.mp3      (was Davis - So What.mp3)
├── 03/              (was Rock/)
│   ├── 001.mp3      (was Led Zeppelin - Stairway.mp3)
│   └── 002.mp3      (was Pink Floyd - Comfortably Numb.mp3)
├── MP3/             (kept as-is)
│   ├── 0001.mp3     (was Announcement 1.mp3)
│   └── 0002.mp3     (was Announcement 2.mp3)
└── ADVERT/          (kept as-is)
    └── 0001.mp3     (was Welcome.mp3)
```

Folders are assigned numbers using **natural sort order** — the same order you
see in your file manager (Finder, Explorer, etc.) — and files within each
folder are numbered the same way. This means you can arrange your folders and
files until the order looks right, and the tool will preserve exactly that
order.

## How It Works

1. **Clean** – The tool scans for any files that don't belong on a DFPlayer SD
   card: hidden files/folders (e.g. `.DS_Store`, `.Trashes`), non-audio files
   inside folders, files in the root directory, and subdirectories nested inside
   folders. If any are found, it lists them and asks for confirmation before
   deleting.
2. **Scan** – The tool scans the given root directory for subdirectories,
   identifying special folders (`MP3`, `ADVERT`) separately from regular folders.
3. **Sort** – Regular subdirectories are sorted using **natural sort order**
   (case-insensitive, numbers compared by value). This is the same ordering
   your file manager uses, so `Track 2` comes before `Track 10`.
4. **Rename files (special folders)** – Inside `MP3` and `ADVERT` folders,
   audio files are sorted in natural order and renamed to `0001.mp3`,
   `0002.wav`, etc. (four-digit, original extension preserved). The folder
   names are kept as-is.
5. **Rename files (numbered folders)** – Inside each regular folder, audio
   files are sorted in natural order and renamed to `001.mp3`, `002.wav`, etc.
   (three-digit, original extension preserved).
6. **Rename folders** – Regular folders are then renamed to `01`, `02`, etc.
   Special folders are not renamed.

### Collision Avoidance

Renaming is done in two phases to prevent name collisions (e.g., if a folder
is already named `02` but needs to become `01`):

- **Phase 1:** All items are renamed to temporary names.
- **Phase 2:** Temporary names are renamed to their final names.

## Limitations

- **99 numbered folders max** – The DFPlayer Mini supports folders `01` through
  `99` (the `MP3` and `ADVERT` special folders do not count toward this limit).
- **255 files per numbered folder** – Each numbered folder can contain files
  `001` through `255`.
- **65535 files in MP3 folder** – The `MP3` special folder supports up to 65535
  files (`0001` through `65535`).
- **255 files in ADVERT folder** – The `ADVERT` special folder supports up to
  255 files (`0001` through `0255`).
- **Supported formats** – Only `.mp3`, `.wav`, and `.wma` files are kept and
  renamed. All other files are flagged for deletion (with user confirmation).
- **One level deep** – Only immediate subdirectories of the root are
  processed. Nested subdirectories within those folders are flagged for
  deletion.
