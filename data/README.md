# Data Directory

## Setup Instructions

Copy your `cdl_db` directory here:

```bash
cp -r /path/to/your/cdl_db data/
```

## Required Structure

After copying, you should have:

```
data/
└── cdl_db/
    ├── Speaker.csv
    ├── Talk.csv
    ├── Tag.csv
    ├── Event.csv
    ├── Category.csv
    ├── GIVES_TALK_Speaker_Talk.csv
    ├── IS_PART_OF_Talk_Event.csv
    ├── IS_CATEGORIZED_AS_Talk_Category.csv
    └── IS_DESCRIBED_BY_Talk_Tag.csv
```

## Verification

Run this to verify all files are present:

```bash
ls data/cdl_db/*.csv
```

You should see 9 CSV files listed.
