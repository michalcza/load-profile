import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Directory containing individual meter load profiles
lp_dir = Path("lp")
output_file = lp_dir / "all.csv"

# Collect all CSV files excluding any with '_gaps' or 'all.csv'
csv_files = [f for f in lp_dir.glob("*.csv") if "_gaps" not in f.name and f.name != "all.csv"]

# Initialize master dataframe
combined_df = None

for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    meter_name = csv_file.stem.lower()

    if "Start Time" not in df.columns or not all(col in df.columns for col in ["MW_del", "MW_rec", "MVA_del", "MVA_rec"]):
        print(f"Skipping {csv_file.name}: missing required columns.")
        continue

    df["Start Time"] = pd.to_datetime(df["Start Time"], format="%m/%d/%y %H:%M:%S", errors="coerce")
    df = df[["Start Time", "MW_del", "MW_rec", "MVA_del", "MVA_rec"]].copy()
    df.columns = [
        "Start Time",
        f"mw_del_{meter_name}", f"mw_rec_{meter_name}",
        f"mva_del_{meter_name}", f"mva_rec_{meter_name}"
    ]

    if combined_df is None:
        combined_df = df
    else:
        combined_df = pd.merge(combined_df, df, on="Start Time", how="outer")

# Fill missing values and compute totals
if combined_df is not None:
    combined_df = combined_df.fillna(0)

    mw_del_cols = [col for col in combined_df.columns if col.startswith("mw_del_")]
    mw_rec_cols = [col for col in combined_df.columns if col.startswith("mw_rec_")]
    mva_del_cols = [col for col in combined_df.columns if col.startswith("mva_del_")]
    mva_rec_cols = [col for col in combined_df.columns if col.startswith("mva_rec_")]

    combined_df["MW_total_del"] = combined_df[mw_del_cols].sum(axis=1)
    combined_df["MW_total_rec"] = combined_df[mw_rec_cols].sum(axis=1)
    combined_df["MW_net"] = combined_df["MW_total_del"] + combined_df["MW_total_rec"]

    combined_df["MVA_total_del"] = combined_df[mva_del_cols].sum(axis=1)
    combined_df["MVA_total_rec"] = combined_df[mva_rec_cols].sum(axis=1)
    combined_df["MVA_net"] = combined_df["MVA_total_del"] + combined_df["MVA_total_rec"]

    combined_df["PF_net"] = combined_df["MW_net"] / combined_df["MVA_net"]
    combined_df.loc[combined_df["MVA_net"] == 0, "PF_net"] = 0.0

    combined_df = combined_df.sort_values("Start Time")
    combined_df.to_csv(output_file, index=False)
    print(f"Combined load profile saved to: {output_file}")

    # Plot MW_net total
    plt.figure(figsize=(14, 6))
    plt.plot(combined_df["Start Time"], combined_df["MW_net"], label="MW_net (total)", color="blue")
    plt.axhline(0, color="gray", linestyle="--")
    plt.title("MW Net Overview (Total)")
    plt.xlabel("Time")
    plt.ylabel("MW")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Plot each profile separately
    for col in mw_del_cols:
        meter = col.replace("mw_del_", "")
        rec_col = f"mw_rec_{meter}"

        if rec_col in combined_df.columns:
            plt.figure(figsize=(14, 5))
            plt.plot(combined_df["Start Time"], combined_df[col], label=f"{meter.upper()} Delivered", linestyle="--", color="green")
            plt.plot(combined_df["Start Time"], -combined_df[rec_col], label=f"{meter.upper()} Received (negated)", linestyle=":", color="red")
            plt.axhline(0, color="gray", linestyle="--")
            plt.title(f"{meter.upper()} MW Flow")
            plt.xlabel("Time")
            plt.ylabel("MW")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.show()

else:
    print("No valid input files found.")
