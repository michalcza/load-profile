import os
import csv
from pathlib import Path

# Root directory with sorted folders
root_dir = '.'
output_prefix = 'all'
keywords = ['north', 'south', 'west', 'gen']

# Process each folder
for folder in Path(root_dir).iterdir():
    if not folder.is_dir():
        continue

    csv_files = sorted([
        f for f in folder.glob('*.csv')
        if any(key in f.name.lower() for key in keywords)
    ])

    if not csv_files:
        continue

    print(f"[INFO] Merging {len(csv_files)} files in {folder.name}")

    start_ts = folder.name
    end_ts = csv_files[-1].name.split('_')[-1].replace('.csv', '')
    output_file = folder / f"{output_prefix}-{start_ts}_{end_ts}.csv"

    written_header = False
    header_fields = []

    with open(output_file, 'w', newline='', encoding='utf-8') as fout:
        writer = None

        for file in csv_files:
            with open(file, 'r', encoding='utf-8') as fin:
                reader = csv.reader(fin)
                try:
                    rows = list(reader)
                    if not rows:
                        continue

                    header = [h.strip() for h in rows[0]]
                    data_rows = rows[1:]

                    if not written_header:
                        writer = csv.writer(fout, quoting=csv.QUOTE_ALL)
                        writer.writerow(header)
                        header_fields = header
                        written_header = True
                    else:
                        # Ensure the new file's header matches
                        if [h.strip().lower() for h in header] != [h.strip().lower() for h in header_fields]:
                            print(f"[WARN] Skipping file with mismatched header: {file}")
                            continue

                    # Write data rows with cleanup and padding
                    for idx, row in enumerate(data_rows, start=1):
                        clean_row = [cell.strip() for cell in row]
                        if len(clean_row) < len(header_fields):
                            print(f"[WARN] Padding short row in {file.name} (line {idx + 1})")
                            clean_row += [''] * (len(header_fields) - len(clean_row))
                        elif len(clean_row) > len(header_fields):
                            print(f"[WARN] Truncating long row in {file.name} (line {idx + 1})")
                            clean_row = clean_row[:len(header_fields)]

                        writer.writerow(clean_row)

                except Exception as e:
                    print(f"[ERROR] Problem reading {file}: {e}")

    print(f"[OK] Merged to: {output_file}")
