from pathlib import Path
import csv

# Load meter name mapping from meter-data.csv
meter_name_by_id = {}
try:
    with open('../../meter-data.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            meter_name_by_id[row['meter'].strip()] = row['sta'].strip().lower()
except Exception as e:
    print(f"[ERROR] Could not load meter-data.csv: {e}")
    meter_name_by_id = {}

# New computed columns
new_fields = ['mw_del', 'mw_rec', 'mva_del', 'mva_rec']
drop_column = 'event type'

# Use correct directory
for file in Path('./').rglob('all-*.csv'):
    print(f"\n[INFO] Checking file: {file.name}")

    try:
        with open(file, 'r', encoding='utf-8') as f_in:
            reader = csv.DictReader(f_in)
            rows = list(reader)
            fieldnames = reader.fieldnames or []

        if not rows:
            print(f"[WARN] File is empty or malformed: {file.name}")
            continue

        if all(field in fieldnames for field in new_fields):
            print(f"[SKIP] File already contains MW/MVA columns: {file.name}")
            continue

        required = ['meter', 'multiplier', 'kw_del', 'kw_rec', 'kva_del', 'kva_rec']
        if not all(col in fieldnames for col in required):
            print(f"[ERROR] Missing required columns in: {file.name}")
            continue

        fieldnames_filtered = [f for f in fieldnames if f.lower() != drop_column.lower()]
        updated_fieldnames = fieldnames_filtered + new_fields

        new_rows = []
        for idx, row in enumerate(rows, start=2):
            row_cleaned = {k: v for k, v in row.items() if k.lower() != drop_column.lower()}
            try:
                meter_id = row['meter'].strip()
                meter_type = meter_name_by_id.get(meter_id, '').lower()
                is_gen = meter_type == 'gen'

                multiplier = float(row['multiplier'])
                kw_del = float(row['kw_del'])
                kw_rec = float(row['kw_rec'])
                kva_del = float(row['kva_del'])
                kva_rec = float(row['kva_rec'])

                mw_del = (kw_del * multiplier) / 1_000_000
                mw_rec = (kw_rec * multiplier) / 1_000_000
                mva_del = (kva_del * multiplier) / 1_000_000
                mva_rec = (kva_rec * multiplier) / 1_000_000

                if is_gen:
                    if any(val < 0 for val in [mw_del, mw_rec, mva_del, mva_rec]):
                        print(f"[WARN] Skipped gen row already negative in {file.name} (line {idx}):")
                        print(f"       {row}")
                    else:
                        mw_del *= -1
                        mw_rec *= -1
                        mva_del *= -1
                        mva_rec *= -1

                row_cleaned['mw_del'] = f"{mw_del:.6f}"
                row_cleaned['mw_rec'] = f"{mw_rec:.6f}"
                row_cleaned['mva_del'] = f"{mva_del:.6f}"
                row_cleaned['mva_rec'] = f"{mva_rec:.6f}"

            except ValueError:
                print(f"[WARN] Row with non-numeric data skipped in {file.name} (line {idx}):")
                print(f"       {row}")
                row_cleaned['mw_del'] = row_cleaned['mw_rec'] = ''
                row_cleaned['mva_del'] = row_cleaned['mva_rec'] = ''
            new_rows.append(row_cleaned)

        with open(file, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=updated_fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(new_rows)

        print(f"[OK] Cleaned + updated: {file.name}")

    except Exception as e:
        print(f"[ERROR] Could not process file {file.name}: {e}")
