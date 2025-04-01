import os
import csv
import shutil
from datetime import datetime

# Paths
dropbox_dir = os.path.join(".", "_dropbox", "KW")
destination_root = os.path.join(".", "data", "KW")
error_dir = os.path.join(destination_root, "ERROR")
log_file_path = os.path.join(".", "dropbox.log")
error_log_path = os.path.join(".", "dropbox-error.log")
date_format = "%m/%d/%y %H:%M:%S"

# Ensure source and error directories exist
if not os.path.exists(dropbox_dir):
    print(f"Source directory does not exist: {dropbox_dir}")
    exit(1)

os.makedirs(error_dir, exist_ok=True)

# Open both log files
with open(log_file_path, 'a', encoding='utf-8') as log_file, \
     open(error_log_path, 'a', encoding='utf-8') as err_file:

    def log(msg, error=False):
        log_file.write(msg)
        if error:
            err_file.write(msg)

    log("\n==== Log Start ====\n")
    log(f"Process started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    for filename in os.listdir(dropbox_dir):
        if filename.lower().endswith('.csv'):
            source_path = os.path.join(dropbox_dir, filename)

            try:
                with open(source_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)

                    # Skip until header
                    for row in reader:
                        row = [cell.strip() for cell in row]
                        if row and row[0].startswith("Record No."):
                            # Rename headers directly
                            row = [
                                'kw_del' if cell.strip() == '-1-' else
                                'kw_rec' if cell.strip() == '-2-' else
                                'kva_del' if cell.strip() == '-3-' else
                                'kva_rec' if cell.strip() == '-4-' else
                                cell.strip()
                                for cell in row
                            ]
                            header = row
                            break

                    data_rows = [
                        [cell.strip() for cell in row]
                        for row in reader
                        if row and len(row) >= 4 and row[2].strip() and row[3].strip()
                    ]

                if not data_rows:
                    log(f"Skipping '{filename}' — no valid data rows found.\n")
                    continue

                parsed_rows = []
                for row in data_rows:
                    try:
                        start_dt = datetime.strptime(row[2].strip(), date_format)
                        end_dt = datetime.strptime(row[3].strip(), date_format)
                        parsed_rows.append((row, start_dt, end_dt))
                    except ValueError:
                        continue

                # Check for gaps
                mismatch_found = False
                mismatch_index = None
                for i in range(1, len(parsed_rows)):
                    if parsed_rows[i][1] != parsed_rows[i - 1][2]:
                        mismatch_found = True
                        mismatch_index = i
                        break

                if mismatch_found:
                    quarantined_name = filename.replace(".csv", "_SEQUENCE-ERROR.csv")
                    dest_path = os.path.join(error_dir, quarantined_name)
                    shutil.move(source_path, dest_path)

                    # Log the mismatch to both logs
                    msg = (
                        f"[ERROR] Non-sequential timestamps in '{filename}'\n"
                        f"  At Record: {parsed_rows[mismatch_index][0][0]} | "
                        f"Expected: {parsed_rows[mismatch_index - 1][2].strftime(date_format)} | "
                        f"Actual: {parsed_rows[mismatch_index][1].strftime(date_format)}\n"
                        f"  File moved to: {dest_path}\n"
                        f"  Context:\n"
                    )
                    log(msg, error=True)

                    context_start = max(0, mismatch_index - 4)
                    context_end = min(len(parsed_rows), mismatch_index + 5)
                    for i in range(context_start, context_end):
                        row = parsed_rows[i][0]
                        log(f"    {row[0]}, {row[2].strip()} -> {row[3].strip()}\n", error=True)

                    continue  # Skip normal move

                # All good — move normally
                start_dt = parsed_rows[0][1]
                end_dt = parsed_rows[-1][2]
                folder_name = start_dt.strftime("%Y-%m")

                dest_folder = os.path.join(destination_root, folder_name)
                os.makedirs(dest_folder, exist_ok=True)

                dest_path = os.path.join(dest_folder, filename)

                # Write cleaned, quoted CSV
                with open(dest_path, 'w', newline='', encoding='utf-8-sig') as cleaned:
                    writer = csv.writer(cleaned, quoting=csv.QUOTE_ALL)
                    writer.writerow(header)
                    for row, _, _ in parsed_rows:
                        writer.writerow(row)

                log(
                    f"Moved: '{filename}' | Start: {start_dt.strftime('%Y-%m-%d %H:%M')} "
                    f"| End: {end_dt.strftime('%Y-%m-%d %H:%M')} | Folder: {dest_folder}\n"
                )
                # Remove the original source file after writing cleaned version
                os.remove(source_path)

            except Exception as e:
                msg = f"Error processing '{filename}': {e}\n"
                log(msg, error=True)

    log(f"Process ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    log("==== Log End ====\n")
