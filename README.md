# DFPlayer Mini File Rename Tool

A Python utility that renames folders and MP3 files on an SD card to match the
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
└── 03/
    └── 001.mp3
```

- **Folders** are numbered `01` through `99` (two-digit, zero-padded).
- **Files** within each folder are numbered `001` through `255` (three-digit,
  zero-padded) with the `.mp3` extension.

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
└── Rock/
    ├── Led Zeppelin - Stairway.mp3
    └── Pink Floyd - Comfortably Numb.mp3
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
└── 03/              (was Rock/)
    ├── 001.mp3      (was Led Zeppelin - Stairway.mp3)
    └── 002.mp3      (was Pink Floyd - Comfortably Numb.mp3)
```

Folders are assigned numbers using **natural sort order** — the same order you
see in your file manager (Finder, Explorer, etc.) — and files within each
folder are numbered the same way. This means you can arrange your folders and
files until the order looks right, and the tool will preserve exactly that
order.

## How It Works

1. **Scan** – The tool scans the given root directory for subdirectories.
2. **Sort** – Subdirectories are sorted using **natural sort order**
   (case-insensitive, numbers compared by value). This is the same ordering
   your file manager uses, so `Track 2` comes before `Track 10`.
3. **Rename files** – Inside each folder, `.mp3` files are sorted in natural
   order and renamed to `001.mp3`, `002.mp3`, etc.
4. **Rename folders** – Folders are then renamed to `01`, `02`, etc.

### Collision Avoidance

Renaming is done in two phases to prevent name collisions (e.g., if a folder
is already named `02` but needs to become `01`):

- **Phase 1:** All items are renamed to temporary names.
- **Phase 2:** Temporary names are renamed to their final names.

## Limitations

- **99 folders max** – The DFPlayer Mini supports folders `01` through `99`.
- **255 files per folder max** – Each folder can contain files `001` through
  `255`.
- **MP3 only** – Only `.mp3` files are renamed. Other files are left
  untouched.
- **One level deep** – Only immediate subdirectories of the root are
  processed. Nested subdirectories within those folders are ignored.
