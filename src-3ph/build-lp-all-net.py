
import pandas as pd
from pathlib import Path

# Directory containing individual meter load profiles
lp_dir = Path("lp")
output_file = lp_dir / "all.csv"

# Collect all CSV files excluding any with '_gaps' or 'all.csv'
csv_files = [f for f in lp_dir.glob("*.csv") if "_gaps" not in f.name and f.name != "all.csv"]

# Initialize master dataframe
combined_df = None

# Process each CSV and merge by "Start Time"
for csv_file in csv_files:
    df = pd.read_csv(csv_file)

    if "Start Time" not in df.columns:
        print(f"Skipping {csv_file.name}: no 'Start Time' column.")
        continue

    # Use consistent datetime parsing
    df["Start Time"] = pd.to_datetime(df["Start Time"], format="%m/%d/%y %H:%M:%S", errors="coerce")

    net_cols = [col for col in df.columns if col.endswith("_net")]
    if not net_cols:
        print(f"Skipping {csv_file.name}: no _net columns found.")
        continue

    df = df[["Start Time"] + net_cols].copy()
    df.columns = ["Start Time"] + [f"{csv_file.stem}_{col}" for col in net_cols]

    if combined_df is None:
        combined_df = df
    else:
        combined_df = pd.merge(combined_df, df, on="Start Time", how="outer")

# Fill missing values with 0 and calculate totals
if combined_df is not None:
    combined_df = combined_df.fillna(0)

    mw_cols = [col for col in combined_df.columns if col.endswith("MW_net")]
    mva_cols = [col for col in combined_df.columns if col.endswith("MVA_net")]

    combined_df["MW_total"] = combined_df[mw_cols].sum(axis=1)
    combined_df["MVA_total"] = combined_df[mva_cols].sum(axis=1)
    combined_df["PF_total"] = combined_df["MW_total"] / combined_df["MVA_total"]
    combined_df.loc[combined_df["MVA_total"] == 0, "PF_total"] = 0.0

    # Create a generic MW_net column for visualization tools
    combined_df["MW_net"] = combined_df["MW_total"]

    combined_df = combined_df.sort_values("Start Time")
    combined_df.to_csv(output_file, index=False)
    print(f"Combined load profile saved to: {output_file}")
else:
    print("No valid input files found.")
