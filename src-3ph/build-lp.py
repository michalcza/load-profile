import csv
import json
import hashlib
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# --- Config ---
project_root = Path('.')
data_root = project_root / 'data' / 'KW'
lp_output_dir = project_root / 'lp'
meter_list_file = project_root / 'meter-data.csv'
logs_dir = project_root / 'logs'
duplicates_log = logs_dir / 'process-data-duplicates.log'
errors_log = logs_dir / 'process-data-error.log'
hash_cache_path = project_root / '.processed-hashes.json'
date_format = "%m/%d/%y %H:%M:%S"

# --- Utilities ---
def hash_file(filepath):
    h = hashlib.sha256()
    with filepath.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def load_hash_cache(cache_path):
    if cache_path.exists():
        with cache_path.open('r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_hash_cache(cache_path, hash_data):
    with cache_path.open('w', encoding='utf-8') as f:
        json.dump(hash_data, f, indent=2)

# --- Load meter metadata ---
meter_metadata = {}
with meter_list_file.open('r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        meter = row['sta'].strip().lower()
        meter_metadata[meter] = {
            "meter": row['meter'].strip(),
            "multiplier": float(row['multiplier'].strip())
        }

# --- Prepare directories and logs ---
lp_output_dir.mkdir(parents=True, exist_ok=True)
logs_dir.mkdir(parents=True, exist_ok=True)
duplicates_log.write_text("=== Duplicate Data Rows ===\n", encoding='utf-8')
errors_log.write_text("=== Errors During Processing ===\n", encoding='utf-8')

hash_cache = load_hash_cache(hash_cache_path)
new_hash_cache = dict(hash_cache)

# --- Group files by meter ---
meter_files = defaultdict(list)
for csv_file in data_root.rglob('*.csv'):
    lower_name = csv_file.name.lower()
    for meter in meter_metadata:
        if meter in lower_name:
            meter_files[meter].append(csv_file)
            break

# --- Process each meter ---
for meter, files in meter_files.items():
    data_by_time = {}
    header = None

    for file in files:
        file_hash = hash_file(file)
        already_processed = file_hash in hash_cache
        if already_processed:
            print(f"[↪] Already processed (appending): {file.name}")
            print(f"[↪] Skipping already-processed file: {file.name}")

        try:
            with file.open('r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                for row in reader:
                    row = [cell.strip() for cell in row]
                    if row and row[0].startswith("Record No."):
                        header = row
                        break

                for row in reader:
                    row = [cell.strip() for cell in row]
                    if row and len(row) >= 4:
                        try:
                            start_time_str = row[2].strip()
                            dt = datetime.strptime(start_time_str, date_format)

                            if dt in data_by_time:
                                existing_row = [cell.strip() for cell in data_by_time[dt]]
                                incoming_row = [cell.strip() for cell in row]
                                log_type = "OVERLAP" if existing_row == incoming_row else "DUPLICATE"
                                with duplicates_log.open('a', encoding='utf-8') as dlog:
                                    dlog.write(f"{meter},{dt},{file.resolve()},{log_type} ROW: {row}\n")
                            else:
                                data_by_time[dt] = row

                        except ValueError:
                            with errors_log.open('a', encoding='utf-8') as elog:
                                elog.write(f"PARSE FAILURE,{meter},{file.name},{row[2]}\n")

            new_hash_cache[file_hash] = str(file)

        except Exception as e:
            with errors_log.open('a', encoding='utf-8') as elog:
                elog.write(f"{meter},{file.name},FAILED TO PARSE FILE: {str(e)}\n")

    # --- Write output CSV ---
    sorted_rows = [data_by_time[k] for k in sorted(data_by_time)]
    output_path = lp_output_dir / f"{meter}.csv"

    with output_path.open('w', newline='', encoding='utf-8') as out_csv:
        writer = csv.writer(out_csv, quoting=csv.QUOTE_ALL)

        if header:
            new_header = ['meter'] + header + [
                'MW_del', 'MW_rec', 'MVA_del', 'MVA_rec',
                'MW_net', 'MVA_net', 'PF_net'
            ]
            writer.writerow(new_header)

        try:
            kw_del_col = header.index('kw_del')
            kw_rec_col = header.index('kw_rec')
            kva_del_col = header.index('kva_del')
            kva_rec_col = header.index('kva_rec')
        except Exception as e:
            with errors_log.open('a', encoding='utf-8') as elog:
                elog.write(f"[HEADER INDEX ERROR] {meter} | {e}\n")

        for row in sorted_rows:
            try:
                multiplier = meter_metadata[meter]['multiplier']
                meter_number = meter_metadata[meter]['meter']

                kw_del = float(row[kw_del_col])
                kw_rec = float(row[kw_rec_col])
                kva_del = float(row[kva_del_col])
                kva_rec = float(row[kva_rec_col])

                mw_del = kw_del * multiplier / 1_000_000
                mw_rec = kw_rec * multiplier / 1_000_000
                mva_del = kva_del * multiplier / 1_000_000
                mva_rec = kva_rec * multiplier / 1_000_000
                mw_net = mw_del + mw_rec
                mva_net = mva_del + mva_rec
                pf_net = mw_net / mva_net if mva_net != 0 else 0.0

                extended_row = [meter_number] + row + [
                    f"{mw_del:.6f}", f"{mw_rec:.6f}",
                    f"{mva_del:.6f}", f"{mva_rec:.6f}",
                    f"{mw_net:.6f}", f"{mva_net:.6f}",
                    f"{pf_net:.6f}"
                ]
                writer.writerow(extended_row)

            except Exception as e:
                with errors_log.open('a', encoding='utf-8') as elog:
                    elog.write(f"[MATH ERROR] {meter} | {file.name} | Row: {row} | Error: {e}\n")

# --- Save updated hash cache ---
save_hash_cache(hash_cache_path, new_hash_cache)
