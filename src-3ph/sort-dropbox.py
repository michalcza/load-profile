import csv
from pathlib import Path
from datetime import datetime
import shutil

# Paths
project_root = Path('.')
dropbox_dir = project_root / '_dropbox' / 'KW'
destination_root = project_root / 'data' / 'KW'
error_dir = destination_root / 'ERROR'
log_dir = project_root / 'logs'
log_file_path = log_dir / 'dropbox.log'
error_log_path = log_dir / 'dropbox-error.log'

date_format = "%m/%d/%y %H:%M:%S"

# Ensure source and error directories exist
if not dropbox_dir.exists():
    print(f"Source directory does not exist: {dropbox_dir}")
    exit(1)

error_dir.mkdir(parents=True, exist_ok=True)

# Open both log files
with log_file_path.open('a', encoding='utf-8') as log_file, \
     error_log_path.open('a', encoding='utf-8') as err_file:

    def log(msg, error=False):
        log_file.write(msg)
        if error:
            err_file.write(msg)

    log("\n==== Log Start ====\n")
    log(f"Process started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    for file_path in dropbox_dir.iterdir():
        if file_path.suffix.lower() == '.csv':
            filename = file_path.name

            try:
                with file_path.open('r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)

                    # Skip until header
                    for row in reader:
                        row = [cell.strip() for cell in row]
                        if row and row[0].startswith("Record No."):
                            header = [
                                'kw_del' if cell.strip() == '-1-' else
                                'kw_rec' if cell.strip() == '-2-' else
                                'kva_del' if cell.strip() == '-3-' else
                                'kva_rec' if cell.strip() == '-4-' else
                                cell.strip()
                                for cell in row
                            ]
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
                    dest_path = error_dir / quarantined_name
                    shutil.move(str(file_path), dest_path)

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
                        log(f"    {row[0]}, {row[2]} -> {row[3]}\n", error=True)

                    continue  # Skip normal move

                # All good — move normally
                start_dt = parsed_rows[0][1]
                end_dt = parsed_rows[-1][2]
                folder_name = start_dt.strftime("%Y-%m")
                dest_folder = destination_root / folder_name
                dest_folder.mkdir(parents=True, exist_ok=True)

                dest_path = dest_folder / filename

                with dest_path.open('w', newline='', encoding='utf-8-sig') as cleaned:
                    writer = csv.writer(cleaned, quoting=csv.QUOTE_ALL)
                    writer.writerow(header)
                    for row, _, _ in parsed_rows:
                        writer.writerow(row)

                log(
                    f"Moved: '{filename}' | Start: {start_dt.strftime('%Y-%m-%d %H:%M')} "
                    f"| End: {end_dt.strftime('%Y-%m-%d %H:%M')} | Folder: {dest_folder}\n"
                )

                file_path.unlink()  # Delete the original

            except Exception as e:
                msg = f"Error processing '{filename}': {e}\n"
                log(msg, error=True)

    log(f"Process ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    log("==== Log End ====\n")
