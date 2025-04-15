import pandas as pd
import os
from glob import glob

# --- Utility functions ---
def find_matching_files(folder, keyword):
    return sorted(glob(os.path.join(folder, f"*{keyword}*.csv")))

def parse_kw_csv(path):
    df = pd.read_csv(path, skiprows=4)
    df.columns = [col.strip() for col in df.columns]
    df['Start Time'] = pd.to_datetime(df['Start Time'], errors='coerce')
    df['End Time'] = pd.to_datetime(df['End Time'], errors='coerce')
    col_map = {'-1-': 'Del kW', '-2-': 'Rec kW', '-3-': 'Del kVA', '-4-': 'Rec kVA'}
    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)
    return df[['Start Time', 'End Time'] + [col for col in df.columns if col not in ['Start Time', 'End Time']]]

def parse_kwh_csv_flexible(path):
    delivered = None
    received = None
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            fields = [x.strip() for x in line.split(",")]
            if len(fields) < 8:
                continue
            direction = fields[6].lower()
            try:
                value = float(fields[7])
            except ValueError:
                continue
            if 'del' in direction and delivered is None:
                delivered = value
            elif 'rec' in direction and received is None:
                received = value
    return {"Delivered kWh": delivered, "Received kWh": received}

def generate_billing_row(substation, meter_number, multiplier, kw_dir, kwh_dir):
    keyword = meter_number[-8:]
    kw_files = find_matching_files(kw_dir, keyword)
    kwh_files = find_matching_files(kwh_dir, keyword)

    if not kw_files or not kwh_files:
        return {
            "Substation": substation,
            "Meter": meter_number,
            "Multiplier": multiplier,
            "Delivered kWh": None,
            "Received kWh": None,
            "Peak Delivered kW": None,
            "Time of Peak Del kW": None,
            "Peak Received kW": None,
            "Time of Peak Rec kW": None,
            "Note": "Files missing"
        }

    kw_df = parse_kw_csv(kw_files[0])
    kwh_values = parse_kwh_csv_flexible(kwh_files[0])

    del_kw_peak = kw_df["Del kW"].max()
    rec_kw_peak = kw_df["Rec kW"].max()
    del_kw_peak_time = kw_df.loc[kw_df["Del kW"].idxmax(), "Start Time"]
    rec_kw_peak_time = kw_df.loc[kw_df["Rec kW"].idxmax(), "Start Time"]

    del_kwh_total = kwh_values.get("Delivered kWh", 0.0)
    rec_kwh_total = kwh_values.get("Received kWh", 0.0)

    return {
        "Substation": substation,
        "Meter": meter_number,
        "Multiplier": multiplier,
        "Delivered kWh": del_kwh_total * multiplier,
        "Received kWh": rec_kwh_total * multiplier,
        "Peak Delivered kW": del_kw_peak * multiplier,
        "Time of Peak Del kW": del_kw_peak_time,
        "Peak Received kW": rec_kw_peak * multiplier,
        "Time of Peak Rec kW": rec_kw_peak_time,
        "Note": ""
    }

# --- Main Process ---
def process_billing(metadata_csv, kw_dir, kwh_dir, output_file):
    metadata = pd.read_csv(metadata_csv)
    results = [
        generate_billing_row(row['Substation'], str(row['Meter Number']), row['Multiplier'], kw_dir, kwh_dir)
        for _, row in metadata.iterrows()
    ]
    df = pd.DataFrame(results)
    df.to_excel(output_file, index=False)
    print(f"Billing summary written to {output_file}")

# Example usage
if __name__ == "__main__":
    process_billing(
        metadata_csv="metadata.csv",  # CSV with columns: Substation,Meter Number,Multiplier
        kw_dir="./kW Readings",
        kwh_dir="./kWH Files 2024",
        output_file="April2024_Billing_Summary.xlsx"
    )
