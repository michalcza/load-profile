import pandas as pd
import matplotlib.pyplot as plt
import os

from pathlib import Path


def analyze_load_profile(file_path):
    df = pd.read_csv(file_path)

    # Convert 'Start Time' to datetime for time-based indexing
    df["datetime"] = pd.to_datetime(df["Start Time"], errors="coerce")

    # Check for null datetime entries
    null_datetimes = df["datetime"].isnull().sum()

    # Sort and index by datetime
    df_sorted = df.sort_values("datetime").set_index("datetime")

    # Calculate time differences between records
    time_diffs = df_sorted.index.to_series().diff()
    expected_diff = time_diffs.mode()[0]
    gaps = time_diffs[time_diffs > expected_diff]

    # Prepare gap dataframe
    gap_info = pd.DataFrame({
        "gap_end": gaps.index,
        "gap_duration": gaps.values
    })
    gap_info["gap_start"] = gap_info["gap_end"] - gap_info["gap_duration"]
    gap_info = gap_info[["gap_start", "gap_end", "gap_duration"]]

    # Export gaps to CSV
    meter_name = os.path.splitext(os.path.basename(file_path))[0]
    #gap_info.to_csv(f"\\lp\\{meter_name}_gaps.csv", index=False)
    output_path = Path("lp") / f"{meter_name}_gaps.csv"
    gap_info.to_csv(output_path, index=False)

    # Plot MW_net over time
    plt.figure(figsize=(14, 6))
    plt.plot(df_sorted.index, df_sorted["MW_net"], label="Net MW", color='blue')

    # Shade long gaps
    for i, row in gap_info.iterrows():
        plt.axvspan(row["gap_start"], row["gap_end"], color='red', alpha=0.2)
        if i == 0:
            plt.text(row["gap_start"], plt.ylim()[1]*0.9, "First Gap", color='red', rotation=90, verticalalignment='top')
        elif i == len(gap_info) - 1:
            plt.text(row["gap_start"], plt.ylim()[1]*0.9, "Last Gap", color='red', rotation=90, verticalalignment='top')
        elif i < 3:
            plt.text(row["gap_start"], plt.ylim()[1]*0.9, f"Gap #{i+1}", color='red', rotation=90, verticalalignment='top')

    plt.title(f"Feeder Load Profile (MW): {os.path.basename(file_path)}")
    plt.xlabel("Datetime")
    plt.ylabel("MW_net")
    plt.grid(True)
    plt.tight_layout()
    plt.legend()
    plt.show()

    # Print summary report
    print("\n=== Load Profile Integrity Report ===")
    print(f"File: {file_path}")
    print(f"Total Records: {len(df)}")
    print(f"Null datetime entries: {null_datetimes}")
    print(f"Expected interval: {expected_diff}")
    print(f"Detected Gaps: {len(gap_info)}")
    if not gap_info.empty:
        print(f"First Gap: {gap_info.iloc[0]['gap_start']}")
        print(f"Last Gap: {gap_info.iloc[-1]['gap_end']}")
        print(f"Gaps saved to: {meter_name}_gaps.csv")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python analyze-single-profile.py <csv_file>")
        print("Example: python analyze-single-profile north.csv")
    else:
        analyze_load_profile(sys.argv[1])
