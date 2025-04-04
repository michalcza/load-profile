import os
import csv
from pathlib import Path

# Configuration
source_directory = '.'
meter_data_file = '../../meter-data.csv'
keywords = ['gen', 'north', 'south', 'west']

# Map column renames
column_rename_map = {
    '-1-': 'kw_del',
    '-2-': 'kw_rec',
    '-3-': 'kva_del',
    '-4-': 'kva_rec',
}

# Load meter information
meter_info = {}
try:
    with open(meter_data_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row['sta'].strip().lower()
            meter_id = row['meter'].strip()
            multiplier = row['multiplier'].strip()
            meter_info[key] = {'meter': meter_id, 'multiplier': multiplier}
except Exception as e:
    print(f"[ERROR] Failed to read meter-data.csv: {e}")
    exit(1)

# Process each CSV file
for path in Path(source_directory).rglob('*.csv'):
    filename = path.name.lower()
    matched_key = next((key for key in keywords if key in filename), None)

    if not matched_key or matched_key not in meter_info:
        print(f"[SKIP] {path} – no matching key")
        continue

    meter_id = meter_info[matched_key]['meter']
    multiplier = meter_info[matched_key]['multiplier']

    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find the header row containing "Record No." (case insensitive, strip whitespace)
        header_index = next(
            (i for i, line in enumerate(lines) if 'record no.' in line.lower()),
            None
        )
        if header_index is None:
            print(f"[ERROR] Header not found in {path}")
            continue

        # Parse CSV starting from header
        data_lines = lines[header_index:]
        reader = csv.reader(data_lines)
        raw_rows = list(reader)

        if len(raw_rows) < 2:
            print(f"[WARN] No data rows in {path}")
            continue

        # Clean header
        header = [h.strip() for h in raw_rows[0]]
        lower_header = [h.lower() for h in header]

        has_meter = 'meter' in lower_header
        has_multiplier = 'multiplier' in lower_header

        # Rename known columns
        renamed_header = []
        for col in header:
            clean = col.strip()
            renamed_header.append(column_rename_map.get(clean, clean))

        # Only prepend meter and multiplier if they don't already exist
        if not (has_meter and has_multiplier):
            renamed_header = ['meter', 'multiplier'] + renamed_header
            data_rows = raw_rows[1:]
            cleaned_data = [[meter_id, multiplier] + [cell.strip() for cell in row] for row in data_rows]
        else:
            # Already present, just clean and rename
            renamed_header = [column_rename_map.get(h.strip(), h.strip()) for h in header]
            cleaned_data = [[cell.strip() for cell in row] for row in raw_rows[1:]]

        # Write cleaned + fully quoted CSV
        with open(path, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.writer(f_out, quoting=csv.QUOTE_ALL)
            writer.writerow(renamed_header)
            for row in cleaned_data:
                # Ensure row matches column count
                padded = row + [''] * (len(renamed_header) - len(row))
                trimmed = padded[:len(renamed_header)]
                writer.writerow(trimmed)

        print(f"[OK] Cleaned: {path}")

    except Exception as e:
        print(f"[ERROR] Failed to process {path}: {e}")
