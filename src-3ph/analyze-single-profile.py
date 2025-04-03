
import pandas as pd
import matplotlib.pyplot as plt
import os

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

    # Plot MW_net over time
    plt.figure(figsize=(14, 6))
    plt.plot(df_sorted.index, df_sorted["MW_net"], label="Net MW")
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
    print(f"Detected Gaps: {len(gaps)}")
    if not gaps.empty:
        print(f"First Gap: {gaps.index[0]}")
        print(f"Last Gap: {gaps.index[-1]}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python analyze_profile.py <csv_file>")
        print("Example: python analyze_profile.py ..\lp\south.csv")
    else:
        analyze_load_profile(sys.argv[1])
