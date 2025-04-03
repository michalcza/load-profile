
# Load Profile Processing and Analysis Toolkit

This project processes and analyzes interval-based load profile data from utility revenue meters. It provides tooling for file ingestion, validation, transformation, gap detection, and visualization.

---

## 📁 Directory Structure

```text
.
├── _dropbox/KW/                  # Raw incoming CSV files
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

---

## ⚙️ Script Descriptions

### 1. `sort-dropbox.py`
Organizes raw meter data files:
- Reads files from `_dropbox/KW`
- Checks for sequential timestamp integrity
- Moves files to `data/KW/YYYY-MM/` or `data/KW/ERROR/`
- Logs sequence errors and processing details

🔗 Called independently during data import phase.

---

### 2. `build-lp.py`
Processes raw meter data into per-feeder profiles:
- Uses `meter-data.csv` for metadata (ID, multiplier)
- Calculates:
  - `MW_del`, `MW_rec`, `MVA_del`, `MVA_rec`
  - `MW_net`, `MVA_net`, `PF_net`
- Outputs: `lp/north.csv`, `lp/south.csv`, etc.

🔗 Can be run after sorting to build individual load profiles.

---

### 3. `build-lp-all-net.py`
Builds a combined multi-feeder profile:
- Reads `*.csv` files in `lp/` excluding `_gaps`
- Aggregates all `_net` columns
- Computes:
  - `MW_total`, `MVA_total`, `PF_total`
  - Final `MW_net` (copy of `MW_total` for visual compatibility)
- Output: `lp/all.csv`

🔗 Used before visualization to combine all feeder data.

---

### 4. `analyze-single-profile.py`
Visualizes and audits a single load profile:
- Input: any `*.csv` with a `Start Time` and `MW_net` column
- Detects gaps based on timestamp intervals
- Exports a `_gaps.csv` file
- Displays a time series plot with shaded gap regions

🔗 Used interactively for QA or analysis of output files like `lp/south.csv`.

---

### 5. `bi-directional-flow.md`
Documentation on interpreting simultaneous forward and reverse power flow in meters.

---

## 🧪 Example Workflow

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

## 🔍 Key Concepts

- **_net Columns**: Represent summed power values over 15-minute intervals
- **Gap Detection**: Identifies missing time intervals
- **Bi-Directional Flow**: Valid interpretation of meters logging both `kw_del` and `kw_rec`

---

## 📦 Dependencies

- Python 3.8+
- `pandas`, `matplotlib`

---

## ✅ Output Files

| File                  | Description                        |
|-----------------------|------------------------------------|
| `lp/gen.csv`          | Cleaned load profile for GEN meter |
| `lp/all.csv`          | Combined profile of all feeders    |
| `lp/gen_gaps.csv`     | Detected gaps in GEN data          |
| `logs/*.log`          | Error and duplicate logs           |

---

## 📬 Contact

Maintainer: `micha`  
Contributions welcome for reporting, alerts, or web dashboard integration.

