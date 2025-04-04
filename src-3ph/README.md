
# Load Profile Processing and Analysis Toolkit

This project processes and analyzes interval-based load profile data from utility revenue meters. It provides tooling for file ingestion, validation, transformation, gap detection, and visualization.

---

## Directory Structure

```text
.
├── _dropbox/KW/                 # Raw incoming CSV files
├── data/KW/YYYY-MM/             # Archived sorted CSVs by month
├── lp/                          # Load profile outputs (per feeder and combined)
├── logs/                        # Process and error logs
├── meter-data.csv               # Meter metadata (name, multiplier, etc.)
├── .processed-hashes.json       # Tracks previously processed file hashes
├── build-lp.py                  # Per-meter load profile builder
├── build-lp-all-net.py          # Combined load profile builder
├── analyze-single-profile.py    # Visualizes gaps and MW_net trends
├── sort-dropbox.py              # Sorts and validates raw files from _dropbox
```

## Function Overview

Below is a concise list of all functions with a short synopsis:


| **File**                 | **Function**                     | **Synopsis**                                           |
|--------------------------|----------------------------------|--------------------------------------------------------|
| `sort-dropbox.py`        | `log`                            | Logs messages to dropbox.log and dropbox-error.log.    |
| `build-lp.py`            | `calculate_power_factors`        | Computes net MW, MVA, and PF from directional values.  |
| `build-lp.py`            | `clean_and_transform_file`       | Cleans, validates, and transforms raw meter data.      |
| `build-lp.py`            | `load_meter_metadata`            | Loads meter metadata from meter-data.csv.              |
| `build-lp.py`            | `build_profiles`                 | Creates individual load profile files per meter.       |
| `build-lp-all-net.py`    | *(no functions; script-level)*   | Merges all load profiles and computes totals.          |
| `analyze-single-profile.py` | `analyze_load_profile`        | Plots MW_net over time and detects timestamp gaps.     |


---

## Script Descriptions

### 1. `sort-dropbox.py`
Organizes raw meter data files:
- Reads files from `_dropbox/KW`
- Checks for sequential timestamp integrity
- Moves files to `data/KW/YYYY-MM/` or `data/KW/ERROR/`
- Logs sequence errors and processing details

Called independently during data import phase.

---

### 2. `build-lp.py`
Processes raw meter data into per-feeder profiles:
- Uses `meter-data.csv` for metadata (ID, multiplier)
- Calculates:
  - `MW_del`, `MW_rec`, `MVA_del`, `MVA_rec`
  - `MW_net`, `MVA_net`, `PF_net`
- Outputs: `lp/north.csv`, `lp/south.csv`, etc.

Can be run after sorting to build individual load profiles.

---

### 3. `build-lp-all-net.py`
Builds a combined multi-feeder profile:
- Reads `*.csv` files in `lp/` excluding `_gaps`
- Aggregates all `_net` columns
- Computes:
  - `MW_total`, `MVA_total`, `PF_total`
  - Final `MW_net` (copy of `MW_total` for visual compatibility)
- Output: `lp/all.csv`

Used before visualization to combine all feeder data.

---

### 4. `analyze-single-profile.py`
Visualizes and audits a single load profile:
- Input: any `*.csv` with a `Start Time` and `MW_net` column
- Detects gaps based on timestamp intervals
- Exports a `_gaps.csv` file
- Displays a time series plot with shaded gap regions

Used interactively for QA or analysis of output files like `lp/south.csv`.

---

### 5. `bi-directional-flow.md`
Documentation on interpreting simultaneous forward and reverse power flow in meters.

---

## Example Workflow

```bash
# Step 1: Sort incoming files
python sort-dropbox.py

# Step 2: Build individual load profiles
python build-lp.py

# Step 3: Merge into combined profile
python build-lp-all-net.py

# Step 4: Analyze a single meter or combined data
python analyze-single-profile.py lp/all.csv
```

---

## Dependencies

- Python 3.8+
- `pandas`, `matplotlib`

---

## Output Files

| File                  | Description                        |
|-----------------------|------------------------------------|
| `lp/gen.csv`          | Cleaned load profile for GEN meter |
| `lp/all.csv`          | Combined profile of all feeders    |
| `lp/gen_gaps.csv`     | Detected gaps in GEN data          |
| `logs/*.log`          | Error and duplicate logs           |

---

# Logging and Gap Detection

## 1. `sort-dropbox.py`

This script detects **sequence errors** in raw CSV files based on timestamp gaps. When a file is found to have timestamp mismatches (i.e., one row’s end time doesn’t match the next row’s start time), it is:

- Renamed with `_SEQUENCE-ERROR.csv`
- Moved to `data/KW/ERROR/`
- Logged in:
  - `logs/dropbox-error.log` — includes mismatch context
  - `logs/dropbox.log` — includes file start/end timestamps

### Example:
```
north-011400-000000_032525-074500_SEQUENCE-ERROR.csv
```

---

## 2. `analyze-single-profile.py`

This script detects **interval gaps** in processed load profile files (`lp/*.csv`) by comparing time deltas between successive rows.

- Gaps are highlighted on the visualization (red shaded regions)
- A CSV of gaps is generated, named:
  ```
  lp/south_gaps.csv
  ```

Each row includes:
- `gap_start`
- `gap_end`
- `gap_duration`

---

## 3. Log Files

| File                            | Description                                 |
|---------------------------------|---------------------------------------------|
| `logs/dropbox.log`              | Status of files processed from `_dropbox`   |
| `logs/dropbox-error.log`        | Sequence violations and details             |
| `lp/*_gaps.csv`                 | Missing interval detections (per profile)   |
| `data/KW/ERROR/*.csv`           | Files with timestamp sequence issues        |




# Understanding Bi-Directional Power Flow in Revenue Meter Data

When a revenue meter records **nonzero values for both `kw_del` and `kw_rec`** during the same 15-minute interval, it indicates **power flow reversal** occurred within that time block.

---

## Example

```text
Start Time: 07/12/24 11:00:00  kw_del = 0.84  kw_rec = 55.79
```

| meter     | Record No. | Event Type | Start Time         | End Time           | kw_del | kw_rec | kva_del | kva_rec | MW_del   | MW_rec   | MVA_del  | MVA_rec  | MW_net  | MVA_net | PF_net  |
|-----------|------------|------------|--------------------|--------------------|--------|--------|---------|---------|----------|----------|----------|----------|---------|---------|---------|
| 144800052 | 157594     | Normal     | 07/12/24 11:00:00  | 07/12/24 11:15:00  | 0.84   | 55.79  | 15.02   | 228.51  | 0.024192 | 1.606752 | 0.432576 | 6.581088 | 1.630944| 7.013664| 0.232538 |
| 144800052 | 157595     | Normal     | 07/12/24 11:15:00  | 07/12/24 11:30:00  | 2.45   | 15.01  | 46.47   | 126.19  | 0.07056  | 0.432288 | 1.338336 | 3.634272 | 0.502848| 4.972608| 0.101124 |
| 144800052 | 157596     | Normal     | 07/12/24 11:30:00  | 07/12/24 11:45:00  | 11.55  | 4.97   | 98.57   | 35.42   | 0.33264  | 0.143136 | 2.838816 | 1.020096 | 0.475776| 3.858912| 0.123293 |
| 144800052 | 157597     | Normal     | 07/12/24 11:45:00  | 07/12/24 12:00:00  | 33.89  | 0.53   | 199.48  | 1.19    | 0.976032 | 0.015264 | 5.745024 | 0.034272 | 0.991296| 5.779296| 0.171525 |
| 144800052 | 157598     | Normal     | 07/12/24 12:00:00  | 07/12/24 12:15:00  | 41.46  | 0.04   | 230.86  | 0.01    | 1.194048 | 0.001152 | 6.648768 | 0.000288 | 1.1952  | 6.649056| 0.179755 |
| 144800052 | 157599     | Normal     | 07/12/24 12:15:00  | 07/12/24 12:30:00  | 39.12  | 0.05   | 229.31  | 0.22    | 1.126656 | 0.00144  | 6.604128 | 0.006336 | 1.128096| 6.610464| 0.170653 |
| 144800052 | 157600     | Normal     | 07/12/24 12:30:00  | 07/12/24 12:45:00  | 34.01  | 0.07   | 214.15  | 0.07    | 0.979488 | 0.002016 | 6.16752  | 0.002016 | 0.981504| 6.169536| 0.159089 |
| 144800052 | 157601     | Normal     | 07/12/24 12:45:00  | 07/12/24 13:00:00  | 41.42  | 0.02   | 228.21  | 0.08    | 1.192896 | 0.000576 | 6.572448 | 0.002304 | 1.193472| 6.574752| 0.181524 |


This means:
- **0.84 kWh** were delivered **to the site** (meter → load)
- **55.79 kWh** were received **from the site** (load → grid, e.g., solar export)

---

## Why This Happens

This condition is **normal** in systems with:
- **Solar PV**, where production can temporarily exceed local demand
- **Battery energy storage systems (BESS)** that charge and discharge dynamically

The meter accumulates **total forward and reverse energy** over the interval — it does not sample direction second-by-second.

Even a brief moment of power reversal during the 15-minute block results in **both `kw_del` and `kw_rec` > 0**.

---

## Power Factor Impact

For example:

```text
MW_net  = 1.630944  
MVA_net = 7.013664  
PF_net  = 0.232538
```

- A **low `PF_net`** occurs when the real power (`MW_net`) is small compared to apparent power (`MVA_net`).
- This often happens when there's **both forward and reverse flow** in the same block.

---

## Interpreting the Pattern

| Interval Start | kw_del | kw_rec | Notes                        |
|----------------|--------|--------|------------------------------|
| 11:00          | 0.84   | 55.79  | Heavy export                 |
| 11:15          | 2.45   | 15.01  | Export decreasing            |
| 11:30          | 11.55  | 4.97   | Shifting toward consumption  |
| 11:45 onward   | 33.89+ | ~0     | Forward flow resumes         |

This pattern could suggest:
- Solar generation **dropping off**
- A load (e.g. HVAC) **turning on**
- **Clouds** moving over PV panels

Meters that record both `kw_del` and `kw_rec` in a time block are:
- Accurately capturing **bidirectional flow**
- Showing that **reversal occurred during that interval**

---
